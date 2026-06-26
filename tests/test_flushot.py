import csv
import copy
import json
import os
import stat
import tempfile
import unittest
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

import flushot


FIXTURE = Path(__file__).parent / "fixtures" / "cdc_weekly_summary.html"
FLUVIEW_PHASE2_FIXTURE = (
    Path(__file__).parent / "fixtures" / "fluview_phase2_init_2026-06-26.json"
)
FLUVIEW_PHASE2_REGION_FIXTURE = (
    Path(__file__).parent / "fixtures" / "fluview_phase2_region_2026-06-26.json"
)
FLUVIEW_PHASE2_LINE_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "fluview_phase2_line_region1_2026-06-26.json"
)
FLUVIEW_PHASE4_FIXTURE = (
    Path(__file__).parent / "fixtures" / "fluview_phase4_mortality_2026-06-26.json"
)
FLUVIEW_ALL_REGION_LINES_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "fluview_phase2_line_all_regions_2026-06-26.json"
)


def same_resolved_path(left, right):
    return Path(left).resolve() == Path(right).resolve()


class FakeResponse:
    def __init__(self, body=b"", url=flushot.CDC_FLU_URL, headers=None, status=200):
        self.body = BytesIO(body)
        self.url = url
        self.headers = headers or {}
        self.status = status
        self.read_calls = 0

    def read(self, size=-1):
        self.read_calls += 1
        return self.body.read(size)

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


