import argparse
import json
import os
import sys
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi


def _get_username(api: KaggleApi) -> str:
    user = os.getenv("KAGGLE_USERNAME")
    if user:
        return user
    # Try Kaggle API internal config
    try:
        cfg = getattr(api, "config_values", {}) or {}
        user = cfg.get("username")
        if user:
            return user
    except Exception:
        pass
    # Fallback to reading config file
    cfg_path = Path.home() / ".kaggle" / "kaggle.json"
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            user = data.get("username")
            if user:
                return user
    except Exception:
        pass
    return "unknown"


def _slugify(value: str) -> str:
    out = []
    value = value.strip().lower().replace(" ", "-")
    for ch in value:
        if ch.isalnum() or ch in ("-", "_"):
            out.append(ch)
    # prevent empty
    return "".join(out) or "dataset"


def create_or_version(api: KaggleApi, folder: Path, notes: str = "auto upload") -> None:
    meta_path = folder / "dataset-metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing dataset-metadata.json in {folder}")
    # Handle potential BOM from Windows tools
    with open(meta_path, "r", encoding="utf-8-sig") as f:
        meta = json.load(f)
    ds_id = meta.get("id")
    if not ds_id:
        raise ValueError(f"Metadata missing 'id' in {meta_path}")
    # Ensure id is owner/slug
    if "/" not in ds_id:
        owner = _get_username(api)
        slug = _slugify(ds_id)
        ds_id = f"{owner}/{slug}"
        meta["id"] = ds_id
    # Re-write metadata without BOM and with normalized id
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    # Try create; if it exists, version instead
    try:
        api.dataset_create_new(folder=str(folder), convert_to_csv=False, dir_mode="zip")
        print(f"Created dataset: {ds_id}")
    except Exception as e:
        msg = str(e)
        if "Conflict" in msg or "already exists" in msg or "409" in msg:
            api.dataset_create_version(folder=str(folder), version_notes=notes, convert_to_csv=False, dir_mode="zip")
            print(f"Updated dataset: {ds_id}")
        else:
            raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="kaggle_datasets", help="Root directory with dataset subfolders")
    args = parser.parse_args()

    api = KaggleApi()
    api.authenticate()

    root = Path(args.root)
    if not root.exists():
        print(f"No such directory: {root}", file=sys.stderr)
        sys.exit(1)

    for sub in sorted(root.iterdir()):
        if not sub.is_dir():
            continue
        if not (sub / "dataset-metadata.json").exists():
            continue
        create_or_version(api, sub)


if __name__ == "__main__":
    main()


