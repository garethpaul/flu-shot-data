#!/usr/bin/env python3
"""Fetch CDC weekly flu summary data and write CSV/JSON outputs."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from email.message import Message
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


CDC_FLU_URL = "https://www.cdc.gov/flu/weekly/"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024

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


def validate_html_content_type(headers) -> None:
    content_type = headers.get("Content-Type")
    if not isinstance(content_type, str) or not content_type.strip():
        raise ValueError("CDC response must declare an HTML Content-Type.")

    message = Message()
    try:
        message["Content-Type"] = content_type
        media_type = message.get_content_type().lower()
        charset = message.get_content_charset()
    except (TypeError, ValueError) as error:
        raise ValueError("CDC response has an invalid Content-Type.") from error

    if media_type != "text/html":
        raise ValueError("CDC response Content-Type must be text/html.")
    if charset is not None and charset.lower() not in {"utf-8", "utf8"}:
        raise ValueError("CDC response Content-Type must use UTF-8.")


def read_response_bytes(response, max_bytes: int) -> bytes:
    if max_bytes < 1:
        raise ValueError("CDC response size limit must be positive.")

    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            declared_bytes = int(content_length)
        except ValueError as error:
            raise ValueError("CDC response has an invalid Content-Length.") from error
        if declared_bytes < 0 or declared_bytes > max_bytes:
            raise ValueError("CDC response exceeds the maximum allowed size.")

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

    return b"".join(chunks)


def decode_html_bytes(body: bytes) -> str:
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("CDC response body must be valid UTF-8.") from None


def fetch_html(
    url: str = CDC_FLU_URL,
    timeout: int = 30,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> str:
    fetch_url = validate_fetch_url(url)
    timeout_seconds = fetch_timeout(timeout)
    request = Request(
        fetch_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; flu-shot-data/1.0; "
                "+https://github.com/garethpaul/flu-shot-data)"
            )
        },
    )
    opener = build_opener(CDCNoRedirectHandler())
    with opener.open(request, timeout=timeout_seconds) as response:
        validate_fetch_url(response.geturl())
        validate_html_content_type(response.headers)
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


def write_outputs(
    records: Iterable[Dict[str, str]],
    csv_path: str | Path = "flu.csv",
    json_path: str | Path = "flu.json",
) -> None:
    records = list(records)

    with Path(csv_path).open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(records)

    with Path(json_path).open("w", encoding="utf-8") as json_file:
        json.dump(records, json_file, indent=4)
        json_file.write("\n")


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
