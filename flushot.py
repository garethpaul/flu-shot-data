#!/usr/bin/env python3
"""Fetch CDC weekly flu summary data and write CSV/JSON outputs."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import secrets
import stat
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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
FLUVIEW_ILINET_TITLE = (
    "PERCENTAGE OF VISITS FOR INFLUENZA-LIKE-ILLNESS REPORTED BY SENTINEL PROVIDERS"
)
FLUVIEW_ILINET_HEADERS = (
    "YEAR",
    "WEEK",
    "AGE 0-4",
    "AGE 5-24",
    "AGE 25-49",
    "AGE 25-64",
    "AGE 50-64",
    "AGE 65",
    "ILITOTAL",
    "TOTAL PATIENTS",
    "NUM. OF PROVIDERS",
    "%UNWEIGHTED ILI",
    "% WEIGHTED ILI",
)


def _fluview_phase2_region_data_structure() -> list:
    return [
        "mmwrid",
        [
            [
                "Labtypeid",
                [
                    [
                        "regiontypeid",
                        [
                            [
                                "regionid",
                                [
                                    [
                                        "virusid",
                                        "positive_count_cumulative",
                                        "positive_count_three_weeks",
                                        "positive_count",
                                    ]
                                ],
                                "PercentPositive",
                                "PercentA",
                                "PercentB",
                                "PercentWeightedILI",
                                "Baseline",
                                "elevated",
                                "PercentUnWeightedILI",
                                "WeeklyILIData",
                                "Insufficient",
                            ]
                        ],
                    ]
                ],
            ]
        ],
    ]
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


def _parse_fluview_csv_integer(value: str, label: str, minimum: int = 0) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value):
        raise ValueError(f"FluView {label} must be an ASCII-decimal integer.")
    parsed = int(value)
    if parsed < minimum:
        raise ValueError(f"FluView {label} must be at least {minimum}.")
    return parsed


def _parse_fluview_csv_percentage(value: str, label: str) -> Decimal:
    if (
        not isinstance(value, str)
        or len(value) > 32
        or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value)
    ):
        raise ValueError(f"FluView {label} must be a decimal percentage.")
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"FluView {label} must be a decimal percentage.") from None
    if not parsed.is_finite() or not Decimal(0) <= parsed <= Decimal(100):
        raise ValueError(f"FluView {label} must be between zero and 100.")
    return parsed


def parse_fluview_phase2_line_csv(
    csv_text: str,
    season_id: int,
    region_id: int,
) -> dict:
    season_id = _validate_positive_season_id(season_id)
    region_id = _validate_hhs_region_id(region_id)
    if not isinstance(csv_text, str):
        raise ValueError("FluView ILINet CSV must be text.")

    rows = list(csv.reader(csv_text.splitlines()))
    if len(rows) < 3 or rows[0] != [FLUVIEW_ILINET_TITLE]:
        raise ValueError("FluView ILINet CSV must contain the reviewed title row.")
    if tuple(rows[1]) != FLUVIEW_ILINET_HEADERS:
        raise ValueError("FluView ILINet CSV headers do not match the reviewed schema.")

    weeks = {}
    for row in rows[2:]:
        if len(row) != len(FLUVIEW_ILINET_HEADERS):
            raise ValueError("FluView ILINet CSV data rows must contain 13 fields.")
        values = dict(zip(FLUVIEW_ILINET_HEADERS, row))
        year = _parse_fluview_csv_integer(values["YEAR"], "ILINet year", 1900)
        if year > 9999:
            raise ValueError("FluView ILINet year must be a four-digit integer.")
        week_number = _parse_fluview_csv_integer(values["WEEK"], "ILINet week", 1)
        if week_number > 53:
            raise ValueError("FluView ILINet week must be between 1 and 53.")
        yearweek = year * 100 + week_number
        if yearweek in weeks:
            raise ValueError("FluView ILINet CSV contains a duplicate yearweek.")
        if values["AGE 25-64"] != "":
            raise ValueError("FluView ILINet AGE 25-64 must remain empty.")

        age_0_4 = _parse_fluview_csv_integer(values["AGE 0-4"], "age 0-4 count")
        age_5_24 = _parse_fluview_csv_integer(values["AGE 5-24"], "age 5-24 count")
        age_25_49 = _parse_fluview_csv_integer(values["AGE 25-49"], "age 25-49 count")
        age_50_64 = _parse_fluview_csv_integer(values["AGE 50-64"], "age 50-64 count")
        age_65_plus = _parse_fluview_csv_integer(values["AGE 65"], "age 65 count")
        ili_total = _parse_fluview_csv_integer(values["ILITOTAL"], "ILI total")
        total_patients = _parse_fluview_csv_integer(
            values["TOTAL PATIENTS"],
            "total patients",
            1,
        )
        provider_count = _parse_fluview_csv_integer(
            values["NUM. OF PROVIDERS"],
            "provider count",
            1,
        )
        if sum((age_0_4, age_5_24, age_25_49, age_50_64, age_65_plus)) != ili_total:
            raise ValueError("FluView ILINet age counts must sum to ILI total.")
        if ili_total > total_patients:
            raise ValueError("FluView ILINet ILI total cannot exceed total patients.")

        unweighted_ili = _parse_fluview_csv_percentage(
            values["%UNWEIGHTED ILI"],
            "unweighted ILI",
        )
        weighted_ili = _parse_fluview_csv_percentage(
            values["% WEIGHTED ILI"],
            "weighted ILI",
        )
        decimal_places = max(0, -unweighted_ili.as_tuple().exponent)
        displayed_precision = Decimal(1).scaleb(-decimal_places)
        calculated_unweighted = (
            Decimal(ili_total) * Decimal(100) / Decimal(total_patients)
        ).quantize(displayed_precision, rounding=ROUND_HALF_UP)
        if calculated_unweighted != unweighted_ili:
            raise ValueError(
                "FluView ILINet unweighted ILI must match ILI and patient totals."
            )

        weeks[yearweek] = {
            "year": year,
            "week_number": week_number,
            "age_0_4": age_0_4,
            "age_5_24": age_5_24,
            "age_25_49": age_25_49,
            "age_50_64": age_50_64,
            "age_65_plus": age_65_plus,
            "ili_total": ili_total,
            "total_patients": total_patients,
            "provider_count": provider_count,
            "unweighted_ili": float(unweighted_ili),
            "weighted_ili": float(weighted_ili),
        }

    return {
        "season_id": season_id,
        "region_id": region_id,
        "weeks": dict(sorted(weeks.items())),
    }


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


def _require_nonnegative_integer(value, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"FluView {label} must be a nonnegative integer.")
    return value


def _require_percentage(value, label: str):
    if type(value) not in {int, float} or not math.isfinite(value):
        raise ValueError(f"FluView {label} must be a finite number.")
    if not 0 <= value <= 100:
        raise ValueError(f"FluView {label} must be between zero and 100.")
    return value


def _require_binary_flag(value, label: str) -> bool:
    if type(value) is not int or value not in {0, 1}:
        raise ValueError(f"FluView {label} must be zero or one.")
    return bool(value)


def _parse_fluview_region_record(record, expected_virus_ids: set[int]) -> dict:
    if not isinstance(record, list) or len(record) != 11:
        raise ValueError("FluView regional data rows must contain 11 fields.")
    region_id = _require_nonnegative_integer(record[0], "region identifier")
    virus_rows = record[1]
    if not isinstance(virus_rows, list):
        raise ValueError("FluView regional virus data must be an array.")

    virus_counts = {}
    for virus_row in virus_rows:
        if not isinstance(virus_row, list) or len(virus_row) != 4:
            raise ValueError("FluView regional virus rows must contain four fields.")
        virus_id = _require_positive_integer(virus_row[0], "virus identifier")
        if virus_id in virus_counts:
            raise ValueError("FluView regional data contains a duplicate virus identifier.")
        cumulative = _require_nonnegative_integer(
            virus_row[1],
            "cumulative virus count",
        )
        three_weeks = _require_nonnegative_integer(
            virus_row[2],
            "three-week virus count",
        )
        current = _require_nonnegative_integer(
            virus_row[3],
            "current virus count",
        )
        if not cumulative >= three_weeks >= current:
            raise ValueError(
                "FluView virus counts must satisfy cumulative, three-week, and current order."
            )
        virus_counts[virus_id] = {
            "cumulative": cumulative,
            "three_weeks": three_weeks,
            "current": current,
        }

    if set(virus_counts) != expected_virus_ids:
        raise ValueError("FluView regional data must contain the expected virus categories.")

    return {
        "region_id": region_id,
        "virus_counts": dict(sorted(virus_counts.items())),
        "percent_positive": _require_percentage(record[2], "percent positive"),
        "percent_a": _require_percentage(record[3], "percent A"),
        "percent_b": _require_percentage(record[4], "percent B"),
        "weighted_ili": _require_percentage(record[5], "weighted ILI"),
        "baseline": _require_percentage(record[6], "ILI baseline"),
        "elevated": _require_binary_flag(record[7], "elevated flag"),
        "unweighted_ili": _require_percentage(record[8], "unweighted ILI"),
        "weekly_ili_data": _require_binary_flag(record[9], "weekly ILI data flag"),
        "insufficient": _require_binary_flag(record[10], "insufficient data flag"),
    }


def parse_fluview_phase2_region_data(payload: dict, metadata: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("FluView phase 2 regional data must be an object.")
    if not isinstance(metadata, dict):
        raise ValueError("FluView phase 2 metadata must be a normalized object.")

    season_id = _require_positive_integer(
        metadata.get("season_id"),
        "metadata season identifier",
    )
    current_week_id = _require_positive_integer(
        metadata.get("week_id"),
        "metadata MMWR identifier",
    )
    hhs_regions = metadata.get("hhs_regions")
    if not isinstance(hhs_regions, dict) or set(hhs_regions) != set(range(1, 11)):
        raise ValueError("FluView metadata must contain HHS regions 1 through 10.")
    lab_types = metadata.get("lab_types")
    if not isinstance(lab_types, dict) or set(lab_types) != {1, 2}:
        raise ValueError("FluView metadata must contain lab types 1 and 2.")
    metadata_viruses = metadata.get("viruses")
    if not isinstance(metadata_viruses, dict) or not metadata_viruses:
        raise ValueError("FluView metadata must contain virus categories.")

    expected_viruses_by_lab = {1: set(), 2: set()}
    for virus_id, virus in metadata_viruses.items():
        virus_id = _require_positive_integer(virus_id, "metadata virus identifier")
        if not isinstance(virus, dict):
            raise ValueError("FluView metadata virus categories must be objects.")
        lab_type_id = _require_positive_integer(
            virus.get("lab_type_id"),
            "metadata virus lab type identifier",
        )
        if lab_type_id not in expected_viruses_by_lab:
            raise ValueError("FluView metadata viruses must reference lab types 1 or 2.")
        expected_viruses_by_lab[lab_type_id].add(virus_id)
    if any(not virus_ids for virus_ids in expected_viruses_by_lab.values()):
        raise ValueError("FluView metadata must contain viruses for both lab types.")

    mmwr_rows = _require_object_list(payload, "mmwr")
    weeks = {}
    for week in mmwr_rows:
        week_id = _require_positive_integer(week.get("mmwrid"), "MMWR identifier")
        if week_id in weeks:
            raise ValueError("FluView regional data contains a duplicate MMWR identifier.")
        if _require_positive_integer(
            week.get("seasonid"),
            "MMWR season identifier",
        ) != season_id:
            raise ValueError("FluView regional MMWR rows must match the metadata season.")
        week_number = week.get("weeknumber")
        if type(week_number) is not int or not 1 <= week_number <= 53:
            raise ValueError("FluView MMWR week number must be between 1 and 53.")
        year = week.get("year")
        if type(year) is not int or not 1900 <= year <= 9999:
            raise ValueError("FluView MMWR year must be a four-digit integer.")
        yearweek = week.get("yearweek")
        if yearweek != year * 100 + week_number:
            raise ValueError("FluView MMWR yearweek must match year and week number.")
        weekend = _require_nonempty_string(week.get("weekend"), "MMWR weekend")
        try:
            parsed_weekend = datetime.strptime(weekend, "%Y-%m-%d")
        except ValueError:
            raise ValueError("FluView MMWR weekend must be a valid ISO date.") from None
        if parsed_weekend.strftime("%Y-%m-%d") != weekend:
            raise ValueError("FluView MMWR weekend must be a valid ISO date.")
        weeks[week_id] = {
            "yearweek": yearweek,
            "week_number": week_number,
            "week_end": weekend,
        }

    response_viruses = _require_object_list(payload, "viruslist")
    response_viruses_by_id = {}
    for virus in response_viruses:
        virus_id = _require_positive_integer(virus.get("virusid"), "virus identifier")
        if virus_id in response_viruses_by_id:
            raise ValueError("FluView regional data contains a duplicate virus identifier.")
        lab_type_id = _require_positive_integer(
            virus.get("labtypeid"),
            "virus lab type identifier",
        )
        response_viruses_by_id[virus_id] = {
            "description": _require_nonempty_string(
                virus.get("description"),
                "virus description",
            ),
            "label": _require_nonempty_string(virus.get("label"), "virus label"),
            "lab_type_id": lab_type_id,
        }
    expected_viruses = {
        virus_id: {
            "description": virus.get("description"),
            "label": virus.get("label"),
            "lab_type_id": virus.get("lab_type_id"),
        }
        for virus_id, virus in metadata_viruses.items()
    }
    if response_viruses_by_id != expected_viruses:
        raise ValueError("FluView regional virus catalog must match validated metadata.")

    summary = payload.get("WHO_Virus_Counts_Summary_Cumulative")
    if not isinstance(summary, dict):
        raise ValueError("FluView regional summary must be an object.")
    if summary.get("data_structure") != _fluview_phase2_region_data_structure():
        raise ValueError("FluView regional data structure does not match the reviewed schema.")
    data_rows = summary.get("data")
    if not isinstance(data_rows, list):
        raise ValueError("FluView regional summary data must be an array.")

    decoded_week_ids = set()
    for week_row in data_rows:
        if not isinstance(week_row, list) or len(week_row) != 2:
            raise ValueError("FluView regional week rows must contain two fields.")
        week_id = _require_positive_integer(week_row[0], "summary MMWR identifier")
        if week_id in decoded_week_ids:
            raise ValueError("FluView regional summary contains a duplicate MMWR identifier.")
        decoded_week_ids.add(week_id)
        if week_id not in weeks:
            raise ValueError("FluView regional summary must reference a known MMWR row.")
        lab_rows = week_row[1]
        if not isinstance(lab_rows, list):
            raise ValueError("FluView regional lab data must be an array.")

        labs = {}
        for lab_row in lab_rows:
            if not isinstance(lab_row, list) or len(lab_row) < 2:
                raise ValueError("FluView regional lab rows must contain collection segments.")
            lab_type_id = _require_positive_integer(lab_row[0], "lab type identifier")
            if lab_type_id in labs:
                raise ValueError("FluView regional data contains a duplicate lab type.")
            if lab_type_id not in expected_viruses_by_lab:
                raise ValueError("FluView regional data contains an unknown lab type.")

            region_types = {}
            for segment in lab_row[1:]:
                if not isinstance(segment, list):
                    raise ValueError("FluView regional collection segments must be arrays.")
                for region_type_row in segment:
                    if not isinstance(region_type_row, list) or len(region_type_row) != 2:
                        raise ValueError("FluView region type rows must contain two fields.")
                    region_type_id = _require_positive_integer(
                        region_type_row[0],
                        "region type identifier",
                    )
                    if region_type_id in region_types:
                        raise ValueError("FluView regional data contains a duplicate region type.")
                    region_rows = region_type_row[1]
                    if not isinstance(region_rows, list):
                        raise ValueError("FluView region type data must be an array.")
                    decoded_regions = {}
                    for region_row in region_rows:
                        decoded = _parse_fluview_region_record(
                            region_row,
                            expected_viruses_by_lab[lab_type_id],
                        )
                        region_id = decoded["region_id"]
                        if region_id in decoded_regions:
                            raise ValueError(
                                "FluView regional data contains a duplicate region identifier."
                            )
                        decoded_regions[region_id] = decoded
                    region_types[region_type_id] = decoded_regions

            if set(region_types) != {1, 3}:
                raise ValueError("FluView regional data must contain region types 1 and 3.")
            if set(region_types[1]) != set(range(1, 11)):
                raise ValueError("FluView regional data must contain HHS regions 1 through 10.")
            if set(region_types[3]) != {0}:
                raise ValueError("FluView national data must contain only region zero.")
            labs[lab_type_id] = {
                "hhs_regions": dict(sorted(region_types[1].items())),
                "national": region_types[3][0],
            }

        if set(labs) != {1, 2}:
            raise ValueError("FluView regional data must contain lab types 1 and 2.")
        weeks[week_id]["labs"] = dict(sorted(labs.items()))

    if decoded_week_ids != set(weeks):
        raise ValueError("FluView regional summary must contain every MMWR row exactly once.")
    if current_week_id not in decoded_week_ids:
        raise ValueError("FluView regional data must contain the metadata current week.")

    return {
        "season_id": season_id,
        "current_week_id": current_week_id,
        "weeks": dict(sorted(weeks.items())),
    }


def parse_fluview_phase4_mortality(payload: dict, metadata: dict) -> dict:
    if not isinstance(payload, dict) or not isinstance(metadata, dict):
        raise ValueError("FluView phase 4 mortality and metadata must be objects.")
    season_id = _require_positive_integer(metadata.get("season_id"), "season identifier")
    current_week_id = _require_positive_integer(metadata.get("week_id"), "MMWR identifier")
    current_week_number = metadata.get("week_number")
    current_week_end = metadata.get("week_end")

    seasons = _require_object_list(payload, "seasons")
    matching_seasons = [row for row in seasons if row.get("seasonid") == season_id]
    if len(matching_seasons) != 1:
        raise ValueError("FluView phase 4 must contain the current season exactly once.")
    season = matching_seasons[0]
    if (
        _require_nonempty_string(season.get("label"), "season label")
        != metadata.get("season_label")
        or season.get("map") != 1
        or season.get("weekly") != 1
    ):
        raise ValueError("FluView phase 4 current season metadata does not match phase 2.")

    weeks = {}
    for row in _require_object_list(payload, "weeks"):
        if row.get("seasonid") != season_id:
            continue
        week_id = _require_positive_integer(row.get("mmwrid"), "MMWR identifier")
        if week_id in weeks:
            raise ValueError("FluView phase 4 contains a duplicate MMWR identifier.")
        week_number = row.get("weeknumber")
        year = row.get("year")
        if type(week_number) is not int or not 1 <= week_number <= 53:
            raise ValueError("FluView phase 4 week must be between 1 and 53.")
        if type(year) is not int or not 1900 <= year <= 9999:
            raise ValueError("FluView phase 4 year must be a four-digit integer.")
        if row.get("label") != f"{year}-{week_number:02d}":
            raise ValueError("FluView phase 4 week label must match year and week.")
        weeks[week_id] = {"yearweek": year * 100 + week_number, "week_number": week_number}
    if current_week_id not in weeks or weeks[current_week_id]["week_number"] != current_week_number:
        raise ValueError("FluView phase 4 must contain the current report week.")

    reported = _require_object_list(payload, "ped_flu_reported")
    if len(reported) != 1 or reported[0].get("cwk") != current_week_number:
        raise ValueError("FluView phase 4 report metadata must match the current week.")
    if reported[0].get("cwk_date") != current_week_end:
        raise ValueError("FluView phase 4 report date must match phase 2 metadata.")

    expected_viruses = {1: "A", 2: "B", 3: "A/B Not Distinguished", 4: "A and B"}
    viruses = {}
    for row in _require_object_list(payload, "ped_flu_virus"):
        virus_id = _require_positive_integer(row.get("id"), "pediatric virus identifier")
        if virus_id in viruses:
            raise ValueError("FluView phase 4 contains a duplicate virus identifier.")
        viruses[virus_id] = _require_nonempty_string(row.get("label"), "pediatric virus label")
    if viruses != expected_viruses:
        raise ValueError("FluView phase 4 virus catalog does not match the reviewed categories.")

    grouped = {week_id: {} for week_id in weeks}
    for row in _require_object_list(payload, "ped_flu_weekly"):
        week_id = row.get("mmwrid")
        if week_id not in grouped:
            continue
        virus_id = row.get("virusid")
        if type(virus_id) is not int or virus_id not in {0, 1, 2, 3, 4}:
            raise ValueError("FluView phase 4 weekly virus identifier is invalid.")
        if virus_id in grouped[week_id]:
            raise ValueError("FluView phase 4 contains a duplicate weekly virus row.")
        previous = _require_nonnegative_integer(row.get("pwk"), "previously reported deaths")
        current = _require_nonnegative_integer(row.get("cwk"), "newly reported deaths")
        total = _require_nonnegative_integer(row.get("allwks"), "total deaths")
        if previous + current != total:
            raise ValueError("FluView phase 4 weekly death counts must add to total.")
        grouped[week_id][virus_id] = {
            "previously_reported": previous,
            "newly_reported": current,
            "total": total,
        }

    national_weeks = {}
    for week_id, virus_rows in grouped.items():
        if set(virus_rows) != {0, 1, 2, 3, 4}:
            raise ValueError("FluView phase 4 must contain five virus rows per week.")
        for field in ("previously_reported", "newly_reported", "total"):
            if virus_rows[0][field] != sum(virus_rows[item][field] for item in range(1, 5)):
                raise ValueError("FluView phase 4 total virus row must equal category rows.")
        if week_id > current_week_id:
            if any(value for row in virus_rows.values() for value in row.values()):
                raise ValueError("FluView phase 4 future placeholder weeks must be zero.")
            continue
        national_weeks[week_id] = {
            **weeks[week_id],
            "total_deaths": virus_rows[0]["total"],
            "virus_deaths": {item: virus_rows[item] for item in range(1, 5)},
        }

    hhs_totals = {}
    for row in _require_object_list(payload, "ped_flu_map"):
        if row.get("seasonid") != season_id:
            continue
        region_id = _require_positive_integer(row.get("hhsid"), "HHS region identifier")
        if region_id in hhs_totals:
            raise ValueError("FluView phase 4 contains a duplicate HHS region.")
        death_count = _require_nonnegative_integer(row.get("c"), "HHS death count")
        rate = row.get("rate")
        if type(rate) not in {int, float} or not math.isfinite(rate) or not 0 <= rate <= 100:
            raise ValueError("FluView phase 4 HHS rate must be between zero and 100.")
        hhs_totals[region_id] = {"death_count": death_count, "rate_per_million": rate}
    if set(hhs_totals) != set(range(1, 11)):
        raise ValueError("FluView phase 4 must contain HHS regions 1 through 10.")
    season_total = sum(row["total_deaths"] for row in national_weeks.values())
    if sum(row["death_count"] for row in hhs_totals.values()) != season_total:
        raise ValueError("FluView phase 4 national and HHS season totals must match.")

    return {
        "season_id": season_id,
        "current_week_id": current_week_id,
        "current_week_number": current_week_number,
        "current_week_end": current_week_end,
        "virus_categories": viruses,
        "national_weeks": dict(sorted(national_weeks.items())),
        "hhs_season_totals": dict(sorted(hhs_totals.items())),
        "season_total_deaths": season_total,
    }


def _v2_lab_surveillance(record: dict) -> dict:
    return {
        "percent_positive": record["percent_positive"],
        "percent_a": record["percent_a"],
        "percent_b": record["percent_b"],
        "virus_counts": [
            {
                "virus_id": virus_id,
                "weekly_positive_count": counts["current"],
                "three_week_positive_count": counts["three_weeks"],
                "season_cumulative_positive_count": counts["cumulative"],
            }
            for virus_id, counts in sorted(record["virus_counts"].items())
        ],
    }


def _v2_metrics_match(left: dict, right: dict) -> bool:
    numeric_fields = ("weighted_ili", "unweighted_ili", "baseline")
    flag_fields = ("elevated", "weekly_ili_data", "insufficient")
    return all(
        type(left.get(field)) in {int, float}
        and type(right.get(field)) in {int, float}
        and math.isclose(left[field], right[field], rel_tol=0, abs_tol=1e-9)
        for field in numeric_fields
    ) and all(
        type(left.get(field)) is bool
        and type(right.get(field)) is bool
        and left[field] == right[field]
        for field in flag_fields
    )


def _v2_numbers_match(left, right) -> bool:
    return (
        type(left) in {int, float}
        and type(right) in {int, float}
        and math.isfinite(left)
        and math.isfinite(right)
        and math.isclose(left, right, rel_tol=0, abs_tol=1e-9)
    )


def build_fluview_v2_dataset(
    metadata: dict,
    regional_data: dict,
    ilinet_by_region: dict,
    mortality: dict,
) -> dict:
    if not all(isinstance(value, dict) for value in (
        metadata, regional_data, ilinet_by_region, mortality
    )):
        raise ValueError("FluView v2 sources must be objects.")

    season_id = _require_positive_integer(metadata.get("season_id"), "v2 season identifier")
    current_week_id = _require_positive_integer(metadata.get("week_id"), "v2 MMWR identifier")
    season_label = _require_nonempty_string(metadata.get("season_label"), "v2 season label")
    hhs_regions = metadata.get("hhs_regions")
    lab_types = metadata.get("lab_types")
    viruses = metadata.get("viruses")
    if not isinstance(hhs_regions, dict) or hhs_regions != {
        region_id: f"Region {region_id}" for region_id in range(1, 11)
    }:
        raise ValueError("FluView v2 metadata must contain canonical HHS regions.")
    if lab_types != {1: "Public Health Labs", 2: "Clinical Labs"}:
        raise ValueError("FluView v2 metadata must contain reviewed lab types.")
    if not isinstance(viruses, dict) or not viruses:
        raise ValueError("FluView v2 metadata must contain virus categories.")

    if regional_data.get("season_id") != season_id or regional_data.get("current_week_id") != current_week_id:
        raise ValueError("FluView v2 regional source identity does not match metadata.")
    regional_weeks = regional_data.get("weeks")
    if not isinstance(regional_weeks, dict) or current_week_id not in regional_weeks:
        raise ValueError("FluView v2 regional source must contain the current week.")
    current_week = regional_weeks[current_week_id]
    if (
        current_week.get("week_number") != metadata.get("week_number")
        or current_week.get("week_end") != metadata.get("week_end")
    ):
        raise ValueError("FluView v2 current regional week does not match metadata.")

    if set(ilinet_by_region) != set(range(1, 11)):
        raise ValueError("FluView v2 requires ILINet data for HHS regions 1 through 10.")
    expected_yearweeks = {week.get("yearweek") for week in regional_weeks.values()}
    if None in expected_yearweeks or len(expected_yearweeks) != len(regional_weeks):
        raise ValueError("FluView v2 regional weeks must contain unique yearweek keys.")
    for region_id, source in ilinet_by_region.items():
        if (
            not isinstance(source, dict)
            or source.get("season_id") != season_id
            or source.get("region_id") != region_id
            or not isinstance(source.get("weeks"), dict)
            or set(source["weeks"]) != expected_yearweeks
        ):
            raise ValueError("FluView v2 ILINet source identity or coverage is invalid.")

    if mortality.get("season_id") != season_id or mortality.get("current_week_id") != current_week_id:
        raise ValueError("FluView v2 mortality source identity does not match metadata.")
    national_mortality = mortality.get("national_weeks")
    hhs_mortality = mortality.get("hhs_season_totals")
    mortality_viruses = mortality.get("virus_categories")
    if (
        not isinstance(national_mortality, dict)
        or not set(regional_weeks).issubset(national_mortality)
        or not isinstance(hhs_mortality, dict)
        or set(hhs_mortality) != set(range(1, 11))
        or not isinstance(mortality_viruses, dict)
        or set(mortality_viruses) != {1, 2, 3, 4}
    ):
        raise ValueError("FluView v2 mortality coverage or catalogs are invalid.")

    regional_weekly = []
    for week_id, week in sorted(regional_weeks.items()):
        yearweek = week.get("yearweek")
        mortality_week = national_mortality[week_id]
        if mortality_week.get("yearweek") != yearweek:
            raise ValueError("FluView v2 mortality yearweek does not match regional data.")
        labs = week.get("labs")
        if not isinstance(labs, dict) or set(labs) != {1, 2}:
            raise ValueError("FluView v2 regional weeks must contain both lab types.")
        for region_id in range(1, 11):
            public_health = labs[1].get("hhs_regions", {}).get(region_id)
            clinical = labs[2].get("hhs_regions", {}).get(region_id)
            if (
                not isinstance(public_health, dict)
                or not isinstance(clinical, dict)
                or public_health.get("region_id") != region_id
                or clinical.get("region_id") != region_id
                or not _v2_metrics_match(public_health, clinical)
            ):
                raise ValueError("FluView v2 lab ILI metrics or region identity disagree.")
            ilinet = ilinet_by_region[region_id]["weeks"].get(yearweek)
            if not isinstance(ilinet, dict):
                raise ValueError("FluView v2 ILINet week is missing.")
            if not (
                _v2_numbers_match(public_health.get("weighted_ili"), ilinet.get("weighted_ili"))
                and _v2_numbers_match(public_health.get("unweighted_ili"), ilinet.get("unweighted_ili"))
            ):
                raise ValueError("FluView v2 ILINet and regional ILI metrics disagree.")
            regional_weekly.append({
                "mmwr_id": week_id,
                "yearweek": yearweek,
                "week_number": week["week_number"],
                "week_end": week["week_end"],
                "hhs_region_id": region_id,
                "hhs_region_name": hhs_regions[region_id],
                "ili": {
                    "age_0_4_ili_visits": ilinet["age_0_4"],
                    "age_5_24_ili_visits": ilinet["age_5_24"],
                    "age_25_49_ili_visits": ilinet["age_25_49"],
                    "age_50_64_ili_visits": ilinet["age_50_64"],
                    "age_65_plus_ili_visits": ilinet["age_65_plus"],
                    "total_ili_visits": ilinet["ili_total"],
                    "total_patients": ilinet["total_patients"],
                    "provider_count": ilinet["provider_count"],
                    "unweighted_ili_percent": ilinet["unweighted_ili"],
                    "weighted_ili_percent": ilinet["weighted_ili"],
                    "baseline_percent": public_health["baseline"],
                    "is_elevated": public_health["elevated"],
                    "has_weekly_ili_data": public_health["weekly_ili_data"],
                    "is_insufficient": public_health["insufficient"],
                },
                "laboratory_surveillance": {
                    "public_health": _v2_lab_surveillance(public_health),
                    "clinical": _v2_lab_surveillance(clinical),
                },
            })

    laboratory_virus_categories = [
        {
            "id": virus_id,
            "description": virus["description"],
            "label": virus["label"],
            "lab_type_id": virus["lab_type_id"],
            "lab_type": lab_types[virus["lab_type_id"]],
        }
        for virus_id, virus in sorted(viruses.items())
    ]
    mortality_national = [
        {
            "mmwr_id": week_id,
            "yearweek": week["yearweek"],
            "week_number": week["week_number"],
            "total_deaths": week["total_deaths"],
            "virus_deaths": [
                {
                    "virus_id": virus_id,
                    "previously_reported_deaths": counts["previously_reported"],
                    "newly_reported_deaths": counts["newly_reported"],
                    "total_deaths": counts["total"],
                }
                for virus_id, counts in sorted(week["virus_deaths"].items())
            ],
        }
        for week_id, week in sorted(national_mortality.items())
    ]
    mortality_hhs = [
        {
            "hhs_region_id": region_id,
            "hhs_region_name": hhs_regions[region_id],
            "death_count": values["death_count"],
            "rate_per_million": values["rate_per_million"],
        }
        for region_id, values in sorted(hhs_mortality.items())
    ]

    return {
        "schema_version": 2,
        "season": {
            "id": season_id,
            "label": season_label,
            "current_week": {
                "mmwr_id": current_week_id,
                "yearweek": current_week["yearweek"],
                "week_number": current_week["week_number"],
                "week_end": current_week["week_end"],
            },
        },
        "laboratory_virus_categories": laboratory_virus_categories,
        "regional_weekly": regional_weekly,
        "pediatric_mortality": {
            "scope": "national_weekly_and_hhs_season_totals",
            "virus_categories": [
                {"id": virus_id, "label": label}
                for virus_id, label in sorted(mortality_viruses.items())
            ],
            "national_weekly": mortality_national,
            "hhs_season_totals": mortality_hhs,
            "season_total_deaths": mortality["season_total_deaths"],
        },
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
