from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "handoff_bundle.py"
SPEC = importlib.util.spec_from_file_location("handoff_bundle", SCRIPT)
handoff = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(handoff)


class HandoffBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="conversation-handoff-tests-")
        self.base = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def messages() -> list[dict]:
        return [
            {"sequence": 1, "timestamp": "2026-10-24T01:00:00Z", "role": "user", "phase": None,
             "content": [{"type": "text", "text": "Please preserve this decision exactly."}]},
            {"sequence": 2, "timestamp": "2026-10-24T01:01:00Z", "role": "assistant", "phase": "final_answer",
             "content": [{"type": "text", "text": "Recorded with evidence sequence 1."}]},
        ]

    @staticmethod
    def metadata() -> dict:
        return {
            "source_type": "supplied-jsonl",
            "coverage": "complete-supplied-jsonl",
            "conversation_id": "fake-conversation",
            "conversation_title": "Synthetic test",
            "source_log_sha256": "0" * 64,
            "source_log_bytes": 100,
        }

    @staticmethod
    def complete_detailed(path: Path) -> None:
        lines = ["# Detailed Conversation Handoff", ""]
        for heading in handoff.REQUIRED_HEADINGS:
            lines.extend((f"## {heading}", "", f"Synthetic verified content for {heading}, supported by sequence 1.", ""))
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    def prepare(self, name: str = "handoff") -> Path:
        output = self.base / name
        handoff.prepare_bundle(output, self.messages(), self.metadata(), {
            "developer_or_system_messages": 0,
            "reasoning_and_tool_records": 0,
            "injected_runtime_context": 0,
        })
        return output

    def test_round_trip_finalize_verify_and_extract(self) -> None:
        output = self.prepare()
        self.complete_detailed(output / "DETAILED_HANDOFF.md")
        archive = handoff.finalize(output)

        zip_result = handoff.verify_zip(archive, None, handoff.DEFAULT_MAX_UNCOMPRESSED_BYTES)
        directory_result = handoff.verify_directory(output)
        extracted = self.base / "extracted"
        extract_result = handoff.verify_zip(archive, extracted, handoff.DEFAULT_MAX_UNCOMPRESSED_BYTES)

        self.assertEqual(zip_result["status"], "verified")
        self.assertEqual(directory_result["message_count"], 2)
        self.assertEqual(extract_result["extracted_to"], str(extracted.resolve()))
        self.assertTrue((extracted / "FULL_TRANSCRIPT.jsonl").is_file())

    def test_secret_blocks_preparation_without_output(self) -> None:
        messages = self.messages()
        messages[0]["content"][0]["text"] = "access_token=abcdefghijklmnopqrstuvwxyz123456"
        output = self.base / "secret"
        with self.assertRaisesRegex(ValueError, "Potential credentials"):
            handoff.prepare_bundle(output, messages, self.metadata(), {})
        self.assertFalse(output.exists())

    def test_existing_output_is_not_overwritten(self) -> None:
        output = self.base / "existing"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            handoff.prepare_bundle(output, self.messages(), self.metadata(), {})
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_existing_zip_is_not_overwritten(self) -> None:
        output = self.prepare()
        self.complete_detailed(output / "DETAILED_HANDOFF.md")
        archive = output.with_suffix(".zip")
        archive.write_bytes(b"sentinel")
        with self.assertRaisesRegex(ValueError, "already exists"):
            handoff.finalize(output)
        self.assertEqual(archive.read_bytes(), b"sentinel")
        metadata = json.loads((output / "BUNDLE_METADATA.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "draft-needs-detailed-handoff")

    def test_publish_failure_rolls_back_directory(self) -> None:
        output = self.prepare()
        self.complete_detailed(output / "DETAILED_HANDOFF.md")
        with mock.patch.object(handoff.os, "link", side_effect=OSError("synthetic publish failure")):
            with self.assertRaisesRegex(OSError, "synthetic publish failure"):
                handoff.finalize(output)
        metadata = json.loads((output / "BUNDLE_METADATA.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "draft-needs-detailed-handoff")
        self.assertFalse((output / "BUNDLE_MANIFEST.json").exists())
        self.assertFalse(output.with_suffix(".zip").exists())

    def test_concurrent_finalize_has_one_winner_and_valid_output(self) -> None:
        output = self.prepare()
        self.complete_detailed(output / "DETAILED_HANDOFF.md")
        barrier = threading.Barrier(2)
        results: list[str] = []

        def worker() -> None:
            barrier.wait()
            try:
                handoff.finalize(output)
                results.append("ok")
            except (OSError, RuntimeError, ValueError):
                results.append("blocked")

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertCountEqual(results, ["ok", "blocked"])
        self.assertEqual(handoff.verify_zip(output.with_suffix(".zip"), None, handoff.DEFAULT_MAX_UNCOMPRESSED_BYTES)["status"], "verified")

    def test_unsafe_zip_names_and_windows_collisions_are_rejected(self) -> None:
        for name in ("../escape.txt", "folder\\..\\escape.txt", "/absolute.txt", "C:evil.txt", "NUL.txt", "trail. /x"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                handoff.safe_zip_name(name)
        archive = self.base / "collision.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("A.txt", b"one")
            bundle.writestr("a.txt", b"two")
        with self.assertRaisesRegex(ValueError, "Windows-colliding"):
            handoff.verify_zip(archive, None, 1000)

    def test_duplicate_manifest_paths_are_rejected(self) -> None:
        record = {"path": "same.txt", "size": 1, "sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            handoff.validate_manifest_files([record, dict(record)])

    def test_declared_image_mime_must_match_bytes(self) -> None:
        fake = base64.b64encode(b"this is not a png").decode("ascii")
        with self.assertRaisesRegex(ValueError, "do not match"):
            handoff.decode_data_url(f"data:image/png;base64,{fake}")
        with self.assertRaises(ValueError):
            handoff.decode_data_url("data:image/png;base64,%%%")

    def test_non_object_import_record_is_rejected_cleanly(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON object"):
            handoff.parse_imported_jsonl(b"[]\n")

    def test_git_repository_destination_is_rejected(self) -> None:
        repository = self.base / "repo"
        (repository / ".git").mkdir(parents=True)
        nested_parent = repository / "must-not-be-created"
        with self.assertRaisesRegex(ValueError, "Git repository"):
            handoff.validate_new_output_path(nested_parent / "handoff")
        self.assertFalse(nested_parent.exists())

    def test_symlink_destination_component_is_rejected_when_supported(self) -> None:
        real = self.base / "real"
        real.mkdir()
        link = self.base / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks are unavailable: {exc}")
        with self.assertRaisesRegex(ValueError, "symbolic link or junction"):
            handoff.validate_new_output_path(link / "handoff")

    def test_uncompressed_limit_is_enforced_before_manifest_read(self) -> None:
        archive = self.base / "large.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("BUNDLE_MANIFEST.json", b"{}")
            bundle.writestr("payload.bin", b"0123456789")
        with self.assertRaisesRegex(ValueError, "uncompressed-size limit"):
            handoff.verify_zip(archive, None, 5)


if __name__ == "__main__":
    unittest.main()