class FluShotParserTests(unittest.TestCase):
    def fluview_phase2_fixture(self):
        return json.loads(FLUVIEW_PHASE2_FIXTURE.read_text(encoding="utf-8"))

    def fluview_phase2_region_fixture(self):
        return json.loads(
            FLUVIEW_PHASE2_REGION_FIXTURE.read_text(encoding="utf-8")
        )

    def fluview_phase2_metadata(self):
        return flushot.parse_fluview_phase2_metadata(
            self.fluview_phase2_fixture()["response"]
        )

    def fluview_phase2_line_fixture(self):
        return json.loads(FLUVIEW_PHASE2_LINE_FIXTURE.read_text(encoding="utf-8"))

    def fluview_phase4_fixture(self):
        return json.loads(FLUVIEW_PHASE4_FIXTURE.read_text(encoding="utf-8"))

    def fluview_v2_sources(self):
        metadata = self.fluview_phase2_metadata()
        regional = flushot.parse_fluview_phase2_region_data(
            self.fluview_phase2_region_fixture()["response"], metadata
        )
        line_fixture = json.loads(
            FLUVIEW_ALL_REGION_LINES_FIXTURE.read_text(encoding="utf-8")
        )
        ilinet = {
            item["region_id"]: flushot.parse_fluview_phase2_line_csv(
                item["response_text"], metadata["season_id"], item["region_id"]
            )
            for item in line_fixture["regions"]
        }
        mortality = flushot.parse_fluview_phase4_mortality(
            self.fluview_phase4_fixture()["response"], metadata
        )
        return metadata, regional, ilinet, mortality

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

    def test_parse_records_rejects_duplicate_regions_case_insensitively(self):
        duplicate_row = (
            "      <tr>\n"
            "        <td><strong>{region}</strong></td>\n"
            "        <td>2.1</td><td>8.1%</td><td>6</td>\n"
            "        <td>3</td><td>4</td><td>0</td><td>1</td><td>0</td>\n"
            "      </tr>\n"
        )

        for region in ("Region 1", "region 1"):
            with self.subTest(region=region):
                html = FIXTURE.read_text(encoding="utf-8").replace(
                    "    </table>",
                    duplicate_row.format(region=region) + "    </table>",
                )

                with self.assertRaisesRegex(ValueError, "duplicate region"):
                    flushot.parse_records(html)

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

            self.assertEqual({"flu.csv", "flu.json"}, set(os.listdir(tmpdir)))

    def test_write_outputs_preserves_destination_modes(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            reference_path = Path(tmpdir) / "reference"
            reference_path.write_text("reference", encoding="utf-8")
            default_mode = stat.S_IMODE(reference_path.stat().st_mode)
            reference_path.unlink()

            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "flu.json"
            flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)
            self.assertEqual(default_mode, stat.S_IMODE(csv_path.stat().st_mode))
            self.assertEqual(default_mode, stat.S_IMODE(json_path.stat().st_mode))

            csv_path.chmod(0o640)
            json_path.chmod(0o604)
            flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)
            self.assertEqual(0o640, stat.S_IMODE(csv_path.stat().st_mode))
            self.assertEqual(0o604, stat.S_IMODE(json_path.stat().st_mode))

    def test_write_outputs_preserves_distinct_symlink_destinations(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_target = Path(tmpdir) / "csv-target"
            json_target = Path(tmpdir) / "json-target"
            csv_target.write_bytes(b"csv sentinel")
            json_target.write_bytes(b"json sentinel")
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "flu.json"
            csv_path.symlink_to(csv_target)
            json_path.symlink_to(json_target)

            flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            self.assertTrue(csv_path.is_symlink())
            self.assertTrue(json_path.is_symlink())
            with csv_target.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            with json_target.open(encoding="utf-8") as json_file:
                json_rows = json.load(json_file)
            self.assertEqual(rows, json_rows)
            self.assertEqual(
                {"csv-target", "json-target", "flu.csv", "flu.json"},
                set(os.listdir(tmpdir)),
            )

        self.assertEqual(flushot.HEADERS, list(rows[0].keys()))
        self.assertEqual(rows, json_rows)

    def test_write_outputs_rejects_identical_destinations_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flu-output"
            output_path.write_bytes(b"sentinel")

            with self.assertRaisesRegex(ValueError, "distinct filesystem targets"):
                flushot.write_outputs(
                    records,
                    csv_path=output_path,
                    json_path=output_path,
                )

            self.assertEqual(b"sentinel", output_path.read_bytes())

    def test_write_outputs_rejects_symlink_aliases_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flu-output"
            alias_path = Path(tmpdir) / "flu-alias"
            output_path.write_bytes(b"sentinel")
            alias_path.symlink_to(output_path)

            with self.assertRaisesRegex(ValueError, "distinct filesystem targets"):
                flushot.write_outputs(
                    records,
                    csv_path=output_path,
                    json_path=alias_path,
                )

            self.assertEqual(b"sentinel", output_path.read_bytes())

    def test_write_outputs_rejects_hard_link_aliases_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flu-output"
            alias_path = Path(tmpdir) / "flu-alias"
            output_path.write_bytes(b"sentinel")
            os.link(output_path, alias_path)

            with self.assertRaisesRegex(ValueError, "distinct filesystem targets"):
                flushot.write_outputs(
                    records,
                    csv_path=output_path,
                    json_path=alias_path,
                )

            self.assertEqual(b"sentinel", output_path.read_bytes())

    def test_write_outputs_rejects_missing_parent_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "missing" / "flu.json"
            csv_path.write_bytes(b"sentinel")

            with self.assertRaisesRegex(ValueError, "output parent must be an existing directory"):
                flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            self.assertEqual(b"sentinel", csv_path.read_bytes())

    def test_write_outputs_rejects_non_directory_parent_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_parent = Path(tmpdir) / "not-a-directory"
            json_path = json_parent / "flu.json"
            csv_path.write_bytes(b"sentinel")
            json_parent.write_bytes(b"parent sentinel")

            with self.assertRaisesRegex(ValueError, "output parent must be an existing directory"):
                flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            self.assertEqual(b"sentinel", csv_path.read_bytes())
            self.assertEqual(b"parent sentinel", json_parent.read_bytes())

    def test_write_outputs_rejects_csv_directory_target_before_staging(self):
        self.assert_non_regular_output_rejected("csv", "directory")

    def test_write_outputs_rejects_json_directory_target_before_staging(self):
        self.assert_non_regular_output_rejected("json", "directory")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs require os.mkfifo")
    def test_write_outputs_rejects_csv_fifo_target_before_staging(self):
        self.assert_non_regular_output_rejected("csv", "fifo")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs require os.mkfifo")
    def test_write_outputs_rejects_json_fifo_target_before_staging(self):
        self.assert_non_regular_output_rejected("json", "fifo")

    def test_write_outputs_rejects_extra_fields_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))
        records[0]["UNEXPECTED"] = "value"

        self.assert_malformed_records_preserve_outputs(records, "documented headers")

    def test_write_outputs_rejects_non_dictionary_rows_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))
        records[0] = ["not", "a", "record"]

        self.assert_malformed_records_preserve_outputs(records, "documented headers")

    def test_write_outputs_rejects_non_string_values_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))
        records[0]["NUM_JURIS"] = 10

        self.assert_malformed_records_preserve_outputs(records, "string values")

    def test_write_outputs_rejects_invalid_utf8_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))
        records[0]["HHS_REGION"] = "invalid \ud800"

        self.assert_malformed_records_preserve_outputs(records, "valid UTF-8")

    def test_write_outputs_preserves_pair_when_json_staging_fails(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)

            with patch("flushot.json.dump", side_effect=OSError("staging failure")):
                with self.assertRaisesRegex(OSError, "staging failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assert_output_sentinels_and_no_artifacts(tmpdir, csv_path, json_path)

    def test_cleanup_failure_does_not_mask_staging_failure(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)
            real_unlink = Path.unlink
            cleanup_attempts = []

            def fail_csv_stage_cleanup(path, *args, **kwargs):
                cleanup_attempts.append(path.name)
                if path.name.startswith(".flu.csv.stage-"):
                    raise OSError("cleanup failure")
                return real_unlink(path, *args, **kwargs)

            with patch("flushot.json.dump", side_effect=OSError("staging failure")), patch(
                "flushot.Path.unlink", new=fail_csv_stage_cleanup
            ):
                with self.assertRaisesRegex(OSError, "staging failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assertEqual(b"csv sentinel", csv_path.read_bytes())
            self.assertEqual(b"json sentinel", json_path.read_bytes())
            self.assertEqual(1, len(list(Path(tmpdir).glob(".flu.csv.stage-*"))))
            self.assertEqual([], list(Path(tmpdir).glob(".flu.json.stage-*")))
            self.assertTrue(
                any(name.startswith(".flu.json.stage-") for name in cleanup_attempts)
            )

    def test_write_outputs_cleans_first_stage_when_second_reservation_fails(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)
            real_reserve = flushot.reserve_output_stage

            def fail_json_reservation(output):
                if same_resolved_path(output, json_path):
                    raise OSError("reservation failure")
                return real_reserve(output)

            with patch(
                "flushot.reserve_output_stage",
                side_effect=fail_json_reservation,
            ):
                with self.assertRaisesRegex(OSError, "reservation failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assert_output_sentinels_and_no_artifacts(tmpdir, csv_path, json_path)

    def test_write_outputs_cleans_stage_when_mode_preservation_fails(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)

            with patch("flushot.Path.chmod", side_effect=OSError("mode failure")):
                with self.assertRaisesRegex(OSError, "mode failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assert_output_sentinels_and_no_artifacts(tmpdir, csv_path, json_path)

    def test_cleanup_failure_does_not_mask_mode_preservation_failure(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)

            with patch("flushot.Path.chmod", side_effect=OSError("mode failure")), patch(
                "flushot.Path.unlink", side_effect=OSError("cleanup failure")
            ):
                with self.assertRaisesRegex(OSError, "mode failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assertEqual(b"csv sentinel", csv_path.read_bytes())
            self.assertEqual(b"json sentinel", json_path.read_bytes())
            self.assertEqual(1, len(list(Path(tmpdir).glob(".flu.csv.stage-*"))))

    def test_write_outputs_rolls_back_pair_when_second_publication_fails(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)
            real_replace = os.replace

            def fail_json_publication(source, destination):
                if ".stage-" in Path(source).name and same_resolved_path(
                    destination,
                    json_path,
                ):
                    raise OSError("publication failure")
                return real_replace(source, destination)

            with patch("flushot.os.replace", side_effect=fail_json_publication):
                with self.assertRaisesRegex(OSError, "publication failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assert_output_sentinels_and_no_artifacts(tmpdir, csv_path, json_path)

    def test_write_outputs_fault_injection_matches_resolved_alias_destination(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            real_directory = Path(tmpdir) / "real"
            real_directory.mkdir()
            alias_directory = Path(tmpdir) / "alias"
            alias_directory.symlink_to(real_directory, target_is_directory=True)
            csv_path, json_path = self.write_output_sentinels(alias_directory)
            real_replace = os.replace

            def fail_json_publication(source, destination):
                if ".stage-" in Path(source).name and same_resolved_path(
                    destination,
                    json_path,
                ):
                    raise OSError("publication failure")
                return real_replace(source, destination)

            with patch("flushot.os.replace", side_effect=fail_json_publication):
                with self.assertRaisesRegex(OSError, "publication failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assert_output_sentinels_and_no_artifacts(
                real_directory,
                csv_path.resolve(),
                json_path.resolve(),
            )

    def test_write_outputs_rolls_back_pair_when_second_backup_fails(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)
            real_replace = os.replace

            def fail_json_backup(source, destination):
                if same_resolved_path(source, json_path) and ".backup-" in Path(
                    destination
                ).name:
                    raise OSError("backup failure")
                return real_replace(source, destination)

            with patch("flushot.os.replace", side_effect=fail_json_backup):
                with self.assertRaisesRegex(OSError, "backup failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assert_output_sentinels_and_no_artifacts(tmpdir, csv_path, json_path)

    def test_write_outputs_removes_new_pair_when_second_publication_fails(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "flu.json"
            real_replace = os.replace

            def fail_json_publication(source, destination):
                if ".stage-" in Path(source).name and same_resolved_path(
                    destination,
                    json_path,
                ):
                    raise OSError("publication failure")
                return real_replace(source, destination)

            with patch("flushot.os.replace", side_effect=fail_json_publication):
                with self.assertRaisesRegex(OSError, "publication failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assertEqual([], os.listdir(tmpdir))

    def test_write_outputs_retains_backup_when_rollback_is_incomplete(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)
            real_replace = os.replace

            def fail_publication_and_csv_restore(source, destination):
                source_path = Path(source)
                if ".stage-" in source_path.name and same_resolved_path(
                    destination,
                    json_path,
                ):
                    raise OSError("publication failure")
                if ".backup-" in source_path.name and same_resolved_path(
                    destination,
                    csv_path,
                ):
                    raise OSError("rollback failure")
                return real_replace(source, destination)

            with patch(
                "flushot.os.replace",
                side_effect=fail_publication_and_csv_restore,
            ):
                with self.assertRaisesRegex(RuntimeError, "rollback was incomplete"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assertEqual(b"json sentinel", json_path.read_bytes())
            recovery_backups = list(Path(tmpdir).glob(".flu.csv.backup-*"))
            self.assertEqual(1, len(recovery_backups))
            self.assertEqual(b"csv sentinel", recovery_backups[0].read_bytes())
            self.assertEqual([], list(Path(tmpdir).glob("*.stage-*")))

    def test_cleanup_failure_does_not_mask_publication_failure(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)
            real_replace = os.replace
            real_unlink = Path.unlink
            cleanup_attempts = []

            def fail_json_publication(source, destination):
                if ".stage-" in Path(source).name and same_resolved_path(
                    destination,
                    json_path,
                ):
                    raise OSError("publication failure")
                return real_replace(source, destination)

            def fail_json_stage_cleanup(path, *args, **kwargs):
                cleanup_attempts.append(path.name)
                if path.name.startswith(".flu.json.stage-"):
                    raise OSError("cleanup failure")
                return real_unlink(path, *args, **kwargs)

            with patch(
                "flushot.os.replace", side_effect=fail_json_publication
            ), patch("flushot.Path.unlink", new=fail_json_stage_cleanup):
                with self.assertRaisesRegex(OSError, "publication failure") as raised:
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assertIsNone(raised.exception.__cause__)
            self.assertEqual(b"csv sentinel", csv_path.read_bytes())
            self.assertEqual(b"json sentinel", json_path.read_bytes())
            self.assertTrue(
                any(name.startswith(".flu.csv.backup-") for name in cleanup_attempts)
            )
            self.assertTrue(
                any(name.startswith(".flu.json.backup-") for name in cleanup_attempts)
            )
            self.assertEqual(1, len(list(Path(tmpdir).glob(".flu.json.stage-*"))))

    def test_cleanup_failure_does_not_mask_incomplete_rollback(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)
            real_replace = os.replace
            real_unlink = Path.unlink

            def fail_publication_and_csv_restore(source, destination):
                source_path = Path(source)
                if ".stage-" in source_path.name and same_resolved_path(
                    destination,
                    json_path,
                ):
                    raise OSError("publication failure")
                if ".backup-" in source_path.name and same_resolved_path(
                    destination,
                    csv_path,
                ):
                    raise OSError("rollback failure")
                return real_replace(source, destination)

            def fail_json_stage_cleanup(path, *args, **kwargs):
                if path.name.startswith(".flu.json.stage-"):
                    raise OSError("cleanup failure")
                return real_unlink(path, *args, **kwargs)

            with patch(
                "flushot.os.replace",
                side_effect=fail_publication_and_csv_restore,
            ), patch("flushot.Path.unlink", new=fail_json_stage_cleanup):
                with self.assertRaisesRegex(
                    RuntimeError, "rollback was incomplete"
                ) as raised:
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assertIsInstance(raised.exception.__cause__, OSError)
            self.assertEqual("publication failure", str(raised.exception.__cause__))
            recovery_backups = list(Path(tmpdir).glob(".flu.csv.backup-*"))
            self.assertEqual(1, len(recovery_backups))
            self.assertEqual(b"csv sentinel", recovery_backups[0].read_bytes())
            self.assertEqual(b"json sentinel", json_path.read_bytes())

    def test_successful_publication_attempts_all_cleanup_after_failure(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, json_path = self.write_output_sentinels(tmpdir)
            real_unlink = Path.unlink
            cleanup_attempts = []

            def fail_csv_backup_cleanup(path, *args, **kwargs):
                cleanup_attempts.append(path.name)
                if path.name.startswith(".flu.csv.backup-"):
                    raise OSError("cleanup failure")
                return real_unlink(path, *args, **kwargs)

            with patch("flushot.Path.unlink", new=fail_csv_backup_cleanup):
                with self.assertRaisesRegex(OSError, "cleanup failure"):
                    flushot.write_outputs(
                        records,
                        csv_path=csv_path,
                        json_path=json_path,
                    )

            self.assertNotEqual(b"csv sentinel", csv_path.read_bytes())
            self.assertEqual(records, json.loads(json_path.read_text(encoding="utf-8")))
            self.assertEqual(1, len(list(Path(tmpdir).glob(".flu.csv.backup-*"))))
            self.assertEqual([], list(Path(tmpdir).glob(".flu.json.backup-*")))
            self.assertTrue(
                any(name.startswith(".flu.json.stage-") for name in cleanup_attempts)
            )
            self.assertTrue(
                any(name.startswith(".flu.json.backup-") for name in cleanup_attempts)
            )

    def assert_malformed_records_preserve_outputs(self, records, message):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "flu.json"
            csv_path.write_bytes(b"csv sentinel")
            json_path.write_bytes(b"json sentinel")

            with self.assertRaisesRegex(ValueError, message):
                flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            self.assertEqual(b"csv sentinel", csv_path.read_bytes())
            self.assertEqual(b"json sentinel", json_path.read_bytes())

    def assert_non_regular_output_rejected(self, target_name, target_type):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "flu.json"
            target = csv_path if target_name == "csv" else json_path
            paired = json_path if target_name == "csv" else csv_path
            paired.write_bytes(b"paired sentinel")

            if target_type == "directory":
                target.mkdir()
                marker = target / "marker"
                marker.write_bytes(b"directory sentinel")
            else:
                os.mkfifo(target)

            with self.assertRaisesRegex(ValueError, "regular file"):
                flushot.write_outputs(
                    records,
                    csv_path=csv_path,
                    json_path=json_path,
                )

            self.assertEqual(b"paired sentinel", paired.read_bytes())
            if target_type == "directory":
                self.assertTrue(target.is_dir())
                self.assertEqual(b"directory sentinel", marker.read_bytes())
            else:
                self.assertTrue(stat.S_ISFIFO(target.stat().st_mode))
            self.assertEqual([], list(Path(tmpdir).glob(".*.stage-*")))
            self.assertEqual([], list(Path(tmpdir).glob(".*.backup-*")))

    def write_output_sentinels(self, tmpdir):
        csv_path = Path(tmpdir) / "flu.csv"
        json_path = Path(tmpdir) / "flu.json"
        csv_path.write_bytes(b"csv sentinel")
        json_path.write_bytes(b"json sentinel")
        return csv_path, json_path

    def assert_output_sentinels_and_no_artifacts(
        self,
        tmpdir,
        csv_path,
        json_path,
    ):
        self.assertEqual(b"csv sentinel", csv_path.read_bytes())
        self.assertEqual(b"json sentinel", json_path.read_bytes())
        self.assertEqual({"flu.csv", "flu.json"}, set(os.listdir(tmpdir)))

    def test_parse_records_fails_when_metadata_is_missing(self):
        with self.assertRaisesRegex(ValueError, "week number and ending date"):
            flushot.parse_records("<html><table cellpadding='3'></table></html>")

    def test_parse_records_rejects_out_of_range_week_number(self):
        for invalid_week in (99, 530, 531):
            html = FIXTURE.read_text(encoding="utf-8").replace(
                "Influenza Season Week 12", f"Influenza Season Week {invalid_week}"
            )

            with self.assertRaisesRegex(ValueError, "between 1 and 53"):
                flushot.parse_records(html)

    def test_parse_records_accepts_week_boundaries(self):
        for week_number in (1, 53):
            html = FIXTURE.read_text(encoding="utf-8").replace(
                "Influenza Season Week 12", f"Influenza Season Week {week_number}"
            )

            records = flushot.parse_records(html)

            self.assertEqual(str(week_number), records[0]["WEEK_NUM"])

    def test_parse_records_rejects_week_zero(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "Influenza Season Week 12", "Influenza Season Week 0"
        )

        with self.assertRaisesRegex(ValueError, "between 1 and 53"):
            flushot.parse_records(html)

    def test_parse_records_rejects_invalid_week_ending_date(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "March 23, 2024", "February 31, 2024"
        )

        with self.assertRaisesRegex(ValueError, "valid calendar date"):
            flushot.parse_records(html)

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

    def test_validate_fetch_url_rejects_embedded_credentials(self):
        with self.assertRaisesRegex(ValueError, "credentials"):
            flushot.validate_fetch_url("https://user:pass@www.cdc.gov/flu/weekly/")

    def test_validate_fetch_url_rejects_query_and_fragment(self):
        with self.assertRaisesRegex(ValueError, "query strings or fragments"):
            flushot.validate_fetch_url("https://www.cdc.gov/flu/weekly/?source=sample")

        with self.assertRaisesRegex(ValueError, "query strings or fragments"):
            flushot.validate_fetch_url("https://www.cdc.gov/flu/weekly/#summary")

    def test_validate_fetch_url_rejects_explicit_or_malformed_ports(self):
        rejected = (
            "https://www.cdc.gov:/flu/weekly/",
            "https://www.cdc.gov:443/flu/weekly/",
            "https://www.cdc.gov:8443/flu/weekly/",
            "https://www.cdc.gov:not-a-port/flu/weekly/",
            "https://www.cdc.gov:65536/flu/weekly/",
        )
        for url in rejected:
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "explicit port"):
                    flushot.validate_fetch_url(url)

    def test_fetch_html_rejects_explicit_port_before_building_opener(self):
        with patch("flushot.build_opener") as build_opener:
            with self.assertRaisesRegex(ValueError, "explicit port"):
                flushot.fetch_html("https://www.cdc.gov:443/flu/weekly/")

        build_opener.assert_not_called()

    def test_fetch_fluview_phase2_init_uses_exact_get_and_returns_json_object(self):
        expected = {"seasons": [{"seasonid": 65}], "mmwr": []}
        body = json.dumps(expected).encode("utf-8")
        response = FakeResponse(
            body=body,
            url=flushot.FLUVIEW_PHASE2_INIT_URL,
            headers={
                "Content-Length": str(len(body)),
                "Content-Type": "application/json; charset=utf-8",
            },
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            result = flushot.fetch_fluview_phase2_init(timeout="45")

        self.assertEqual(expected, result)
        self.assertEqual("GET", opener.request.get_method())
        self.assertEqual(flushot.FLUVIEW_PHASE2_INIT_URL, opener.request.full_url)
        self.assertIsNone(opener.request.data)
        self.assertEqual(45, opener.timeout)

    def test_fluview_phase4_fixture_records_exact_source_provenance(self):
        fixture = self.fluview_phase4_fixture()
        self.assertEqual(
            {
                "source_url": flushot.FLUVIEW_PHASE4_INIT_URL,
                "request_method": "GET",
                "retrieved_at": "2026-06-26T22:20:01Z",
                "response_content_type": "application/json; charset=utf-8",
                "full_response_bytes": 1017561,
                "full_response_sha256": "81d560217254765f707d65b949272c56c305bcd65d13fe001f172789a46543fe",
                "minimization": "Retains only current-season fields consumed by parse_fluview_phase4_mortality.",
            }, fixture["provenance"])

    def test_parse_fluview_phase4_mortality_preserves_national_and_region_grains(self):
        payload = self.fluview_phase4_fixture()["response"]
        metadata = self.fluview_phase2_metadata()
        original_payload = copy.deepcopy(payload)
        original_metadata = copy.deepcopy(metadata)

        mortality = flushot.parse_fluview_phase4_mortality(payload, metadata)

        self.assertEqual(65, mortality["season_id"])
        self.assertEqual(3364, mortality["current_week_id"])
        self.assertEqual(24, mortality["current_week_number"])
        self.assertEqual("2026-06-20", mortality["current_week_end"])
        self.assertEqual(38, len(mortality["national_weeks"]))
        self.assertEqual(184, mortality["season_total_deaths"])
        week = mortality["national_weeks"][3342]
        self.assertEqual(11, week["total_deaths"])
        self.assertEqual(
            {"previously_reported": 9, "newly_reported": 1, "total": 10},
            week["virus_deaths"][1],
        )
        self.assertEqual(set(range(1, 11)), set(mortality["hhs_season_totals"]))
        self.assertEqual(
            {"death_count": 12, "rate_per_million": 3.8},
            mortality["hhs_season_totals"][1],
        )
        self.assertEqual(payload, original_payload)
        self.assertEqual(metadata, original_metadata)

    def test_parse_fluview_phase4_mortality_ignores_collection_order(self):
        payload = self.fluview_phase4_fixture()["response"]
        metadata = self.fluview_phase2_metadata()
        expected = flushot.parse_fluview_phase4_mortality(payload, metadata)
        reordered = copy.deepcopy(payload)
        for name in ("weeks", "ped_flu_virus", "ped_flu_weekly", "ped_flu_map"):
            reordered[name].reverse()
        self.assertEqual(expected, flushot.parse_fluview_phase4_mortality(reordered, metadata))

    def test_parse_fluview_phase4_mortality_rejects_catalog_and_report_drift(self):
        base = self.fluview_phase4_fixture()["response"]
        mutations = []
        missing = copy.deepcopy(base); del missing["ped_flu_weekly"]; mutations.append(missing)
        duplicate_week = copy.deepcopy(base); duplicate_week["weeks"].append(copy.deepcopy(duplicate_week["weeks"][0])); mutations.append(duplicate_week)
        wrong_virus = copy.deepcopy(base); wrong_virus["ped_flu_virus"][0]["label"] = "Other"; mutations.append(wrong_virus)
        wrong_report = copy.deepcopy(base); wrong_report["ped_flu_reported"][0]["cwk"] = 23; mutations.append(wrong_report)
        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase4_mortality(payload, self.fluview_phase2_metadata())

    def test_parse_fluview_phase4_mortality_rejects_invalid_weekly_counts(self):
        base = self.fluview_phase4_fixture()["response"]
        mutations = []
        missing_virus = copy.deepcopy(base); missing_virus["ped_flu_weekly"].pop(); mutations.append(missing_virus)
        negative = copy.deepcopy(base); negative["ped_flu_weekly"][0]["pwk"] = -1; mutations.append(negative)
        bad_sum = copy.deepcopy(base); bad_sum["ped_flu_weekly"][0]["allwks"] = 1; mutations.append(bad_sum)
        bad_total = copy.deepcopy(base); bad_total["ped_flu_weekly"][0]["cwk"] = 1; bad_total["ped_flu_weekly"][0]["allwks"] = 1; mutations.append(bad_total)
        future = copy.deepcopy(base); future["ped_flu_weekly"][-1]["cwk"] = 1; future["ped_flu_weekly"][-1]["allwks"] = 1; mutations.append(future)
        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase4_mortality(payload, self.fluview_phase2_metadata())

    def test_parse_fluview_phase4_mortality_rejects_invalid_hhs_totals(self):
        base = self.fluview_phase4_fixture()["response"]
        mutations = []
        missing_region = copy.deepcopy(base); missing_region["ped_flu_map"].pop(); mutations.append(missing_region)
        duplicate_region = copy.deepcopy(base); duplicate_region["ped_flu_map"].append(copy.deepcopy(duplicate_region["ped_flu_map"][0])); mutations.append(duplicate_region)
        invalid_rate = copy.deepcopy(base); invalid_rate["ped_flu_map"][0]["rate"] = True; mutations.append(invalid_rate)
        mismatched_total = copy.deepcopy(base); mismatched_total["ped_flu_map"][0]["c"] += 1; mutations.append(mismatched_total)
        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase4_mortality(payload, self.fluview_phase2_metadata())

    def test_fetch_fluview_phase4_init_uses_exact_get_and_returns_json_object(self):
        expected = {"ped_flu_reported": [{"cwk": 24}], "weeks": []}
        body = json.dumps(expected).encode("utf-8")
        response = FakeResponse(
            body=body,
            url=flushot.FLUVIEW_PHASE4_INIT_URL,
            headers={"Content-Type": "application/json"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            result = flushot.fetch_fluview_phase4_init()

        self.assertEqual(expected, result)
        self.assertEqual("GET", opener.request.get_method())
        self.assertEqual(flushot.FLUVIEW_PHASE4_INIT_URL, opener.request.full_url)
        self.assertIsNone(opener.request.data)

    def test_fluview_phase2_fixture_records_exact_source_provenance(self):
        fixture = self.fluview_phase2_fixture()

        self.assertEqual(
            {
                "source_url": flushot.FLUVIEW_PHASE2_INIT_URL,
                "request_method": "GET",
                "retrieved_at": "2026-06-26T21:52:37Z",
                "response_content_type": "application/json; charset=utf-8",
                "full_response_bytes": 357473,
                "full_response_sha256": (
                    "63ae6be2711dbe7ddd500f2d8b31f25170c6e128395021f11b353443a130aa56"
                ),
                "minimization": (
                    "Retains only fields consumed by "
                    "parse_fluview_phase2_metadata."
                ),
            },
            fixture["provenance"],
        )

    def test_parse_fluview_phase2_metadata_normalizes_current_catalogs(self):
        payload = self.fluview_phase2_fixture()["response"]
        original = copy.deepcopy(payload)

        metadata = flushot.parse_fluview_phase2_metadata(payload)

        self.assertEqual(payload, original)
        self.assertEqual(65, metadata["season_id"])
        self.assertEqual("2025-26", metadata["season_label"])
        self.assertEqual(3364, metadata["week_id"])
        self.assertEqual(24, metadata["week_number"])
        self.assertEqual("2026-06-20", metadata["week_end"])
        self.assertEqual(
            {region_id: f"Region {region_id}" for region_id in range(1, 11)},
            metadata["hhs_regions"],
        )
        self.assertEqual(
            {1: "Public Health Labs", 2: "Clinical Labs"},
            metadata["lab_types"],
        )
        self.assertEqual(
            {
                "description": "AH1SWINE",
                "label": "A (H1N1)pdm09",
                "lab_type_id": 1,
            },
            metadata["viruses"][4],
        )
        self.assertEqual(12, len(metadata["viruses"]))

    def test_parse_fluview_phase2_metadata_ignores_collection_order(self):
        payload = self.fluview_phase2_fixture()["response"]
        expected = flushot.parse_fluview_phase2_metadata(payload)
        reordered = copy.deepcopy(payload)
        for collection in ("seasons", "mmwr", "hhsregion", "labtypes", "viruslist"):
            reordered[collection].reverse()

        self.assertEqual(expected, flushot.parse_fluview_phase2_metadata(reordered))

    def test_parse_fluview_phase2_metadata_rejects_missing_or_non_list_collections(self):
        for collection in ("seasons", "mmwr", "hhsregion", "labtypes", "viruslist"):
            for replacement in (None, {}, "records", [1]):
                payload = copy.deepcopy(self.fluview_phase2_fixture()["response"])
                payload[collection] = replacement

                with self.subTest(collection=collection, replacement=replacement):
                    with self.assertRaisesRegex(
                        ValueError,
                        f"FluView {collection} must be an array of objects",
                    ):
                        flushot.parse_fluview_phase2_metadata(payload)

        with self.assertRaisesRegex(ValueError, "metadata must be an object"):
            flushot.parse_fluview_phase2_metadata([])

    def test_parse_fluview_phase2_metadata_rejects_duplicate_identifiers(self):
        cases = (
            ("seasons", "seasonid", "season"),
            ("mmwr", "mmwrid", "MMWR"),
            ("hhsregion", "hhsregionid", "HHS region"),
            ("labtypes", "labtypeid", "lab type"),
            ("viruslist", "virusid", "virus"),
        )
        for collection, _, label in cases:
            payload = copy.deepcopy(self.fluview_phase2_fixture()["response"])
            payload[collection].append(copy.deepcopy(payload[collection][0]))

            with self.subTest(collection=collection):
                with self.assertRaisesRegex(
                    ValueError,
                    f"duplicate {label} identifier",
                ):
                    flushot.parse_fluview_phase2_metadata(payload)

    def test_parse_fluview_phase2_metadata_rejects_invalid_season_and_week_metadata(self):
        mutations = (
            (lambda payload: payload["seasons"][0].update(seasonid=True), "season identifier"),
            (lambda payload: payload["seasons"][0].update(label=" "), "season label"),
            (
                lambda payload: [season.update(enabled=0) for season in payload["seasons"]],
                "enabled season",
            ),
            (lambda payload: payload["mmwr"][-1].update(mmwrid=True), "MMWR identifier"),
            (lambda payload: payload["mmwr"][-1].update(weeknumber=0), "week number"),
            (lambda payload: payload["mmwr"][-1].update(weekend="June 20"), "ISO date"),
            (lambda payload: payload["mmwr"][-1].update(yearweek=202625), "yearweek"),
            (
                lambda payload: [week.update(seasonid=64) for week in payload["mmwr"]],
                "current enabled season",
            ),
        )
        for mutate, message in mutations:
            payload = copy.deepcopy(self.fluview_phase2_fixture()["response"])
            mutate(payload)

            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    flushot.parse_fluview_phase2_metadata(payload)

    def test_parse_fluview_phase2_metadata_rejects_invalid_catalogs(self):
        mutations = (
            (lambda payload: payload["hhsregion"].pop(), "regions 1 through 10"),
            (
                lambda payload: payload["hhsregion"][0].update(hhsregionname="First"),
                "canonical name",
            ),
            (lambda payload: payload["labtypes"][0].update(labname=" "), "lab type name"),
            (lambda payload: payload["labtypes"].pop(0), "lab types 1 and 2"),
            (lambda payload: payload["viruslist"][0].update(label=""), "virus label"),
            (lambda payload: payload["viruslist"][0].update(labtypeid=9), "known lab type"),
        )
        for mutate, message in mutations:
            payload = copy.deepcopy(self.fluview_phase2_fixture()["response"])
            mutate(payload)

            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    flushot.parse_fluview_phase2_metadata(payload)

    def test_fluview_phase2_region_fixture_records_exact_source_provenance(self):
        fixture = self.fluview_phase2_region_fixture()

        self.assertEqual(
            {
                "source_url": flushot.FLUVIEW_PHASE2_DATA_URL,
                "request_method": "POST",
                "request_body": {
                    "AppVersion": "Public",
                    "SeasonID": 65,
                    "RegionTypeID": 1,
                    "RegionID": 1,
                },
                "retrieved_at": "2026-06-26T21:58:17Z",
                "response_content_type": "application/json; charset=utf-8",
                "full_response_bytes": 1166773,
                "full_response_sha256": (
                    "519d0af02375ba80319b1981ba45fd3659d71a51e393d32d68583e0eba31b994"
                ),
                "minimization": (
                    "Retains two official weeks and every lab, HHS region, "
                    "national region, virus category, positional metric, and "
                    "declared-structure field consumed by "
                    "parse_fluview_phase2_region_data."
                ),
            },
            fixture["provenance"],
        )

    def test_parse_fluview_phase2_region_data_normalizes_declared_structure(self):
        fixture = self.fluview_phase2_region_fixture()
        payload = fixture["response"]
        metadata = self.fluview_phase2_metadata()
        original_payload = copy.deepcopy(payload)
        original_metadata = copy.deepcopy(metadata)

        regional_data = flushot.parse_fluview_phase2_region_data(payload, metadata)

        self.assertEqual(65, regional_data["season_id"])
        self.assertEqual(3364, regional_data["current_week_id"])
        self.assertEqual([3327, 3364], list(regional_data["weeks"]))
        current = regional_data["weeks"][3364]
        self.assertEqual(202624, current["yearweek"])
        self.assertEqual(24, current["week_number"])
        self.assertEqual("2026-06-20", current["week_end"])
        self.assertEqual({1, 2}, set(current["labs"]))
        public_health = current["labs"][1]
        self.assertEqual(set(range(1, 11)), set(public_health["hhs_regions"]))
        self.assertEqual(0, public_health["national"]["region_id"])
        region_one = public_health["hhs_regions"][1]
        self.assertEqual(
            {"cumulative": 889, "three_weeks": 4, "current": 1},
            region_one["virus_counts"][6],
        )
        self.assertEqual(12.5, region_one["percent_positive"])
        self.assertEqual(0.7318, region_one["weighted_ili"])
        self.assertFalse(region_one["elevated"])
        self.assertTrue(region_one["weekly_ili_data"])
        self.assertFalse(region_one["insufficient"])
        self.assertEqual(payload, original_payload)
        self.assertEqual(metadata, original_metadata)

    def test_parse_fluview_phase2_region_data_ignores_collection_order(self):
        payload = self.fluview_phase2_region_fixture()["response"]
        metadata = self.fluview_phase2_metadata()
        expected = flushot.parse_fluview_phase2_region_data(payload, metadata)
        reordered = copy.deepcopy(payload)
        reordered["mmwr"].reverse()
        reordered["viruslist"].reverse()
        summary = reordered["WHO_Virus_Counts_Summary_Cumulative"]
        summary["data"].reverse()
        for week in summary["data"]:
            week[1].reverse()
            for lab in week[1]:
                lab[1:] = reversed(lab[1:])
                for segment in lab[1:]:
                    segment[0][1].reverse()
                    for region in segment[0][1]:
                        region[1].reverse()

        self.assertEqual(
            expected,
            flushot.parse_fluview_phase2_region_data(reordered, metadata),
        )

    def test_parse_fluview_phase2_region_data_rejects_structure_drift(self):
        fixture = self.fluview_phase2_region_fixture()
        mutations = []
        missing_summary = copy.deepcopy(fixture["response"])
        del missing_summary["WHO_Virus_Counts_Summary_Cumulative"]
        mutations.append(missing_summary)
        missing_structure = copy.deepcopy(fixture["response"])
        del missing_structure["WHO_Virus_Counts_Summary_Cumulative"]["data_structure"]
        mutations.append(missing_structure)
        renamed_field = copy.deepcopy(fixture["response"])
        renamed_field["WHO_Virus_Counts_Summary_Cumulative"]["data_structure"][0] = "week"
        mutations.append(renamed_field)
        malformed_week = copy.deepcopy(fixture["response"])
        malformed_week["WHO_Virus_Counts_Summary_Cumulative"]["data"][0].append([])
        mutations.append(malformed_week)
        malformed_lab = copy.deepcopy(fixture["response"])
        malformed_lab["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0] = [1]
        mutations.append(malformed_lab)
        malformed_region = copy.deepcopy(fixture["response"])
        malformed_region["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][1][0][1][0].append(0)
        mutations.append(malformed_region)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase2_region_data(
                        payload,
                        self.fluview_phase2_metadata(),
                    )

    def test_parse_fluview_phase2_region_data_rejects_catalog_disagreement(self):
        fixture = self.fluview_phase2_region_fixture()
        mutations = []
        duplicate_week = copy.deepcopy(fixture["response"])
        duplicate_week["mmwr"].append(copy.deepcopy(duplicate_week["mmwr"][0]))
        mutations.append(duplicate_week)
        unknown_virus = copy.deepcopy(fixture["response"])
        unknown_virus["viruslist"][0]["virusid"] = 99
        mutations.append(unknown_virus)
        wrong_lab = copy.deepcopy(fixture["response"])
        wrong_lab["viruslist"][0]["labtypeid"] = 2
        mutations.append(wrong_lab)
        wrong_label = copy.deepcopy(fixture["response"])
        wrong_label["viruslist"][0]["label"] = "Different"
        mutations.append(wrong_label)
        missing_current = copy.deepcopy(fixture["response"])
        missing_current["mmwr"] = missing_current["mmwr"][:1]
        missing_current["WHO_Virus_Counts_Summary_Cumulative"]["data"] = (
            missing_current["WHO_Virus_Counts_Summary_Cumulative"]["data"][:1]
        )
        mutations.append(missing_current)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase2_region_data(
                        payload,
                        self.fluview_phase2_metadata(),
                    )

    def test_parse_fluview_phase2_region_data_rejects_incomplete_regions_and_viruses(self):
        fixture = self.fluview_phase2_region_fixture()
        mutations = []
        missing_hhs_region = copy.deepcopy(fixture["response"])
        missing_hhs_region["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][1][0][1].pop()
        mutations.append(missing_hhs_region)
        wrong_national_region = copy.deepcopy(fixture["response"])
        wrong_national_region["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][2][0][1][0][0] = 1
        mutations.append(wrong_national_region)
        duplicate_lab = copy.deepcopy(fixture["response"])
        duplicate_lab["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1].append(
            copy.deepcopy(duplicate_lab["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0])
        )
        mutations.append(duplicate_lab)
        missing_virus = copy.deepcopy(fixture["response"])
        missing_virus["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][1][0][1][0][1].pop()
        mutations.append(missing_virus)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase2_region_data(
                        payload,
                        self.fluview_phase2_metadata(),
                    )

    def test_parse_fluview_phase2_region_data_rejects_invalid_counts_metrics_and_flags(self):
        fixture = self.fluview_phase2_region_fixture()
        mutations = []
        negative_count = copy.deepcopy(fixture["response"])
        negative_count["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][1][0][1][0][1][0][1] = -1
        mutations.append(negative_count)
        unordered_counts = copy.deepcopy(fixture["response"])
        unordered_counts["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][1][0][1][0][1][0][2] = 1
        mutations.append(unordered_counts)
        invalid_percent = copy.deepcopy(fixture["response"])
        invalid_percent["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][1][0][1][0][2] = 101
        mutations.append(invalid_percent)
        invalid_metric_type = copy.deepcopy(fixture["response"])
        invalid_metric_type["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][1][0][1][0][5] = True
        mutations.append(invalid_metric_type)
        invalid_flag = copy.deepcopy(fixture["response"])
        invalid_flag["WHO_Virus_Counts_Summary_Cumulative"]["data"][0][1][0][1][0][1][0][7] = 2
        mutations.append(invalid_flag)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase2_region_data(
                        payload,
                        self.fluview_phase2_metadata(),
                    )

    def test_fetch_fluview_phase2_region_data_uses_reviewed_post_body(self):
        expected = {"mmwr": [], "WHO_Virus_Counts_Summary_Cumulative": {}}
        body = json.dumps(expected).encode("utf-8")
        response = FakeResponse(
            body=body,
            url=flushot.FLUVIEW_PHASE2_DATA_URL,
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            result = flushot.fetch_fluview_phase2_region_data(65, 3)

        self.assertEqual(expected, result)
        self.assertEqual("POST", opener.request.get_method())
        self.assertEqual(flushot.FLUVIEW_PHASE2_DATA_URL, opener.request.full_url)
        self.assertEqual("application/json", opener.request.get_header("Content-type"))
        self.assertEqual(
            b'{"AppVersion":"Public","RegionID":3,"RegionTypeID":1,"SeasonID":65}',
            opener.request.data,
        )

    def test_fetch_fluview_phase2_line_csv_uses_reviewed_post_body(self):
        expected = "YEAR,WEEK,NUM. OF PROVIDERS\n2026,24,270\n"
        body = expected.encode("utf-8")
        response = FakeResponse(
            body=body,
            url=flushot.FLUVIEW_PHASE2_LINE_CSV_URL,
            headers={"Content-Type": "application/octet-stream"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            result = flushot.fetch_fluview_phase2_line_csv(65, 3)

        self.assertEqual(expected, result)
        self.assertEqual("POST", opener.request.get_method())
        self.assertEqual(flushot.FLUVIEW_PHASE2_LINE_CSV_URL, opener.request.full_url)
        self.assertEqual("application/json", opener.request.get_header("Content-type"))
        self.assertEqual(
            b'{"AppVersion":"Public","DatasourceDT":[{"ID":1,"Name":"ILINet"}],'
            b'"RegionTypeId":1,"SeasonsDT":[{"ID":65,"Name":"65"}],'
            b'"SubRegionsDT":[{"ID":3,"Name":"3"}]}',
            opener.request.data,
        )

    def test_fluview_phase2_line_fixture_records_exact_source_provenance(self):
        fixture = self.fluview_phase2_line_fixture()

        self.assertEqual(
            {
                "source_url": flushot.FLUVIEW_PHASE2_LINE_CSV_URL,
                "request_method": "POST",
                "request_body": {
                    "AppVersion": "Public",
                    "DatasourceDT": [{"ID": 1, "Name": "ILINet"}],
                    "RegionTypeId": 1,
                    "SubRegionsDT": [{"ID": 1, "Name": "1"}],
                    "SeasonsDT": [{"ID": 65, "Name": "65"}],
                },
                "retrieved_at": "2026-06-26T22:15:04Z",
                "response_content_type": "application/octet-stream",
                "full_response_bytes": 2583,
                "full_response_sha256": (
                    "985493ce04d949f06ac66d846b9bf56e513711bf362c3c00b6f0241448115128"
                ),
                "minimization": (
                    "Retains the exact title and header plus first, "
                    "year-boundary, and current rows consumed by "
                    "parse_fluview_phase2_line_csv."
                ),
            },
            fixture["provenance"],
        )

    def test_parse_fluview_phase2_line_csv_normalizes_provider_and_visit_counts(self):
        source = self.fluview_phase2_line_fixture()["response_text"]

        decoded = flushot.parse_fluview_phase2_line_csv(source, 65, 1)

        self.assertEqual(65, decoded["season_id"])
        self.assertEqual(1, decoded["region_id"])
        self.assertEqual([202540, 202553, 202601, 202624], list(decoded["weeks"]))
        current = decoded["weeks"][202624]
        self.assertEqual(2026, current["year"])
        self.assertEqual(24, current["week_number"])
        self.assertEqual(217, current["age_0_4"])
        self.assertEqual(349, current["age_5_24"])
        self.assertEqual(303, current["age_25_49"])
        self.assertEqual(148, current["age_50_64"])
        self.assertEqual(208, current["age_65_plus"])
        self.assertEqual(1225, current["ili_total"])
        self.assertEqual(162510, current["total_patients"])
        self.assertEqual(270, current["provider_count"])
        self.assertEqual(0.7538, current["unweighted_ili"])
        self.assertEqual(0.7318, current["weighted_ili"])
        self.assertEqual(
            "PERCENTAGE OF VISITS FOR INFLUENZA-LIKE-ILLNESS REPORTED BY SENTINEL PROVIDERS",
            source.splitlines()[0],
        )

    def test_parse_fluview_phase2_line_csv_ignores_data_row_order(self):
        source = self.fluview_phase2_line_fixture()["response_text"]
        lines = source.splitlines()
        reordered = "\n".join(lines[:2] + list(reversed(lines[2:]))) + "\n"

        self.assertEqual(
            flushot.parse_fluview_phase2_line_csv(source, 65, 1),
            flushot.parse_fluview_phase2_line_csv(reordered, 65, 1),
        )

    def test_parse_fluview_phase2_line_csv_rejects_envelope_drift(self):
        source = self.fluview_phase2_line_fixture()["response_text"]
        mutations = (
            source.replace("PERCENTAGE OF VISITS", "VISITS", 1),
            source.replace("NUM. OF PROVIDERS", "JURISDICTIONS", 1),
            source + "\n",
            source.replace("2026,24,", "2025,40,", 1),
        )

        with self.assertRaises(ValueError):
            flushot.parse_fluview_phase2_line_csv([], 65, 1)
        for mutated in mutations:
            with self.subTest(mutated=mutated):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase2_line_csv(mutated, 65, 1)

    def test_parse_fluview_phase2_line_csv_rejects_invalid_rows(self):
        source = self.fluview_phase2_line_fixture()["response_text"]
        mutations = (
            source.replace("2025,40,", "year,40,", 1),
            source.replace("2025,40,", "1899,40,", 1),
            source.replace("2025,40,", "2025,54,", 1),
            source.replace("505,,217", "505,1,217", 1),
            source.replace("263,549,505", "-1,549,505", 1),
            source.replace("1850,168814", "1851,168814", 1),
            source.replace("1850,168814", "1850,1000", 1),
            source.replace("168814,280", "168814,0", 1),
            source.replace("1.09588,1.08073", "1.0,1.08073", 1),
            source.replace("1.09588,1.08073", "1.09588,NaN", 1),
            source.replace("1.09588,1.08073", f"0.{('1' * 100)},1.08073", 1),
        )

        for mutated in mutations:
            with self.subTest(mutated=mutated):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase2_line_csv(mutated, 65, 1)

    def test_parse_fluview_phase2_line_csv_rejects_invalid_identifiers(self):
        source = self.fluview_phase2_line_fixture()["response_text"]

        for season_id, region_id in ((True, 1), (0, 1), (65, True), (65, 0), (65, 11)):
            with self.subTest(season_id=season_id, region_id=region_id):
                with self.assertRaises(ValueError):
                    flushot.parse_fluview_phase2_line_csv(
                        source,
                        season_id,
                        region_id,
                    )

    def test_build_fluview_v2_dataset_emits_truthful_versioned_schema(self):
        metadata, regional, ilinet, mortality = self.fluview_v2_sources()
        originals = copy.deepcopy((metadata, regional, ilinet, mortality))

        dataset = flushot.build_fluview_v2_dataset(
            metadata, regional, ilinet, mortality
        )
        json.dumps(dataset)

        self.assertEqual(2, dataset["schema_version"])
        self.assertEqual(
            {
                "schema_version",
                "season",
                "laboratory_virus_categories",
                "regional_weekly",
                "pediatric_mortality",
            },
            set(dataset),
        )
        self.assertEqual(
            {
                "id": 65,
                "label": "2025-26",
                "current_week": {
                    "mmwr_id": 3364,
                    "yearweek": 202624,
                    "week_number": 24,
                    "week_end": "2026-06-20",
                },
            },
            dataset["season"],
        )
        self.assertEqual(12, len(dataset["laboratory_virus_categories"]))
        self.assertEqual(20, len(dataset["regional_weekly"]))
        current = next(
            row for row in dataset["regional_weekly"]
            if row["mmwr_id"] == 3364 and row["hhs_region_id"] == 1
        )
        self.assertEqual("Region 1", current["hhs_region_name"])
        self.assertEqual(270, current["ili"]["provider_count"])
        self.assertEqual(0.7318, current["ili"]["weighted_ili_percent"])
        self.assertEqual(2.2, current["ili"]["baseline_percent"])
        self.assertFalse(current["ili"]["is_elevated"])
        self.assertEqual(
            {"virus_id": 6, "weekly_positive_count": 1, "three_week_positive_count": 4,
             "season_cumulative_positive_count": 889},
            next(item for item in current["laboratory_surveillance"]["public_health"]["virus_counts"] if item["virus_id"] == 6),
        )
        self.assertEqual(
            "national_weekly_and_hhs_season_totals",
            dataset["pediatric_mortality"]["scope"],
        )
        self.assertEqual(184, dataset["pediatric_mortality"]["season_total_deaths"])
        self.assertEqual(38, len(dataset["pediatric_mortality"]["national_weekly"]))
        self.assertEqual(10, len(dataset["pediatric_mortality"]["hhs_season_totals"]))
        self.assertEqual(
            [
                {"id": 1, "label": "A"},
                {"id": 2, "label": "B"},
                {"id": 3, "label": "A/B Not Distinguished"},
                {"id": 4, "label": "A and B"},
            ],
            dataset["pediatric_mortality"]["virus_categories"],
        )
        serialized = json.dumps(dataset)
        self.assertNotIn("ped_deaths", serialized)
        self.assertNotIn("num_juris", serialized)
        self.assertEqual(originals, (metadata, regional, ilinet, mortality))

    def test_fluview_all_region_line_fixture_records_exact_provenance(self):
        fixture = json.loads(
            FLUVIEW_ALL_REGION_LINES_FIXTURE.read_text(encoding="utf-8")
        )
        self.assertEqual(flushot.FLUVIEW_PHASE2_LINE_CSV_URL, fixture["provenance"]["source_url"])
        self.assertEqual("2026-06-26T22:24:21Z", fixture["provenance"]["retrieved_at"])
        expected_hashes = {
            1: (2583, "985493ce04d949f06ac66d846b9bf56e513711bf362c3c00b6f0241448115128"),
            2: (2668, "41c6d063a4b2d816cf5394c229761d6c0799b27543ac09efc8756a54f7c872d9"),
            3: (2628, "fbfbf91cbf92c7f1cba257c690bb062db7fe6b6442731b002023636b9a7de14f"),
            4: (2738, "ce9f4b36460efdaa7360f96e01a069793adfe47cf072f76d9ea4fe78aea47f6d"),
            5: (2649, "f67b40bfc689347a71268640e3bba0c8ddad4270323f141d06f406333e0624c2"),
            6: (2576, "3ee7164c30bc84e1f5c021627f125ed67779c48d8364e7cef79d026536215f69"),
            7: (2436, "a44ac814c8a7bfe37ab922e2319fecfd48508f052ad406672dbb272bfc40b1e8"),
            8: (2518, "560844e5356963582a58f6591f77301fb1a0f202762f983f12d507d0cdf79b7a"),
            9: (2733, "32bac37c510c628be318c60128ebe99d4fc063b82849e423a87ff741b0be6cb4"),
            10: (2580, "5137935ad6fe09076a9e621fdf0403b51693a5645bee1898fd479e860f0e6b9a"),
        }
        self.assertEqual(
            expected_hashes,
            {
                item["region_id"]: (
                    item["full_response_bytes"], item["full_response_sha256"]
                )
                for item in fixture["regions"]
            },
        )
        for item in fixture["regions"]:
            self.assertEqual(
                [{"ID": item["region_id"], "Name": str(item["region_id"])}],
                item["request_body"]["SubRegionsDT"],
            )

    def test_build_fluview_v2_dataset_orders_records_and_categories(self):
        metadata, regional, ilinet, mortality = self.fluview_v2_sources()
        ilinet = dict(reversed(list(ilinet.items())))

        dataset = flushot.build_fluview_v2_dataset(metadata, regional, ilinet, mortality)

        identities = [
            (row["mmwr_id"], row["hhs_region_id"])
            for row in dataset["regional_weekly"]
        ]
        self.assertEqual(sorted(identities), identities)
        self.assertEqual(
            list(range(1, 13)),
            [item["id"] for item in dataset["laboratory_virus_categories"]],
        )

    def test_build_fluview_v2_dataset_rejects_source_identity_and_coverage_drift(self):
        sources = self.fluview_v2_sources()
        mutations = []
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        regional["season_id"] = 64
        mutations.append((metadata, regional, ilinet, mortality))
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        mortality["current_week_id"] = 3363
        mutations.append((metadata, regional, ilinet, mortality))
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        ilinet.pop(10)
        mutations.append((metadata, regional, ilinet, mortality))
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        ilinet[1]["region_id"] = 2
        mutations.append((metadata, regional, ilinet, mortality))
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        ilinet[1]["weeks"].pop(202540)
        mutations.append((metadata, regional, ilinet, mortality))
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        mortality["national_weeks"].pop(3327)
        mutations.append((metadata, regional, ilinet, mortality))

        for args in mutations:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    flushot.build_fluview_v2_dataset(*args)

    def test_build_fluview_v2_dataset_rejects_ili_disagreement(self):
        sources = self.fluview_v2_sources()
        mutations = []
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        ilinet[1]["weeks"][202624]["weighted_ili"] = 9.9
        mutations.append((metadata, regional, ilinet, mortality))
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        regional["weeks"][3364]["labs"][2]["hhs_regions"][1]["baseline"] = 9.9
        mutations.append((metadata, regional, ilinet, mortality))
        metadata, regional, ilinet, mortality = copy.deepcopy(sources)
        regional["weeks"][3364]["labs"][1]["hhs_regions"][1]["weekly_ili_data"] = False
        mutations.append((metadata, regional, ilinet, mortality))

        for args in mutations:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    flushot.build_fluview_v2_dataset(*args)

    def test_build_fluview_v2_dataset_rejects_malformed_metric_types(self):
        metadata, regional, ilinet, mortality = self.fluview_v2_sources()
        ilinet[1]["weeks"][202624]["weighted_ili"] = None

        with self.assertRaises(ValueError):
            flushot.build_fluview_v2_dataset(
                metadata, regional, ilinet, mortality
            )

        metadata, regional, ilinet, mortality = self.fluview_v2_sources()
        regional["weeks"][3364]["labs"][1]["hhs_regions"][1]["elevated"] = 0

        with self.assertRaises(ValueError):
            flushot.build_fluview_v2_dataset(
                metadata, regional, ilinet, mortality
            )

    def test_fluview_post_transports_reject_invalid_identifiers_before_network(self):
        invalid_seasons = (True, 0, -1, "65", 1.5)
        invalid_regions = (False, 0, 11, -1, "3", 1.5)

        for function in (
            flushot.fetch_fluview_phase2_region_data,
            flushot.fetch_fluview_phase2_line_csv,
        ):
            for season_id in invalid_seasons:
                with self.subTest(function=function.__name__, season_id=season_id):
                    with patch("flushot.build_opener") as build_opener:
                        with self.assertRaisesRegex(ValueError, "season identifier"):
                            function(season_id, 3)
                    build_opener.assert_not_called()

            for region_id in invalid_regions:
                with self.subTest(function=function.__name__, region_id=region_id):
                    with patch("flushot.build_opener") as build_opener:
                        with self.assertRaisesRegex(ValueError, "HHS region identifier"):
                            function(65, region_id)
                    build_opener.assert_not_called()

    def test_fluview_json_transport_requires_exact_final_url_before_body(self):
        response = FakeResponse(
            body=b'{"private":"ignored"}',
            url="https://gis.cdc.gov/grasp/flu2/other",
            headers={"Content-Type": "application/json"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "exact requested URL"):
                flushot.fetch_fluview_phase2_init()

        self.assertEqual(0, response.read_calls)

    def test_fluview_json_transport_rejects_unreviewed_media_before_body(self):
        headers_cases = (
            ({}, "declare a JSON Content-Type"),
            ({"Content-Type": "text/html"}, "must be application/json"),
            (
                {"Content-Type": "application/json; charset=iso-8859-1"},
                "must use UTF-8",
            ),
            (
                {"Content-Type": "application/json; profile=private"},
                "unreviewed parameters",
            ),
        )

        for headers, message in headers_cases:
            response = FakeResponse(
                body=b'{"private":"ignored"}',
                url=flushot.FLUVIEW_PHASE2_INIT_URL,
                headers=headers,
            )
            opener = FakeOpener(response)

            with self.subTest(headers=headers):
                with patch("flushot.build_opener", return_value=opener):
                    with self.assertRaisesRegex(ValueError, message):
                        flushot.fetch_fluview_phase2_init()
                self.assertEqual(0, response.read_calls)

        duplicate_headers = Message()
        duplicate_headers["Content-Type"] = "application/json"
        duplicate_headers["Content-Type"] = "application/json"
        response = FakeResponse(
            body=b'{"private":"ignored"}',
            url=flushot.FLUVIEW_PHASE2_INIT_URL,
            headers=duplicate_headers,
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "exactly one Content-Type"):
                flushot.fetch_fluview_phase2_init()
        self.assertEqual(0, response.read_calls)

    def test_fluview_csv_transport_requires_octet_stream_before_body(self):
        for content_type in (
            None,
            "text/csv",
            "application/json",
            "application/octet-stream; charset=utf-8",
        ):
            headers = {} if content_type is None else {"Content-Type": content_type}
            response = FakeResponse(
                body=b"private,ignored\n",
                url=flushot.FLUVIEW_PHASE2_LINE_CSV_URL,
                headers=headers,
            )
            opener = FakeOpener(response)

            with self.subTest(content_type=content_type):
                with patch("flushot.build_opener", return_value=opener):
                    with self.assertRaisesRegex(
                        ValueError,
                        "application/octet-stream",
                    ):
                        flushot.fetch_fluview_phase2_line_csv(65, 3)
                self.assertEqual(0, response.read_calls)

    def test_fluview_json_transport_rejects_malformed_or_non_object_json(self):
        for body, message in (
            (b'{"private":', "valid JSON"),
            (b"[]", "JSON object"),
            (b"null", "JSON object"),
        ):
            response = FakeResponse(
                body=body,
                url=flushot.FLUVIEW_PHASE2_INIT_URL,
                headers={"Content-Type": "application/json"},
            )
            opener = FakeOpener(response)

            with self.subTest(body=body):
                with patch("flushot.build_opener", return_value=opener):
                    with self.assertRaisesRegex(ValueError, message) as error:
                        flushot.fetch_fluview_phase2_init()
                self.assertNotIn("private", str(error.exception))
                self.assertGreater(response.read_calls, 0)

    def test_fetch_timeout_rejects_invalid_or_out_of_range_values(self):
        self.assertEqual(30, flushot.fetch_timeout(""))
        self.assertEqual(30, flushot.fetch_timeout("not-a-timeout"))
        self.assertEqual(30, flushot.fetch_timeout(0))
        self.assertEqual(30, flushot.fetch_timeout(301))
        self.assertEqual(45, flushot.fetch_timeout("45"))

    def test_redirect_handler_revalidates_targets(self):
        handler = flushot.CDCNoRedirectHandler()
        request = Request(flushot.CDC_FLU_URL)

        with self.assertRaisesRegex(ValueError, "cdc.gov"):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://example.com/private",
            )

        with self.assertRaisesRegex(ValueError, "explicit port"):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://www.cdc.gov:8443/flu/weekly/",
            )

        with self.assertRaisesRegex(ValueError, "redirects are not allowed"):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://www.cdc.gov/flu/weekly/index.html",
            )

    def test_read_response_rejects_declared_oversize(self):
        response = FakeResponse(headers={"Content-Length": "11"})

        with self.assertRaisesRegex(ValueError, "maximum allowed size"):
            flushot.read_response_bytes(response, max_bytes=10)

        self.assertEqual(0, response.read_calls)

    def test_read_response_accepts_missing_or_exact_content_length(self):
        for headers in ({}, {"Content-Length": "10"}):
            with self.subTest(headers=headers):
                response = FakeResponse(body=b"1234567890", headers=headers)

                self.assertEqual(
                    b"1234567890",
                    flushot.read_response_bytes(response, max_bytes=10),
                )

    def test_read_response_rejects_body_shorter_than_content_length(self):
        response = FakeResponse(
            body=b"123456789",
            headers={"Content-Length": "10"},
        )

        with self.assertRaisesRegex(ValueError, "does not match Content-Length"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_read_response_rejects_body_longer_than_content_length(self):
        response = FakeResponse(
            body=b"1234567890",
            headers={"Content-Length": "9"},
        )

        with self.assertRaisesRegex(ValueError, "does not match Content-Length"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_read_response_rejects_duplicate_content_length_before_reading(self):
        for values in (("10", "10"), ("9", "10")):
            with self.subTest(values=values):
                headers = Message()
                for value in values:
                    headers["Content-Length"] = value
                response = FakeResponse(body=b"1234567890", headers=headers)

                with self.assertRaisesRegex(ValueError, "exactly one Content-Length"):
                    flushot.read_response_bytes(response, max_bytes=10)

                self.assertEqual(0, response.read_calls)

    def test_read_response_rejects_noncanonical_content_length_before_reading(self):
        rejected = ("", " 10", "10 ", "+10", "-1", "10, 10", "1.0", "ten")
        for content_length in rejected:
            with self.subTest(content_length=content_length):
                response = FakeResponse(
                    body=b"1234567890",
                    headers={"Content-Length": content_length},
                )

                with self.assertRaisesRegex(ValueError, "ASCII decimal"):
                    flushot.read_response_bytes(response, max_bytes=10)

                self.assertEqual(0, response.read_calls)

    def test_read_response_rejects_streamed_oversize(self):
        response = FakeResponse(body=b"12345678901")

        with self.assertRaisesRegex(ValueError, "maximum allowed size"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_read_response_rejects_streamed_oversize_after_smaller_declaration(self):
        response = FakeResponse(
            body=b"12345678901",
            headers={"Content-Length": "1"},
        )

        with self.assertRaisesRegex(ValueError, "maximum allowed size"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_fetch_html_requires_exact_success_status_before_metadata_or_body(self):
        for status in (199, 201, 204, 206, 301, 400, 404, 429, 500):
            response = FakeResponse(
                body=b"private response",
                status=status,
                headers={"Content-Type": "text/html; charset=utf-8"},
            )
            opener = FakeOpener(response)

            with self.subTest(status=status):
                with patch("flushot.build_opener", return_value=opener):
                    with patch(
                        "flushot.validate_fetch_url",
                        wraps=flushot.validate_fetch_url,
                    ) as validate_url:
                        with self.assertRaisesRegex(
                            ValueError,
                            r"^CDC response status must be 200\.$",
                        ):
                            flushot.fetch_html(max_bytes=40)
                self.assertEqual(0, response.read_calls)
                validate_url.assert_called_once_with(flushot.CDC_FLU_URL)

    def test_validate_response_content_type_accepts_utf8_html(self):
        for content_type in (
            "text/html",
            "text/html; charset=UTF-8",
            "text/html; charset=utf8",
            "TEXT/HTML; Charset=UTF-8",
            "text/html; charset*=utf-8''utf-8",
        ):
            with self.subTest(content_type=content_type):
                flushot.validate_html_content_type({"Content-Type": content_type})

    def test_validate_response_content_type_rejects_missing_or_incompatible_values(self):
        rejected = (
            ({}, "declare an HTML Content-Type"),
            ({"Content-Type": "application/json"}, "must be text/html"),
            ({"Content-Type": "text/html; charset=iso-8859-1"}, "must use UTF-8"),
        )

        for headers, message in rejected:
            with self.subTest(headers=headers):
                with self.assertRaisesRegex(ValueError, message):
                    flushot.validate_html_content_type(headers)

    def test_validate_response_content_type_rejects_duplicate_charset_parameters(
        self,
    ):
        for content_type in (
            "text/html; charset=utf-8; charset=utf-8",
            "text/html; charset=utf-8; charset=iso-8859-1",
            "text/html; CHARSET=utf8; charset=UTF-8",
            "text/html; charset*=utf-8''utf-8; charset=utf-8",
        ):
            with self.subTest(content_type=content_type):
                with self.assertRaisesRegex(
                    ValueError,
                    r"^CDC response Content-Type must declare at most one charset parameter\.$",
                ):
                    flushot.validate_html_content_type({"Content-Type": content_type})

    def test_fetch_html_rejects_duplicate_charset_before_reading_body(self):
        response = FakeResponse(
            body=b"private response",
            headers={
                "Content-Type": "text/html; charset=utf-8; charset=iso-8859-1"
            },
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(
                ValueError,
                r"^CDC response Content-Type must declare at most one charset parameter\.$",
            ):
                flushot.fetch_html(max_bytes=40)

        self.assertEqual(0, response.read_calls)

    def test_fetch_html_rejects_content_type_before_reading_body(self):
        response = FakeResponse(
            body=b'{"not": "html"}',
            headers={"Content-Type": "application/json"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "must be text/html"):
                flushot.fetch_html(max_bytes=20)

        self.assertEqual(0, response.read_calls)

    def test_fetch_html_rejects_duplicate_content_type_before_reading_body(self):
        for second_content_type in (
            "text/html; charset=utf-8",
            "application/json",
        ):
            headers = Message()
            headers["Content-Type"] = "text/html; charset=utf-8"
            headers["Content-Type"] = second_content_type
            response = FakeResponse(body=b"private response", headers=headers)
            opener = FakeOpener(response)

            with self.subTest(second_content_type=second_content_type):
                with patch("flushot.build_opener", return_value=opener):
                    with self.assertRaisesRegex(
                        ValueError,
                        r"^CDC response must declare exactly one Content-Type\.$",
                    ):
                        flushot.fetch_html(max_bytes=40)
                self.assertEqual(0, response.read_calls)

    def test_fetch_html_uses_validated_bounded_response(self):
        response = FakeResponse(
            body=b"<html>ok</html>",
            headers={
                "Content-Length": "15",
                "Content-Type": "text/html; charset=utf-8",
            },
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            html = flushot.fetch_html(timeout="45", max_bytes=20)

        self.assertEqual("<html>ok</html>", html)
        self.assertEqual(45, opener.timeout)
        self.assertEqual(flushot.CDC_FLU_URL, opener.request.full_url)

    def test_fetch_html_accepts_absent_or_identity_content_encoding(self):
        for content_encoding in (None, "identity", " IDENTITY "):
            headers = {"Content-Type": "text/html; charset=utf-8"}
            if content_encoding is not None:
                headers["Content-Encoding"] = content_encoding
            response = FakeResponse(body=b"<html>ok</html>", headers=headers)
            opener = FakeOpener(response)

            with self.subTest(content_encoding=content_encoding):
                with patch("flushot.build_opener", return_value=opener):
                    self.assertEqual(
                        "<html>ok</html>",
                        flushot.fetch_html(max_bytes=20),
                    )
                self.assertGreater(response.read_calls, 0)

    def test_fetch_html_rejects_unsupported_content_encoding_before_reading_body(self):
        for content_encoding in ("", "gzip", "deflate", "br", "identity, gzip"):
            response = FakeResponse(
                body=b"encoded private response",
                headers={
                    "Content-Type": "text/html; charset=utf-8",
                    "Content-Encoding": content_encoding,
                },
            )
            opener = FakeOpener(response)

            with self.subTest(content_encoding=content_encoding):
                with patch("flushot.build_opener", return_value=opener):
                    with self.assertRaisesRegex(
                        ValueError,
                        r"^CDC response Content-Encoding must be identity\.$",
                    ):
                        flushot.fetch_html(max_bytes=40)
                self.assertEqual(0, response.read_calls)

        duplicate_headers = Message()
        duplicate_headers["Content-Type"] = "text/html; charset=utf-8"
        duplicate_headers["Content-Encoding"] = "identity"
        duplicate_headers["Content-Encoding"] = "gzip"
        response = FakeResponse(
            body=b"encoded private response",
            headers=duplicate_headers,
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(
                ValueError,
                r"^CDC response Content-Encoding must be identity\.$",
            ):
                flushot.fetch_html(max_bytes=40)
        self.assertEqual(0, response.read_calls)

    def test_fetch_html_preserves_valid_multibyte_utf8(self):
        expected = "<html>caf\u00e9</html>"
        response = FakeResponse(
            body=expected.encode("utf-8"),
            headers={"Content-Type": "text/html; charset=utf-8"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            html = flushot.fetch_html(max_bytes=30)

        self.assertEqual(expected, html)

    def test_fetch_html_rejects_malformed_utf8_without_leaking_body(self):
        response = FakeResponse(
            body=b"<html>private-\xff-value</html>",
            headers={"Content-Type": "text/html; charset=utf-8"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with patch(
                "flushot.read_response_bytes",
                wraps=flushot.read_response_bytes,
            ) as bounded_read:
                with self.assertRaisesRegex(
                    ValueError,
                    r"^CDC response body must be valid UTF-8\.$",
                ) as error:
                    flushot.fetch_html(max_bytes=40)

        bounded_read.assert_called_once_with(response, 40)
        self.assertNotIn("private", str(error.exception))
        self.assertIsNone(error.exception.__cause__)

    def test_fetch_html_rejects_untrusted_final_url(self):
        response = FakeResponse(body=b"ignored", url="https://example.com/private")
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "cdc.gov"):
                flushot.fetch_html(max_bytes=20)


if __name__ == "__main__":
    unittest.main()
