from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("sync-discord-sprays.py")
SPEC = importlib.util.spec_from_file_location("sync_discord_sprays", SCRIPT)
assert SPEC and SPEC.loader
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


def attachment(attachment_id: str = "500", filename: str = "preview.png") -> dict:
    return {
        "id": attachment_id,
        "filename": filename,
        "content_type": "image/png",
        "width": 800,
        "height": 600,
        "url": "https://cdn.example/preview.png",
    }


class SpraySyncTests(unittest.TestCase):
    def test_parse_name_accepts_plain_text_and_code_blocks(self) -> None:
        self.assertEqual(sync.parse_spray_name("cool_spray / token 30"), "cool_spray")
        self.assertEqual(sync.parse_spray_name("```\nSpray: neon_cat\ncredit: user\n```"), "neon_cat")
        self.assertIsNone(sync.parse_spray_name("================"))
        self.assertIsNone(sync.parse_spray_name("credit: user"))

    def test_pairs_media_in_same_or_following_message(self) -> None:
        messages = [
            {"id": "100", "content": "first", "attachments": [attachment("501")]},
            {"id": "200", "content": "second", "attachments": []},
            {"id": "201", "content": "", "attachments": [attachment("502")]},
        ]
        records, warnings = sync.pair_spray_messages(messages)
        self.assertEqual(warnings, [])
        self.assertEqual([record["name"] for record in records], ["first", "second"])
        self.assertEqual(records[1]["media_message_id"], "201")

    def test_warns_instead_of_guessing_between_multiple_media(self) -> None:
        messages = [{
            "id": "100",
            "content": "ambiguous",
            "attachments": [attachment("501"), attachment("502")],
        }]
        records, warnings = sync.pair_spray_messages(messages)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(warnings), 1)

    def test_adds_a_new_spray_and_reuses_it_by_source_message(self) -> None:
        record = {
            "name": "new_spray",
            "name_message_id": "100",
            "media_message_id": "100",
            "timestamp": "2026-07-21T01:00:00+00:00",
            "edited_timestamp": "",
            "image_timestamp": "2026-07-21T01:00:00+00:00",
            "media": attachment(),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_dir = Path(temp_dir) / "spray"

            def fake_convert(_data: bytes, destination: Path, _max_width: int) -> tuple[int, int]:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"webp")
                return 640, 480

            with patch.object(sync.common, "download_attachment", return_value=b"image"), patch.object(
                sync.common, "convert_image", side_effect=fake_convert
            ):
                catalog, state, catalog_changes, asset_changes = sync.synchronize(
                    [record],
                    {"version": 5, "category": "spray", "updatedAt": "2026-07-21", "items": []},
                    {"version": 1, "threadId": "20", "items": {}},
                    "10",
                    "20",
                    asset_dir,
                )

            self.assertEqual(catalog_changes, 1)
            self.assertEqual(asset_changes, 1)
            self.assertEqual(catalog["items"][0]["id"], "spray-001")
            self.assertEqual(catalog["items"][0]["media"][0]["role"], "preview")
            self.assertEqual(state["items"]["100"]["sprayId"], "spray-001")


if __name__ == "__main__":
    unittest.main()
