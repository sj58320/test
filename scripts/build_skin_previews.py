"""Build the complete skin preview catalog for GitHub Pages."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "assets" / "skins"
CATALOG_VERSION = 5
CATALOG_DIR = ROOT / "data" / "skins"
CATALOG_FILES = {
    "human": CATALOG_DIR / "human.json",
    "zombie": CATALOG_DIR / "zombie.json",
    "weapon": CATALOG_DIR / "weapon.json",
}
BUILD_VERSION = "skin-catalog-v2-webp-q82-max800-1280"
BUILD_VERSION_FILE = OUTPUT_DIR / ".build-version"
GENERATED_MANIFEST_FILE = OUTPUT_DIR / ".generated-manifest.json"
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov"}
ANIMATED_IMAGE_SUFFIXES = {".gif"}
OPTIONAL_ITEM_FIELDS = {"subcategory", "weaponType", "nameKo", "sourceUrl"}

CHARACTER_SOURCES = [
    {
        "category": "human",
        "root": "Human_Skin_List_Extract",
        "json": "skins.json",
        "output": "",
        "id_prefix": "",
    },
    {
        "category": "zombie",
        "root": "Zombie_Skin_List_Extract",
        "json": "skins.json",
        "output": "zombie",
        "id_prefix": "zombie-",
    },
]

WEAPON_SOURCES = [
    ("primary", "Primary_Weapon_Skin_List_Extract"),
    ("secondary", "Secondary_Weapon_Skin_List_Extract"),
    ("melee", "Knife_Skin_List_Extract"),
    ("throwable", "Throwing_Weapon_Skin_List_Extract"),
]

PRIMARY_WEAPON_TYPES = [
    ("smg", ("mp5", "mp7", "mp9", "p90", "ump", "bizon", "mac10")),
    ("rifle", ("ak47", "m4a1", "m4a4", "famas", "aug", "galil")),
    ("shotgun", ("xm1014", "sawedoff")),
    ("machinegun", ("m249", "mg42", "mg3", "negev")),
    ("sniper", ("awp", "m200")),
]


def classify_primary_weapon(name: str) -> str:
    normalized = name.casefold().replace("-", "").replace("_", "").replace(" ", "")
    for weapon_type, aliases in PRIMARY_WEAPON_TYPES:
        if any(alias in normalized for alias in aliases):
            return weapon_type
    return "other"


def find_source_dir(root_name: str, json_name: str) -> Path:
    root = ROOT / root_name
    direct = root / json_name
    if direct.exists():
        return root
    matches = sorted(root.rglob(json_name))
    if not matches:
        raise FileNotFoundError(f"{json_name} was not found under {root}")
    return matches[0].parent


def read_items(source_dir: Path, json_name: str) -> list[dict[str, Any]]:
    data = json.loads((source_dir / json_name).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{source_dir / json_name} must contain a JSON array")
    return data


def convert_image(
    source: Path, destination: Path, max_width: int, force: bool = False
) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if (
        not force
        and destination.exists()
        and destination.stat().st_mtime >= source.stat().st_mtime
    ):
        with Image.open(destination) as image:
            return image.size

    with Image.open(source) as image:
        has_alpha = image.mode in {"RGBA", "LA"} or (
            image.mode == "P" and "transparency" in image.info
        )
        image = image.convert("RGBA" if has_alpha else "RGB")
        if image.width > max_width:
            height = round(image.height * max_width / image.width)
            image = image.resize((max_width, height), Image.Resampling.LANCZOS)
        image.save(destination, "WEBP", quality=82, method=4)
        return image.size


def copy_media(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if (
        destination.exists()
        and destination.stat().st_size == source.stat().st_size
        and destination.stat().st_mtime >= source.stat().st_mtime
    ):
        return
    shutil.copy2(source, destination)


def relative_output(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalize_skin_item(item: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical catalog form used by Pages CMS."""
    normalized = dict(item)
    for field in OPTIONAL_ITEM_FIELDS:
        value = normalized.get(field)
        if value is None or value == "":
            normalized.pop(field, None)
    return normalized


