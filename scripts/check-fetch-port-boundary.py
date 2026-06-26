#!/usr/bin/env python3
from pathlib import Path
import sys


source = Path(sys.argv[1]).read_text(encoding="utf-8")
tests = Path(sys.argv[2]).read_text(encoding="utf-8")

validator = source.split("def validate_fetch_url", 1)[1].split("\ndef fetch_timeout", 1)[0]
contracts = (
    "parsed.username is not None or parsed.password is not None",
    "parsed.query or parsed.fragment",
    'authority = parsed.netloc.rsplit("@", 1)[-1]',
    "try:",
    "port = parsed.port",
    "except ValueError:",
    'raise ValueError("CDC fetch URL must not include an explicit port.") from None',
    'if port is not None or ":" in authority:',
    'hostname != "cdc.gov"',
    "return url",
)
for contract in contracts:
    if validator.count(contract) != 1:
        raise SystemExit(f"Fetch URL validator must contain one {contract!r}.")
if not all(validator.index(a) < validator.index(b) for a, b in zip(contracts, contracts[1:])):
    raise SystemExit("Fetch URL ports must be parsed and rejected before host acceptance.")
if validator.count(
    'raise ValueError("CDC fetch URL must not include an explicit port.") from None'
) != 1 or validator.count(
    '        raise ValueError("CDC fetch URL must not include an explicit port.")\n'
) != 1:
    raise SystemExit("Malformed and explicit ports must have deterministic rejection paths.")

test_contracts = (
    "def test_validate_fetch_url_rejects_explicit_or_malformed_ports",
    '"https://www.cdc.gov:/flu/weekly/"',
    '"https://www.cdc.gov:not-a-port/flu/weekly/"',
    '"https://www.cdc.gov:65536/flu/weekly/"',
    "def test_fetch_html_rejects_explicit_port_before_building_opener",
    "def test_redirect_handler_revalidates_targets",
)
for contract in test_contracts:
    if tests.count(contract) != 1:
        raise SystemExit(f"Fetch port regressions must contain one {contract!r}.")
fetch_test = tests.split(
    "def test_fetch_html_rejects_explicit_port_before_building_opener", 1
)[1].split("\n    def ", 1)[0]
if fetch_test.count("build_opener.assert_not_called()") != 1:
    raise SystemExit("Fetch port regression must prove the opener is not built.")
for fixture in (
    '"https://www.cdc.gov:443/flu/weekly/"',
    '"https://www.cdc.gov:8443/flu/weekly/"',
):
    if tests.count(fixture) != 2:
        raise SystemExit(f"Fetch port regressions must contain two uses of {fixture!r}.")

redirect_test = tests.split("def test_redirect_handler_revalidates_targets", 1)[1].split(
    "\n    def ", 1
)[0]
if '"https://www.cdc.gov:8443/flu/weekly/"' not in redirect_test:
    raise SystemExit("Redirect targets must retain explicit-port rejection coverage.")

print("CDC fetch port boundary checks passed.")
