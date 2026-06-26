#!/usr/bin/env python3
"""Fetch CDC weekly flu summary data and write CSV/JSON outputs."""

from __future__ import annotations

import csv
import json
import os
import re
import secrets
import stat
import sys
from datetime import datetime
from email.message import Message
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


CDC_FLU_URL = "https://www.cdc.gov/flu/weekly/"
FLUVIEW_PHASE2_INIT_URL = (
    "https://gis.cdc.gov/grasp/flu2/GetPhase02InitApp?appVersion=Public"
)
FLUVIEW_PHASE2_DATA_URL = (
    "https://gis.cdc.gov/grasp/flu2/PostPhase02WHOGetData"
)
FLUVIEW_PHASE2_LINE_CSV_URL = (
    "https://gis.cdc.gov/grasp/flu2/PostPhase02LineChartDataDownload"
)
FLUVIEW_PHASE4_INIT_URL = (
    "https://gis.cdc.gov/grasp/flu4/GetPhase04InitApp?appVersion=Public"
)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
USER_AGENT = (
    "Mozilla/5.0 (compatible; flu-shot-data/1.0; "
    "+https://github.com/garethpaul/flu-shot-data)"
)

HEADERS = [
    "WEEK_NUM",
    "WEEK_END",
    "HHS_REGION",
    "OUTPATIENT_ILI",
    "PCT_FLU_POS",
    "NUM_JURIS",
    "A_H3",
    "A_2009_H1N1",
    "A_NO_SUBTYPE",
    "B",
    "PED_DEATHS",
]

EXPECTED_TABLE_HEADERS = [
    "Region",
    "ILI",
    "Percent positive",
    "Jurisdictions",
    "A H3",
    "A 2009 H1N1",
    "A no subtype",
    "B",
    "Ped deaths",
]


class FluSummaryTableParser(HTMLParser):
    """Extract rows from the CDC summary table used by the original scraper."""

    def __init__(self) -> None:
        super().__init__()
        self._in_target_table = False
        self._table_depth = 0
        self._in_row = False
        self._in_cell = False
        self._current_row: List[str] = []
        self._current_cell: List[str] = []
        self._current_table: List[List[str]] = []
        self.tables: List[List[List[str]]] = []
        self.rows: List[List[str]] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "table":
            if self._in_target_table:
                self._table_depth += 1
            elif attr_map.get("cellpadding") == "3":
                self._in_target_table = True
                self._table_depth = 1
                self._current_table = []

        if not self._in_target_table:
            return

        if tag == "tr":
            self._in_row = True
            self._current_row = []
        elif tag in {"td", "th"} and self._in_row:
            self._in_cell = True
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._in_target_table and self._in_cell:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._in_target_table:
            return

        if tag in {"td", "th"} and self._in_cell:
            cell = " ".join("".join(self._current_cell).split())
            self._current_row.append(cell)
            self._current_cell = []
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if self._current_row:
                self.rows.append(self._current_row)
                self._current_table.append(self._current_row)
            self._current_row = []
            self._in_row = False
        elif tag == "table":
            self._table_depth -= 1
            if self._table_depth == 0:
                if self._current_table:
                    self.tables.append(self._current_table)
                self._current_table = []
                self._in_target_table = False