def load_existing_catalog(category: str, path: Path | None = None) -> dict[str, Any]:
    path = path or CATALOG_FILES[category]
    if not path.exists():
        return {
            "version": CATALOG_VERSION,
            "category": category,
            "updatedAt": "",
            "items": [],
        }
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("items"), list):
        raise ValueError(f"{path} must contain an object with an items array")
    if catalog.get("category") != category:
        raise ValueError(f"{path} must have category {category!r}")
    items: list[dict[str, Any]] = []
    for source_item in catalog["items"]:
        if not isinstance(source_item, dict):
            raise ValueError(f"{path} items must be objects")
        item = dict(source_item)
        item_category = item.get("category", category)
        if item_category != category:
            raise ValueError(
                f"{path} contains {item.get('id', '<unknown>')} in category "
                f"{item_category!r}"
            )
        item["category"] = category
        items.append(item)
    return {**catalog, "items": items}


def build_category_catalog(
    category: str,
    items: list[dict[str, Any]],
    updated_at: str,
) -> dict[str, Any]:
    stored_items: list[dict[str, Any]] = []
    for item in items:
        if item.get("category") != category:
            continue
        stored_item = normalize_skin_item(item)
        stored_item.pop("category", None)
        stored_items.append(stored_item)
    return {
        "version": CATALOG_VERSION,
        "category": category,
        "updatedAt": updated_at,
        "items": stored_items,
    }


def require_item_id(item: dict[str, Any]) -> str:
    item_id = item.get("id")
    if not isinstance(item_id, str) or not item_id.strip():
        raise ValueError("Every skin catalog item must have a non-empty id")
    return item_id


def merge_catalog_items(
    existing_items: list[dict[str, Any]],
    generated_items: list[dict[str, Any]],
    overwrite_existing: bool = False,
) -> list[dict[str, Any]]:
    """Preserve CMS entries by default and append newly imported source IDs."""
    generated_by_id: dict[str, dict[str, Any]] = {}
    generated_order: list[str] = []
    for item in generated_items:
        item_id = require_item_id(item)
        if item_id in generated_by_id:
            raise ValueError(f"Generated skin id is duplicated: {item_id}")
        generated_by_id[item_id] = item
        generated_order.append(item_id)

    merged: list[dict[str, Any]] = []
    seen_existing: set[str] = set()
    for item in existing_items:
        item_id = require_item_id(item)
        if item_id in seen_existing:
            raise ValueError(f"Existing skin id is duplicated: {item_id}")
        seen_existing.add(item_id)
        generated_item = generated_by_id.pop(item_id, None)
        selected = (
            generated_item
            if overwrite_existing and generated_item is not None
            else item
        )
        merged.append(normalize_skin_item(selected))

    for item_id in generated_order:
        item = generated_by_id.get(item_id)
        if item is not None:
            merged.append(normalize_skin_item(item))
    return merged


def catalog_media_paths(items: list[dict[str, Any]]) -> set[str]:
    prefix = "assets/skins/"
    paths: set[str] = set()
    for item in items:
        for media in item.get("media", []):
            if not isinstance(media, dict):
                continue
            source = media.get("src")
            if isinstance(source, str) and source.startswith(prefix):
                relative = source[len(prefix) :]
                if relative:
                    paths.add(relative)
    return paths


