from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def iter_files(root: Path) -> list[Path]:
    return sorted((path for path in root.rglob("*") if path.is_file()), key=lambda item: str(item).lower())


def build_inventory(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in iter_files(root):
        relative = path.relative_to(root).as_posix()
        rows.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256(path),
                "suffix": path.suffix.lower(),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "size", "sha256", "suffix"])
        writer.writeheader()
        writer.writerows(rows)


def write_sha256(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{row['sha256']}  {row['path']}" for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sbom(path: Path, root: Path, rows: list[dict[str, object]]) -> None:
    payload = {
        "format": "movaura-simple-sbom-v1",
        "root": str(root),
        "file_count": len(rows),
        "total_size": sum(int(row["size"]) for row in rows),
        "files": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Movaura artifact inventory, hashes and simple SBOM.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--name", required=True, choices=("standalone", "msix"))
    parser.add_argument("--reports", type=Path, default=Path("release/reports"))
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"artifact root not found: {root}")

    rows = build_inventory(root)
    write_csv(args.reports / f"{args.name}-file-inventory.csv", rows)
    (args.reports / f"{args.name}-file-inventory.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_sha256(args.reports / f"{args.name}-sha256.txt", rows)
    write_sbom(args.reports / f"{args.name}-sbom.json", root, rows)
    print(f"{args.name}_file_count={len(rows)}")
    print(f"{args.name}_total_size={sum(int(row['size']) for row in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
