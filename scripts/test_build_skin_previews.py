from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_skin_previews as builder


def media(source: str) -> list[dict[str, object]]:
    return [
        {
            "type": "image",
            "role": "preview",
            "src": source,
            "width": 800,
            "height": 800,
        }
    ]


class SkinCatalogMergeTests(unittest.TestCase):
    def test_normalize_omits_empty_optional_fields(self) -> None:
        normalized = builder.normalize_skin_item(
            {
                "id": "001",
                "category": "human",
                "subcategory": None,
                "weaponType": None,
                "order": 1,
                "name": "Example",
                "nameKo": "",
                "sourceUrl": "",
                "media": media("assets/skins/example.webp"),
            }
        )

        self.assertNotIn("subcategory", normalized)
        self.assertNotIn("weaponType", normalized)
        self.assertNotIn("nameKo", normalized)
        self.assertNotIn("sourceUrl", normalized)

    def test_category_catalog_load_and_storage_normalize_category(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "human.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 5,
                        "category": "human",
                        "updatedAt": "2026-07-17T12:28:00Z",
                        "items": [
                            {
                                "id": "001",
                                "order": 1,
                                "name": "Example",
                                "nameKo": "",
                                "media": media("assets/skins/example.webp"),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            catalog = builder.load_existing_catalog("human", path)
            payload = builder.build_category_catalog(
                "human", catalog["items"], catalog["updatedAt"]
            )

            self.assertEqual(catalog["items"][0]["category"], "human")
            self.assertEqual(payload["category"], "human")
            self.assertNotIn("category", payload["items"][0])
            self.assertNotIn("nameKo", payload["items"][0])

    def test_default_merge_preserves_cms_edits_and_media(self) -> None:
        existing = [
            {
                "id": "001",
                "category": "human",
                "order": 7,
                "name": "CMS name",
                "nameKo": "",
                "media": media("assets/skins/cms-upload.webp"),
            },
            {
                "id": "cms-only",
                "category": "zombie",
                "order": 99,
                "name": "CMS only",
                "media": media("assets/skins/cms-only.webp"),
            },
        ]
        generated = [
            {
                "id": "001",
                "category": "human",
                "subcategory": None,
                "order": 1,
                "name": "Source name",
                "nameKo": "",
                "media": media("assets/skins/001.webp"),
            },
            {
                "id": "002",
                "category": "human",
                "subcategory": None,
                "order": 2,
                "name": "New source item",
                "nameKo": "",
                "media": media("assets/skins/002.webp"),
            },
        ]

        merged = builder.merge_catalog_items(existing, generated)

        self.assertEqual([item["id"] for item in merged], ["001", "cms-only", "002"])
        self.assertEqual(merged[0]["name"], "CMS name")
        self.assertEqual(merged[0]["order"], 7)
        self.assertEqual(merged[0]["media"], media("assets/skins/cms-upload.webp"))
        self.assertNotIn("nameKo", merged[0])
        self.assertEqual(merged[1]["name"], "CMS only")
        self.assertNotIn("subcategory", merged[2])
        self.assertNotIn("nameKo", merged[2])

    def test_overwrite_flag_replaces_source_backed_item(self) -> None:
        existing = [
            {
                "id": "001",
                "category": "human",
                "order": 7,
                "name": "CMS name",
                "media": media("assets/skins/cms-upload.webp"),
            }
        ]
        generated = [
            {
                "id": "001",
                "category": "human",
                "order": 1,
                "name": "Source name",
                "media": media("assets/skins/001.webp"),
            }
        ]

        merged = builder.merge_catalog_items(
            existing, generated, overwrite_existing=True
        )

        self.assertEqual(merged[0]["name"], "Source name")
        self.assertEqual(merged[0]["media"], media("assets/skins/001.webp"))


class GeneratedMediaCleanupTests(unittest.TestCase):
    def test_manifest_loads_owned_files_and_known_item_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_text(
                '{"version":1,"files":["generated/a.webp"],'
                '"itemIds":["001","weapon-primary-001"]}',
                encoding="utf-8",
            )

            files, item_ids = builder.load_generated_manifest(manifest)

            self.assertEqual(files, {"generated/a.webp"})
            self.assertEqual(item_ids, {"001", "weapon-primary-001"})

    def test_cleanup_only_deletes_previously_owned_stale_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            stale = output_dir / "generated" / "stale.webp"
            current = output_dir / "generated" / "current.webp"
            cms_upload = output_dir / "cms-upload.webp"
            for path in (stale, current, cms_upload):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"test")

            builder.remove_stale_media(
                {"generated/stale.webp", "generated/current.webp"},
                {"generated/current.webp"},
                output_dir,
            )

            self.assertFalse(stale.exists())
            self.assertTrue(current.exists())
            self.assertTrue(cms_upload.exists())

    def test_cleanup_rejects_manifest_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                builder.remove_stale_media({"../outside.webp"}, set(), Path(temporary))


if __name__ == "__main__":
    unittest.main()