def load_generated_manifest(
    path: Path = GENERATED_MANIFEST_FILE,
) -> tuple[set[str], set[str]]:
    if not path.exists():
        return set(), set()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    files = manifest.get("files") if isinstance(manifest, dict) else None
    item_ids = manifest.get("itemIds", []) if isinstance(manifest, dict) else None
    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        raise ValueError(f"{path} must contain a files string array")
    if not isinstance(item_ids, list) or not all(
        isinstance(item, str) for item in item_ids
    ):
        raise ValueError(f"{path} must contain an itemIds string array")
    return set(files), set(item_ids)


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def write_generated_manifest(files: set[str], item_ids: set[str]) -> None:
    payload = {
        "version": 1,
        "files": sorted(files),
        "itemIds": sorted(item_ids),
    }
    atomic_write_text(
        GENERATED_MANIFEST_FILE,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def build_character_items(
    config: dict[str, str], force_rebuild: bool, skip_ids: set[str] | None = None
) -> tuple[list[dict[str, Any]], set[str], list[str]]:
    category = config["category"]
    source_dir = find_source_dir(config["root"], config["json"])
    source_items = read_items(source_dir, config["json"])
    output_subdir = Path(config["output"]) if config["output"] else Path()
    generated: set[str] = set()
    timestamps: list[str] = []
    output_items: list[dict[str, Any]] = []

    for item in source_items:
        order = int(item["order"])
        item_id = f"{config['id_prefix']}{order:03d}"
        if skip_ids and item_id in skip_ids:
            continue
        media = []
        for role, file_key, max_width in [
            ("thirdPerson", "third_person_file", 800),
            ("firstPerson", "first_person_file", 1280),
        ]:
            filename = f"{order:03d}-{'third' if role == 'thirdPerson' else 'first'}.webp"
            destination = OUTPUT_DIR / output_subdir / filename
            size = convert_image(
                source_dir / item[file_key], destination, max_width, force_rebuild
            )
            generated.add(destination.relative_to(OUTPUT_DIR).as_posix())
            media.append(
                {
                    "type": "image",
                    "role": role,
                    "src": relative_output(destination),
                    "width": size[0],
                    "height": size[1],
                }
            )

        timestamp = item.get("timestamp", "")
        if timestamp:
            timestamps.append(timestamp)
        output_items.append(
            {
                "id": item_id,
                "category": category,
                "subcategory": None,
                "order": order,
                "name": item["skin_name"],
                "nameKo": item.get("skin_name_ko", ""),
                "media": media,
                "sourceUrl": item.get("message_url", ""),
            }
        )

    return output_items, generated, timestamps


def build_weapon_items(
    subcategory: str,
    root_name: str,
    force_rebuild: bool,
    skip_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], set[str], list[str]]:
    source_dir = find_source_dir(root_name, "items.json")
    source_items = read_items(source_dir, "items.json")
    generated: set[str] = set()
    timestamps: list[str] = []
    output_items: list[dict[str, Any]] = []

    for item in source_items:
        order = int(item["order"])
        item_id = f"weapon-{subcategory}-{order:03d}"
        if skip_ids and item_id in skip_ids:
            continue
        source_media = item.get("media_files", [])
        metadata = item.get("media", [])
        media = []
        for media_index, relative_source in enumerate(source_media, start=1):
            source = source_dir / relative_source
            suffix = source.suffix.lower()
            metadata_item = metadata[media_index - 1] if media_index <= len(metadata) else {}
            output_base = OUTPUT_DIR / "weapon" / subcategory / f"{order:03d}-{media_index:02d}"

            if suffix in VIDEO_SUFFIXES:
                destination = output_base.with_suffix(suffix)
                copy_media(source, destination)
                media_type = "video"
                width = int(metadata_item.get("width") or 1920)
                height = int(metadata_item.get("height") or 1080)
            elif suffix in ANIMATED_IMAGE_SUFFIXES:
                destination = output_base.with_suffix(suffix)
                copy_media(source, destination)
                media_type = "image"
                width = int(metadata_item.get("width") or 800)
                height = int(metadata_item.get("height") or 800)
            else:
                destination = output_base.with_suffix(".webp")
                width, height = convert_image(
                    source, destination, 1280, force_rebuild
                )
                media_type = "image"

            generated.add(destination.relative_to(OUTPUT_DIR).as_posix())
            media.append(
                {
                    "type": media_type,
                    "role": "preview",
                    "src": relative_output(destination),
                    "width": width,
                    "height": height,
                }
            )

        if not media:
            raise ValueError(f"{item.get('item_name', order)} has no preview media")

        timestamp = item.get("timestamp", "")
        if timestamp:
            timestamps.append(timestamp)
        output_items.append(
            {
                "id": item_id,
                "category": "weapon",
                "subcategory": subcategory,
                "weaponType": (
                    classify_primary_weapon(item["item_name"])
                    if subcategory == "primary"
                    else None
                ),
                "order": order,
                "name": item["item_name"],
                "nameKo": "",
                "media": media,
                "sourceUrl": item.get("message_url", ""),
            }
        )

    return output_items, generated, timestamps