def validate_fetch_url(url: str) -> str:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not hostname:
        raise ValueError("CDC fetch URL must be an HTTPS URL with a host.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("CDC fetch URL must not include credentials.")
    if parsed.query or parsed.fragment:
        raise ValueError("CDC fetch URL must not include query strings or fragments.")
    authority = parsed.netloc.rsplit("@", 1)[-1]
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("CDC fetch URL must not include an explicit port.") from None
    if port is not None or ":" in authority:
        raise ValueError("CDC fetch URL must not include an explicit port.")
    if hostname != "cdc.gov" and not hostname.endswith(".cdc.gov"):
        raise ValueError("CDC fetch URL host must be cdc.gov.")
    return url


def fetch_timeout(value: int | str = 30, default: int = 30) -> int:
    try:
        timeout_value = int(value)
    except (TypeError, ValueError):
        return default

    if 1 <= timeout_value <= 300:
        return timeout_value
    return default


class CDCNoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_fetch_url(newurl)
        raise ValueError("CDC fetch redirects are not allowed.")


def validate_response_status(response) -> None:
    if response.getcode() != 200:
        raise ValueError("CDC response status must be 200.")


def validate_html_content_type(headers) -> None:
    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        content_types = get_all("Content-Type", [])
    else:
        content_type = headers.get("Content-Type")
        content_types = [] if content_type is None else [content_type]

    if len(content_types) > 1:
        raise ValueError("CDC response must declare exactly one Content-Type.")

    content_type = content_types[0] if content_types else None
    if not isinstance(content_type, str) or not content_type.strip():
        raise ValueError("CDC response must declare an HTML Content-Type.")

    message = Message()
    try:
        message["Content-Type"] = content_type
        media_type = message.get_content_type().lower()
        charset_parameters = [
            value
            for name, value in message.get_params()[1:]
            if name.lower() == "charset"
        ]
    except (TypeError, ValueError) as error:
        raise ValueError("CDC response has an invalid Content-Type.") from error

    if media_type != "text/html":
        raise ValueError("CDC response Content-Type must be text/html.")
    if len(charset_parameters) > 1:
        raise ValueError(
            "CDC response Content-Type must declare at most one charset parameter."
        )
    charset = message.get_content_charset()
    if charset is not None and charset.lower() not in {"utf-8", "utf8"}:
        raise ValueError("CDC response Content-Type must use UTF-8.")


def _validate_fluview_content_type(headers, expected_media_type: str) -> None:
    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        content_types = get_all("Content-Type", [])
    else:
        content_type = headers.get("Content-Type")
        content_types = [] if content_type is None else [content_type]

    if len(content_types) > 1:
        raise ValueError("CDC response must declare exactly one Content-Type.")

    content_type = content_types[0] if content_types else None
    if expected_media_type == "application/json" and (
        not isinstance(content_type, str) or not content_type.strip()
    ):
        raise ValueError("CDC response must declare a JSON Content-Type.")
    if not isinstance(content_type, str) or not content_type.strip():
        raise ValueError(
            f"CDC response Content-Type must be {expected_media_type}."
        )

    message = Message()
    try:
        message["Content-Type"] = content_type
        media_type = message.get_content_type().lower()
        parameters = message.get_params()[1:]
    except (TypeError, ValueError) as error:
        raise ValueError("CDC response has an invalid Content-Type.") from error

    if media_type != expected_media_type:
        raise ValueError(
            f"CDC response Content-Type must be {expected_media_type}."
        )

    if expected_media_type == "application/json":
        charset_parameters = [
            value for name, value in parameters if name.lower() == "charset"
        ]
        if any(name.lower() != "charset" for name, _ in parameters):
            raise ValueError(
                "CDC response JSON Content-Type must not include unreviewed parameters."
            )
        if len(charset_parameters) > 1:
            raise ValueError(
                "CDC response Content-Type must declare at most one charset parameter."
            )
        charset = message.get_content_charset()
        if charset is not None and charset.lower() not in {"utf-8", "utf8"}:
            raise ValueError("CDC response Content-Type must use UTF-8.")
    elif parameters:
        raise ValueError(
            "CDC response application/octet-stream Content-Type must not include parameters."
        )


def validate_content_encoding(headers) -> None:
    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        content_encodings = get_all("Content-Encoding", [])
    else:
        content_encoding = headers.get("Content-Encoding")
        content_encodings = [] if content_encoding is None else [content_encoding]

    if not content_encodings:
        return
    if len(content_encodings) != 1:
        raise ValueError("CDC response Content-Encoding must be identity.")

    content_encoding = content_encodings[0]
    if not isinstance(content_encoding, str):
        raise ValueError("CDC response Content-Encoding must be identity.")

    normalized_encoding = content_encoding.strip().lower()
    if normalized_encoding != "identity":
        raise ValueError("CDC response Content-Encoding must be identity.")


def validate_content_length(headers, max_bytes: int) -> int | None:
    if max_bytes < 1:
        raise ValueError("CDC response size limit must be positive.")

    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        content_lengths = get_all("Content-Length", [])
    else:
        content_length = headers.get("Content-Length")
        content_lengths = [] if content_length is None else [content_length]

    if len(content_lengths) > 1:
        raise ValueError("CDC response must declare exactly one Content-Length.")
    if not content_lengths:
        return None

    content_length = content_lengths[0]
    if not isinstance(content_length, str) or re.fullmatch(r"[0-9]+", content_length) is None:
        raise ValueError("CDC response Content-Length must be an ASCII decimal value.")

    declared_length = int(content_length)
    if declared_length > max_bytes:
        raise ValueError("CDC response exceeds the maximum allowed size.")
    return declared_length


def read_response_bytes(response, max_bytes: int) -> bytes:
    declared_length = validate_content_length(response.headers, max_bytes)

    chunks = []
    total_bytes = 0
    while True:
        chunk = response.read(min(READ_CHUNK_BYTES, max_bytes - total_bytes + 1))
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise ValueError("CDC response exceeds the maximum allowed size.")
        chunks.append(chunk)

    if declared_length is not None and total_bytes != declared_length:
        raise ValueError("CDC response body does not match Content-Length.")

    return b"".join(chunks)


def decode_html_bytes(body: bytes) -> str:
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("CDC response body must be valid UTF-8.") from None


def _validate_positive_season_id(season_id: int) -> int:
    if type(season_id) is not int or season_id < 1:
        raise ValueError("FluView season identifier must be a positive integer.")
    return season_id


def _validate_hhs_region_id(region_id: int) -> int:
    if type(region_id) is not int or not 1 <= region_id <= 10:
        raise ValueError("FluView HHS region identifier must be between 1 and 10.")
    return region_id


def _encode_json_request(payload: dict) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _read_fluview_response(
    request: Request,
    expected_url: str,
    expected_media_type: str,
    timeout: int,
    max_bytes: int,
) -> bytes:
    opener = build_opener(CDCNoRedirectHandler())
    with opener.open(request, timeout=fetch_timeout(timeout)) as response:
        validate_response_status(response)
        if response.geturl() != expected_url:
            raise ValueError("CDC response final URL must match the exact requested URL.")
        _validate_fluview_content_type(response.headers, expected_media_type)
        validate_content_encoding(response.headers)
        return read_response_bytes(response, max_bytes)


def _decode_json_object(body: bytes) -> dict:
    text = decode_html_bytes(body)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("CDC response body must be valid JSON.") from None
    if not isinstance(value, dict):
        raise ValueError("CDC response JSON root must be a JSON object.")
    return value


def _fluview_request(
    url: str,
    payload: dict | None = None,
) -> Request:
    headers = {"User-Agent": USER_AGENT}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = _encode_json_request(payload)
    return Request(url, data=data, headers=headers)


def fetch_fluview_phase2_init(
    timeout: int = 30,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> dict:
    body = _read_fluview_response(
        _fluview_request(FLUVIEW_PHASE2_INIT_URL),
        FLUVIEW_PHASE2_INIT_URL,
        "application/json",
        timeout,
        max_bytes,
    )
    return _decode_json_object(body)


def fetch_fluview_phase2_region_data(
    season_id: int,
    region_id: int,
    timeout: int = 30,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> dict:
    season_id = _validate_positive_season_id(season_id)
    region_id = _validate_hhs_region_id(region_id)
    payload = {
        "AppVersion": "Public",
        "SeasonID": season_id,
        "RegionTypeID": 1,
        "RegionID": region_id,
    }
    body = _read_fluview_response(
        _fluview_request(FLUVIEW_PHASE2_DATA_URL, payload),
        FLUVIEW_PHASE2_DATA_URL,
        "application/json",
        timeout,
        max_bytes,
    )
    return _decode_json_object(body)


def fetch_fluview_phase2_line_csv(
    season_id: int,
    region_id: int,
    timeout: int = 30,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> str:
    season_id = _validate_positive_season_id(season_id)
    region_id = _validate_hhs_region_id(region_id)
    payload = {
        "AppVersion": "Public",
        "DatasourceDT": [{"ID": 1, "Name": "ILINet"}],
        "RegionTypeId": 1,
        "SubRegionsDT": [{"ID": region_id, "Name": str(region_id)}],
        "SeasonsDT": [{"ID": season_id, "Name": str(season_id)}],
    }
    body = _read_fluview_response(
        _fluview_request(FLUVIEW_PHASE2_LINE_CSV_URL, payload),
        FLUVIEW_PHASE2_LINE_CSV_URL,
        "application/octet-stream",
        timeout,
        max_bytes,
    )
    return decode_html_bytes(body)


def fetch_fluview_phase4_init(
    timeout: int = 30,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> dict:
    body = _read_fluview_response(
        _fluview_request(FLUVIEW_PHASE4_INIT_URL),
        FLUVIEW_PHASE4_INIT_URL,
        "application/json",
        timeout,
        max_bytes,
    )
    return _decode_json_object(body)


def _require_object_list(payload: dict, name: str) -> list[dict]:
    value = payload.get(name)
    if not isinstance(value, list) or any(
        not isinstance(item, dict) for item in value
    ):
        raise ValueError(f"FluView {name} must be an array of objects.")
    return value


def _require_positive_integer(value, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"FluView {label} must be a positive integer.")
    return value


def _require_nonempty_string(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"FluView {label} must be a non-empty string.")
    return value.strip()


def parse_fluview_phase2_metadata(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("FluView phase 2 metadata must be an object.")

    seasons = _require_object_list(payload, "seasons")
    mmwr_rows = _require_object_list(payload, "mmwr")
    region_rows = _require_object_list(payload, "hhsregion")
    lab_rows = _require_object_list(payload, "labtypes")
    virus_rows = _require_object_list(payload, "viruslist")

    season_labels = {}
    enabled_season_ids = []
    for season in seasons:
        season_id = _require_positive_integer(
            season.get("seasonid"),
            "season identifier",
        )
        if season_id in season_labels:
            raise ValueError("FluView metadata contains a duplicate season identifier.")
        label = _require_nonempty_string(season.get("label"), "season label")
        enabled = season.get("enabled")
        if type(enabled) is not int or enabled not in {0, 1}:
            raise ValueError("FluView season enabled flag must be zero or one.")
        season_labels[season_id] = label
        if enabled == 1:
            enabled_season_ids.append(season_id)

    if not enabled_season_ids:
        raise ValueError("FluView metadata must contain an enabled season.")
    current_season_id = max(enabled_season_ids)

    seen_week_ids = set()
    current_weeks = []
    for week in mmwr_rows:
        week_id = _require_positive_integer(week.get("mmwrid"), "MMWR identifier")
        if week_id in seen_week_ids:
            raise ValueError("FluView metadata contains a duplicate MMWR identifier.")
        seen_week_ids.add(week_id)

        season_id = _require_positive_integer(
            week.get("seasonid"),
            "MMWR season identifier",
        )
        week_number = week.get("weeknumber")
        if type(week_number) is not int or not 1 <= week_number <= 53:
            raise ValueError("FluView MMWR week number must be between 1 and 53.")
        year = week.get("year")
        if type(year) is not int or not 1900 <= year <= 9999:
            raise ValueError("FluView MMWR year must be a four-digit integer.")
        yearweek = week.get("yearweek")
        if type(yearweek) is not int or yearweek != year * 100 + week_number:
            raise ValueError("FluView MMWR yearweek must match year and week number.")
        weekend = _require_nonempty_string(week.get("weekend"), "MMWR weekend")
        try:
            parsed_weekend = datetime.strptime(weekend, "%Y-%m-%d")
        except ValueError:
            raise ValueError("FluView MMWR weekend must be a valid ISO date.") from None
        if parsed_weekend.strftime("%Y-%m-%d") != weekend:
            raise ValueError("FluView MMWR weekend must be a valid ISO date.")

        if season_id == current_season_id:
            current_weeks.append(
                {
                    "week_id": week_id,
                    "week_number": week_number,
                    "week_end": weekend,
                }
            )

    if not current_weeks:
        raise ValueError("FluView metadata must contain a week for the current enabled season.")
    current_week = max(current_weeks, key=lambda item: item["week_id"])

    seen_region_ids = set()
    active_regions = {}
    for region in region_rows:
        region_id = _require_positive_integer(
            region.get("hhsregionid"),
            "HHS region identifier",
        )
        if region_id in seen_region_ids:
            raise ValueError("FluView metadata contains a duplicate HHS region identifier.")
        seen_region_ids.add(region_id)
        name = _require_nonempty_string(region.get("hhsregionname"), "HHS region name")
        active = region.get("isactive")
        if type(active) is not int or active not in {0, 1}:
            raise ValueError("FluView HHS region active flag must be zero or one.")
        if active == 1:
            if name != f"Region {region_id}":
                raise ValueError("FluView active HHS regions must use the canonical name.")
            active_regions[region_id] = name

    required_region_ids = set(range(1, 11))
    if set(active_regions) != required_region_ids:
        raise ValueError("FluView metadata must contain active HHS regions 1 through 10.")

    lab_types = {}
    for lab in lab_rows:
        lab_type_id = _require_positive_integer(
            lab.get("labtypeid"),
            "lab type identifier",
        )
        if lab_type_id in lab_types:
            raise ValueError("FluView metadata contains a duplicate lab type identifier.")
        lab_types[lab_type_id] = _require_nonempty_string(
            lab.get("labname"),
            "lab type name",
        )

    if lab_types.get(1) != "Public Health Labs" or lab_types.get(2) != "Clinical Labs":
        raise ValueError("FluView metadata must contain lab types 1 and 2.")

    viruses = {}
    for virus in virus_rows:
        virus_id = _require_positive_integer(
            virus.get("virusid"),
            "virus identifier",
        )
        if virus_id in viruses:
            raise ValueError("FluView metadata contains a duplicate virus identifier.")
        description = _require_nonempty_string(
            virus.get("description"),
            "virus description",
        )
        label = _require_nonempty_string(virus.get("label"), "virus label")
        lab_type_id = _require_positive_integer(
            virus.get("labtypeid"),
            "virus lab type identifier",
        )
        if lab_type_id not in lab_types:
            raise ValueError("FluView virus metadata must reference a known lab type.")
        viruses[virus_id] = {
            "description": description,
            "label": label,
            "lab_type_id": lab_type_id,
        }

    if not viruses:
        raise ValueError("FluView metadata must contain at least one virus category.")

    return {
        "season_id": current_season_id,
        "season_label": season_labels[current_season_id],
        **current_week,
        "hhs_regions": dict(sorted(active_regions.items())),
        "lab_types": dict(sorted(lab_types.items())),
        "viruses": dict(sorted(viruses.items())),
    }


def fetch_html(
    url: str = CDC_FLU_URL,
    timeout: int = 30,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> str:
    fetch_url = validate_fetch_url(url)
    timeout_seconds = fetch_timeout(timeout)
    request = Request(
        fetch_url,
        headers={"User-Agent": USER_AGENT},
    )
    opener = build_opener(CDCNoRedirectHandler())
    with opener.open(request, timeout=timeout_seconds) as response:
        validate_response_status(response)
        validate_fetch_url(response.geturl())
        validate_html_content_type(response.headers)
        validate_content_encoding(response.headers)
        response_bytes = read_response_bytes(response, max_bytes)
        return decode_html_bytes(response_bytes)


def parse_week_metadata(html: str) -> tuple[str, str]:
    week_num_match = re.search(r"Influenza Season Week (\d+)", html)
    week_end_match = re.search(
        r"ending ((January|February|March|April|May|June|July|August|September|October|November|December) "
        r"\d{1,2}, \d{4})",
        html,
    )

    if not week_num_match or not week_end_match:
        raise ValueError("Could not find flu week number and ending date in CDC HTML.")

    week_num = week_num_match.group(1)
    week_end = week_end_match.group(1)

    if not 1 <= int(week_num) <= 53:
        raise ValueError("CDC influenza season week must be between 1 and 53.")

    try:
        datetime.strptime(week_end, "%B %d, %Y")
    except ValueError as error:
        raise ValueError("CDC flu week ending date must be a valid calendar date.") from error

    return week_num, week_end


def normalize_percent(value: str) -> str:
    return value.strip().rstrip("%").strip()


def has_expected_summary_header(rows: List[List[str]]) -> bool:
    if not rows:
        return False

    expected = [header.lower() for header in EXPECTED_TABLE_HEADERS]
    actual = [cell.lower() for cell in rows[0][: len(EXPECTED_TABLE_HEADERS)]]
    return actual == expected


def parse_records(html: str) -> List[Dict[str, str]]:
    week_num, week_end = parse_week_metadata(html)
    parser = FluSummaryTableParser()
    parser.feed(html)

    if not parser.tables:
        raise ValueError("Could not find CDC summary table with cellpadding=3.")

    summary_rows = next(
        (table for table in parser.tables if has_expected_summary_header(table)),
        None,
    )
    if summary_rows is None:
        raise ValueError("CDC summary table did not contain expected flu summary headers.")

    records: List[Dict[str, str]] = []
    seen_regions: set[str] = set()
    for row in summary_rows[1:]:
        if len(row) < 9:
            continue
        if has_expected_summary_header([row]):
            continue

        region = row[0].strip()
        if not region:
            continue
        region_key = region.casefold()
        if region_key in seen_regions:
            raise ValueError("CDC summary table contains duplicate region rows.")
        seen_regions.add(region_key)

        values = [
            week_num,
            week_end,
            region,
            row[1],
            normalize_percent(row[2]),
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
        ]
        records.append(dict(zip(HEADERS, values)))

    if not records:
        raise ValueError("CDC summary table did not contain parseable region rows.")

    return records


def validate_output_paths(
    csv_path: str | Path,
    json_path: str | Path,
) -> tuple[Path, Path]:
    csv_output = Path(csv_path)
    json_output = Path(json_path)
    resolved_outputs = []

    for output in (csv_output, json_output):
        if not output.parent.resolve().is_dir():
            raise ValueError("Each output parent must be an existing directory.")
        resolved_output = output.resolve()
        try:
            output_mode = resolved_output.stat().st_mode
        except FileNotFoundError:
            pass
        else:
            if not stat.S_ISREG(output_mode):
                raise ValueError("Each existing output target must be a regular file.")
        resolved_outputs.append(resolved_output)

    paths_collide = csv_output.resolve() == json_output.resolve()
    if not paths_collide:
        try:
            paths_collide = csv_output.samefile(json_output)
        except FileNotFoundError:
            paths_collide = False

    if paths_collide:
        raise ValueError("CSV and JSON outputs must use distinct filesystem targets.")

    return resolved_outputs[0], resolved_outputs[1]


def validate_output_records(records: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    output_records = list(records)
    expected_headers = set(HEADERS)

    for record in output_records:
        if not isinstance(record, dict) or set(record) != expected_headers:
            raise ValueError("Each output record must use exactly the documented headers.")

        for value in record.values():
            if not isinstance(value, str):
                raise ValueError("Each output record must contain only string values.")
            try:
                value.encode("utf-8")
            except UnicodeEncodeError as error:
                raise ValueError(
                    "Each output record must contain valid UTF-8 text."
                ) from error

    return output_records


def cleanup_output_paths(paths: Iterable[Path]) -> Exception | None:
    cleanup_error = None
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except Exception as error:
            if cleanup_error is None:
                cleanup_error = error
    return cleanup_error


def reserve_output_path(
    output: Path,
    purpose: str,
    creation_mode: int = 0o600,
) -> Path:
    for _attempt in range(100):
        path = output.parent / f".{output.name}.{purpose}-{secrets.token_hex(8)}"
        try:
            descriptor = os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_RDWR,
                creation_mode,
            )
        except FileExistsError:
            continue
        try:
            os.close(descriptor)
        except Exception:
            cleanup_output_paths((path,))
            raise
        return path
    raise FileExistsError("Could not reserve a unique output publication path.")


def reserve_output_stage(output: Path) -> Path:
    try:
        existing_mode = stat.S_IMODE(output.stat().st_mode)
    except FileNotFoundError:
        existing_mode = None

    stage = reserve_output_path(output, "stage", creation_mode=0o666)
    try:
        if existing_mode is not None:
            stage.chmod(existing_mode)
    except Exception:
        cleanup_output_paths((stage,))
        raise
    return stage


def stage_outputs(
    records: List[Dict[str, str]],
    csv_output: Path,
    json_output: Path,
) -> tuple[Path, Path]:
    csv_stage = None
    json_stage = None

    try:
        csv_stage = reserve_output_stage(csv_output)
        json_stage = reserve_output_stage(json_output)

        with csv_stage.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(records)
            csv_file.flush()
            os.fsync(csv_file.fileno())

        with json_stage.open("w", encoding="utf-8") as json_file:
            json.dump(records, json_file, indent=4)
            json_file.write("\n")
            json_file.flush()
            os.fsync(json_file.fileno())
    except Exception:
        cleanup_output_paths(
            stage for stage in (csv_stage, json_stage) if stage is not None
        )
        raise

    return csv_stage, json_stage


def move_existing_output_to_backup(output: Path) -> Path | None:
    backup = reserve_output_path(output, "backup")
    try:
        os.replace(output, backup)
    except FileNotFoundError:
        cleanup_error = cleanup_output_paths((backup,))
        if cleanup_error is not None:
            raise cleanup_error
        return None
    except Exception:
        cleanup_output_paths((backup,))
        raise
    return backup


def publish_output_pair(
    staged_outputs: tuple[tuple[Path, Path], tuple[Path, Path]],
) -> None:
    states = [
        {
            "output": output,
            "stage": stage,
            "backup": None,
            "published": False,
        }
        for output, stage in staged_outputs
    ]
    retain_recovery_backups = False

    try:
        for state in states:
            state["backup"] = move_existing_output_to_backup(state["output"])
            os.replace(state["stage"], state["output"])
            state["published"] = True
    except Exception as publication_error:
        rollback_errors = []
        for state in reversed(states):
            backup = state["backup"]
            try:
                if backup is not None:
                    os.replace(backup, state["output"])
                elif state["published"]:
                    state["output"].unlink(missing_ok=True)
            except Exception as rollback_error:
                rollback_errors.append(rollback_error)

        if rollback_errors:
            retain_recovery_backups = True
            raise RuntimeError(
                "Paired output publication failed and rollback was incomplete; "
                "recovery backups were retained."
            ) from publication_error
        raise
    finally:
        active_error = sys.exc_info()[1]
        cleanup_paths = []
        for state in states:
            cleanup_paths.append(state["stage"])
            backup = state["backup"]
            if backup is not None and not retain_recovery_backups:
                cleanup_paths.append(backup)

        cleanup_error = cleanup_output_paths(cleanup_paths)
        if cleanup_error is not None and active_error is None:
            raise cleanup_error


def write_outputs(
    records: Iterable[Dict[str, str]],
    csv_path: str | Path = "flu.csv",
    json_path: str | Path = "flu.json",
) -> None:
    csv_output, json_output = validate_output_paths(csv_path, json_path)
    records = validate_output_records(records)
    csv_stage, json_stage = stage_outputs(records, csv_output, json_output)
    publish_output_pair(((csv_output, csv_stage), (json_output, json_stage)))


def run(
    verbose: bool = True,
    url: str = CDC_FLU_URL,
    csv_path: str | Path = "flu.csv",
    json_path: str | Path = "flu.json",
    html: str | None = None,
) -> List[Dict[str, str]]:
    if verbose:
        print("Fetching CDC flu summary data ...")

    source_html = html if html is not None else fetch_html(url)
    records = parse_records(source_html)
    write_outputs(records, csv_path=csv_path, json_path=json_path)

    if verbose:
        print(f"Wrote {len(records)} rows to {csv_path} and {json_path}.")

    return records


if __name__ == "__main__":
    run()
