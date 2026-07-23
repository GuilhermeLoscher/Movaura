from __future__ import annotations

import argparse
import csv
import secrets
import string
from pathlib import Path


ALPHABET = "".join(ch for ch in string.ascii_uppercase + string.digits if ch not in "0O1I")


def make_key() -> str:
    groups = ["".join(secrets.choice(ALPHABET) for _ in range(4)) for _ in range(3)]
    return "MOVAURA-BETA-" + "-".join(groups)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerar chaves beta do Movaura.")
    parser.add_argument("--count", type=int, default=50, help="Quantidade de chaves.")
    parser.add_argument(
        "--output",
        default="release/beta/movaura_beta_keys.csv",
        help="CSV de saida para importar no Supabase.",
    )
    args = parser.parse_args()

    count = max(1, min(args.count, 10000))
    keys: set[str] = set()
    while len(keys) < count:
        keys.add(make_key())

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["key", "status", "notes"])
        writer.writeheader()
        for key in sorted(keys):
            writer.writerow({"key": key, "status": "available", "notes": "beta"})

    print(f"Chaves geradas: {len(keys)}")
    print(f"Arquivo: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
