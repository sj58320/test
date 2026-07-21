from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("sync-discord-weapon-skins.py")
SPEC = importlib.util.spec_from_file_location("sync_discord_weapon_skins", SCRIPT)
assert SPEC and SPEC.loader
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


THREAD_IDS = {
    "primary": "11",
    "secondary": "12",
    "melee": "13",
    "throwable": "14",
}
ALIASES = {"m4a1": "rifle", "mp9": "smg", "negev": "machinegun"}


def attachment(attachment_id: str, content_type: str = "image/png") -> dict:
    suffix = "mp4" if content_type.startswith("video/") else "png"
    return {
        "id": attachment_id,
        "filename": f"{attachment_id}.{suffix}",
        "content_type": content_type,
        "width": 1920,
        "height": 1080,
        "url": f"https://cdn.example/{attachment_id}.{suffix}",
    }


def record(name: str, message_id: str = "100", subcategory: str = "primary") -> dict:
    return {
        "subcategory": subcategory,
        "name": name,
        "name_message_id": message_id,
        "media_message_id": message_id,
        "timestamp": "2026-07-21T10:00:00+00:00",
        "edited_timestamp": "",
        "media_timestamp": "2026-07-21T10:00:00+00:00",
        "media": attachment("asset-" + message_id),
    }


class WeaponSkinSyncTests(unittest.TestCase):
    def test_plain_and_code_block_names_use_first_line_before_slash(self) -> None:
        self.assertEqual(sync.parse_weapon_name("chillet / token 30"), "chillet")
        self.assertEqual(
            sync.parse_weapon_name(
                "```\nhl_hyper_negev / Event\ncredit : 千音星璃\n```"
            ),
            "hl_hyper_negev",
        )
        self.assertIsNone(sync.parse_weapon_name("----------------"))

    def test_pairs_a_video_from_the_following_message(self) -> None:
        messages = [
            {
                "id": "100",
                "content": "```\ndatastream_huntsman\n```",
                "timestamp": "2026-07-21T10:00:00+00:00",
                "attachments": [],
            },
            {
                "id": "101",
                "content": "",
                "timestamp": "2026-07-21T10:00:01+00:00",
                "attachments": [attachment("video", "video/mp4")],
            },
        ]
        records, warnings = sync.pair_weapon_messages(messages, "melee")
        self.assertEqual(warnings, [])
        self.assertEqual(records[0]["name"], "datastream_huntsman")
        self.assertEqual(records[0]["media_message_id"], "101")
        self.assertEqual(sync.media_kind(records[0]["media"]), "video")

    def test_primary_classification_uses_only_final_parentheses(self) -> None:
        self.assertEqual(
            sync.classify_primary("custom_skin(m4a1)", ALIASES),
            ("rifle", "m4a1"),
        )
        self.assertIsNone(sync.classify_primary("custom_m4a1_skin", ALIASES))
        self.assertIsNone(sync.classify_primary("custom_skin(unknown)", ALIASES))

    def test_first_run_cleans_slash_metadata_without_replacing_media(self) -> None:
        catalog = {
            "version": 5,
            "category": "weapon",
            "updatedAt": "2026-07-20T00:00:00Z",
            "items": [
                {
                    "id": "weapon-primary-001",
                    "subcategory": "primary",
                    "weaponType": "machinegun",
                    "order": 1,
                    "name": "hl_hyper_negev / Event / sponsor: 千音星璃",
                    "media": [
                        {
                            "type": "video",
                            "role": "preview",
                            "src": "assets/skins/weapon/primary/001-01.mp4",
                            "width": 1920,
                            "height": 1080,
                        }
                    ],
                    "sourceUrl": "https://discord.com/channels/574/11/100",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            assets = Path(directory)
            (assets / "primary").mkdir()
            (assets / "primary" / "001-01.mp4").write_bytes(b"existing")
            with patch.object(sync, "write_media") as writer:
                result, state, catalog_changes, asset_changes = sync.synchronize(
                    [record("hl_hyper_negev")],
                    catalog,
                    {"items": {}},
                    ALIASES,
                    "574",
                    THREAD_IDS,
                    assets,
                )
            writer.assert_not_called()
        self.assertEqual(result["items"][0]["name"], "hl_hyper_negev")
        self.assertEqual(result["items"][0]["weaponType"], "machinegun")
        self.assertEqual(catalog_changes, 1)
        self.assertEqual(asset_changes, 0)
        self.assertEqual(state["items"]["100"]["skinId"], "weapon-primary-001")

    def test_rejects_a_new_primary_without_recognized_parentheses(self) -> None:
        catalog = {"version": 5, "category": "weapon", "items": []}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "final parentheses"):
                sync.synchronize(
                    [record("new_skin")],
                    catalog,
                    {"items": {}},
                    ALIASES,
                    "574",
                    THREAD_IDS,
                    Path(directory),
                )

    def test_adds_a_valid_new_primary(self) -> None:
        catalog = {"version": 5, "category": "weapon", "items": []}
        generated = {
            "type": "image",
            "role": "preview",
            "src": "assets/skins/weapon/primary/001-01.webp",
            "width": 1280,
            "height": 720,
        }
        with tempfile.TemporaryDirectory() as directory, patch.object(
            sync, "write_media", return_value=generated
        ):
            result, _, catalog_changes, asset_changes = sync.synchronize(
                [record("new_skin(mp9)")],
                catalog,
                {"items": {}},
                ALIASES,
                "574",
                THREAD_IDS,
                Path(directory),
            )
        item = result["items"][0]
        self.assertEqual(item["id"], "weapon-primary-001")
        self.assertEqual(item["weaponType"], "smg")
        self.assertEqual(catalog_changes, 1)
        self.assertEqual(asset_changes, 1)


if __name__ == "__main__":
    unittest.main()
