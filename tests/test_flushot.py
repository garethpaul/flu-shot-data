import csv
import json
import tempfile
import unittest
from pathlib import Path

import flushot


FIXTURE = Path(__file__).parent / "fixtures" / "cdc_weekly_summary.html"


class FluShotParserTests(unittest.TestCase):
    def test_parse_records_from_fixture(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(2, len(records))
        self.assertEqual("12", records[0]["WEEK_NUM"])
        self.assertEqual("March 23, 2024", records[0]["WEEK_END"])
        self.assertEqual("National", records[0]["HHS_REGION"])
        self.assertEqual("12.5", records[0]["PCT_FLU_POS"])
        self.assertEqual("Region 1", records[1]["HHS_REGION"])

    def test_parse_records_trims_percent_spacing(self):
        html = FIXTURE.read_text(encoding="utf-8").replace("12.5%", " 12.5 % ")
        records = flushot.parse_records(html)

        self.assertEqual("12.5", records[0]["PCT_FLU_POS"])

    def test_parse_records_without_subheading_keeps_first_region(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "      <tr>\n"
            "        <th colspan=\"9\">National and Regional Summary</th>\n"
            "      </tr>\n",
            "",
        )
        records = flushot.parse_records(html)

        self.assertEqual(2, len(records))
        self.assertEqual("National", records[0]["HHS_REGION"])

    def test_parse_records_skips_unrelated_matching_tables(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "    <table cellpadding=\"3\">",
            "    <table cellpadding=\"3\">\n"
            "      <tr><th>Unrelated</th><th>Count</th></tr>\n"
            "      <tr><td>Before summary</td><td>1</td></tr>\n"
            "    </table>\n"
            "    <table cellpadding=\"3\">",
            1,
        )
        records = flushot.parse_records(html)

        self.assertEqual(2, len(records))
        self.assertEqual("National", records[0]["HHS_REGION"])

    def test_parse_records_skips_repeated_header_and_blank_region_rows(self):
        header = (
            "      <tr>\n"
            "        <th>Region</th>\n"
            "        <th>ILI</th>\n"
            "        <th>Percent positive</th>\n"
            "        <th>Jurisdictions</th>\n"
            "        <th>A H3</th>\n"
            "        <th>A 2009 H1N1</th>\n"
            "        <th>A no subtype</th>\n"
            "        <th>B</th>\n"
            "        <th>Ped deaths</th>\n"
            "      </tr>"
        )
        blank_region = (
            "      <tr><td> </td><td>1.0</td><td>2%</td><td>1</td>"
            "<td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>"
        )
        html = FIXTURE.read_text(encoding="utf-8").replace(
            header,
            f"{header}\n{header}\n{blank_region}",
            1,
        )

        records = flushot.parse_records(html)

        self.assertEqual(2, len(records))
        self.assertEqual(["National", "Region 1"], [row["HHS_REGION"] for row in records])

    def test_write_outputs_uses_expected_schema(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "flu.json"
            flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            with csv_path.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            with json_path.open(encoding="utf-8") as json_file:
                json_rows = json.load(json_file)

        self.assertEqual(flushot.HEADERS, list(rows[0].keys()))
        self.assertEqual(rows, json_rows)

    def test_parse_records_fails_when_metadata_is_missing(self):
        with self.assertRaisesRegex(ValueError, "week number and ending date"):
            flushot.parse_records("<html><table cellpadding='3'></table></html>")

    def test_parse_records_fails_when_summary_header_is_missing(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "<th>Percent positive</th>", "<th>Unexpected metric</th>"
        )

        with self.assertRaisesRegex(ValueError, "expected flu summary headers"):
            flushot.parse_records(html)

    def test_validate_fetch_url_requires_https_with_host(self):
        self.assertEqual(flushot.CDC_FLU_URL, flushot.validate_fetch_url(flushot.CDC_FLU_URL))

        with self.assertRaisesRegex(ValueError, "HTTPS URL"):
            flushot.validate_fetch_url("http://www.cdc.gov/flu/weekly/")

        with self.assertRaisesRegex(ValueError, "HTTPS URL"):
            flushot.validate_fetch_url("https:///flu/weekly/")

        with self.assertRaisesRegex(ValueError, "cdc.gov"):
            flushot.validate_fetch_url("https://example.com/flu/weekly/")

        self.assertEqual(
            "https://data.cdc.gov/flu/weekly/",
            flushot.validate_fetch_url("https://data.cdc.gov/flu/weekly/"),
        )


if __name__ == "__main__":
    unittest.main()