def remove_stale_media(
    previously_owned: set[str],
    currently_owned: set[str],
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Delete only files recorded as generator-owned by the prior manifest."""
    managed_suffixes = {".webp", ".gif", *VIDEO_SUFFIXES}
    output_root = output_dir.resolve()
    for relative in sorted(previously_owned - currently_owned):
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"Unsafe generated manifest path: {relative}")
        old_file = (output_dir / Path(*relative_path.parts)).resolve()
        if output_root != old_file and output_root not in old_file.parents:
            raise ValueError(f"Generated manifest path escapes assets/skins: {relative}")
        if not old_file.is_file():
            continue
        if old_file.suffix.lower() in managed_suffixes:
            old_file.unlink()
    for directory in sorted(
        (path for path in output_dir.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        if not any(directory.iterdir()):
            directory.rmdir()


def main(overwrite_existing: bool = False) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    existing_catalogs = {
        category: load_existing_catalog(category)
        for category in CATALOG_FILES
    }
    existing_items = [
        item
        for category in CATALOG_FILES
        for item in existing_catalogs[category]["items"]
    ]
    existing_ids = {require_item_id(item) for item in existing_items}
    previously_owned, known_source_ids = load_generated_manifest()
    skip_ids = (
        set() if overwrite_existing else existing_ids | known_source_ids
    )
    previous_version = (
        BUILD_VERSION_FILE.read_text(encoding="utf-8").strip()
        if BUILD_VERSION_FILE.exists()
        else ""
    )
    force_rebuild = previous_version != BUILD_VERSION

    all_items: list[dict[str, Any]] = []
    generated: set[str] = set()
    timestamps: dict[str, list[str]] = {
        category: [] for category in CATALOG_FILES
    }

    for config in CHARACTER_SOURCES:
        items, files, item_timestamps = build_character_items(
            config, force_rebuild, skip_ids
        )
        all_items.extend(items)
        generated.update(files)
        timestamps[config["category"]].extend(item_timestamps)

    for subcategory, root_name in WEAPON_SOURCES:
        items, files, item_timestamps = build_weapon_items(
            subcategory, root_name, force_rebuild, skip_ids
        )
        all_items.extend(items)
        generated.update(files)
        timestamps["weapon"].extend(item_timestamps)

    all_items = merge_catalog_items(
        existing_items, all_items, overwrite_existing=overwrite_existing
    )
    catalog_item_ids = {require_item_id(item) for item in all_items}
    currently_known_source_ids = (
        known_source_ids | existing_ids | catalog_item_ids
    )
    referenced_media = catalog_media_paths(all_items)
    currently_owned = (previously_owned & referenced_media) | (
        generated & referenced_media
    )
    for category, path in CATALOG_FILES.items():
        updated_candidates = [
            value
            for value in [
                existing_catalogs[category].get("updatedAt"),
                *timestamps[category],
            ]
            if isinstance(value, str) and value
        ]
        payload = build_category_catalog(
            category,
            all_items,
            max(updated_candidates, default=""),
        )
        atomic_write_text(
            path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        )
    remove_stale_media(previously_owned, currently_owned)
    write_generated_manifest(currently_owned, currently_known_source_ids)
    atomic_write_text(BUILD_VERSION_FILE, BUILD_VERSION + "\n")
    print(
        f"Built a catalog with {len(all_items)} skins; imported or refreshed "
        f"{len(generated)} media files ({len(currently_owned)} generator-owned)."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help=(
            "replace source-backed existing catalog items and their media; "
            "without this flag Pages CMS edits are preserved"
        ),
    )
    args = parser.parse_args()
    main(overwrite_existing=args.overwrite_existing)
