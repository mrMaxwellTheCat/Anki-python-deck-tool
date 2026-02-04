"""
Build an Anki .apkg from a YAML source using genanki.

Expected YAML schema (list of items):
- id: num-0001
  numeral: "1"
  kanji: "一"
  lectura_a: "いち"
  lectura_b: "ひとつ"
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "Falta PyYAML. Instala con: pip install pyyaml"
    ) from exc

try:
    import genanki
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "Falta genanki. Instala con: pip install genanki"
    ) from exc


MODEL_NAME = "Numerales en japonés"
DECK_NAME = "test"


def stable_id(name: str) -> int:
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def load_items(yaml_path: Path) -> Iterable[dict]:
    with yaml_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or []
    if not isinstance(data, list):
        raise SystemExit("El YAML debe ser una lista de objetos.")
    return data


def build_model() -> "genanki.Model":
    return genanki.Model(
        stable_id(MODEL_NAME),
        MODEL_NAME,
        fields=[
            {"name": "Numeral"},
            {"name": "Kanji"},
            {"name": "Lectura A"},
            {"name": "Lectura B"},
        ],
        templates=[
            # 1. Kanji -> Numeral
            {
                "name": "Kanji -> Numeral",
                "qfmt": (
                    "<div class=\"kanji\">{{Kanji}}</div>"
                    "<div style=\"font-size: medium; color: gray;\">(Numeral)</div>"
                ),
                "afmt": (
                    "{{FrontSide}}"
                    "<hr id=\"answer\">"
                    "<div class=\"numeral\">{{Numeral}}</div>"
                ),
            },
            # 2. Numeral -> Kanji
            {
                "name": "Numeral -> Kanji",
                "qfmt": (
                    "<div class=\"numeral\">{{Numeral}}</div>"
                    "<div style=\"font-size: medium; color: gray;\">(Kanji)</div>"
                ),
                "afmt": (
                    "{{FrontSide}}"
                    "<hr id=\"answer\">"
                    "<div class=\"kanji\">{{Kanji}}</div>"
                ),
            },
            # 3. Lectura A -> Numeral
            {
                "name": "Lectura A -> Numeral",
                "qfmt": (
                    "<div class=\"lectura\">{{Lectura A}}</div>"
                    "<div style=\"font-size: medium; color: gray;\">(Numeral)</div>"
                ),
                "afmt": (
                    "{{FrontSide}}"
                    "<hr id=\"answer\">"
                    "<div class=\"numeral\">{{Numeral}}</div>"
                ),
            },
            # 4. Lectura B -> Numeral
            {
                "name": "Lectura B -> Numeral",
                "qfmt": (
                    "<div class=\"lectura\">{{Lectura B}}</div>"
                    "<div style=\"font-size: medium; color: gray;\">(Numeral)</div>"
                ),
                "afmt": (
                    "{{FrontSide}}"
                    "<hr id=\"answer\">"
                    "<div class=\"numeral\">{{Numeral}}</div>"
                    "<div class=\"kanji\" style=\"font-size: 50%;\">{{Kanji}}</div>"
                ),
            },
            # 5. Numeral -> Lecturas
            {
                "name": "Numeral -> Lecturas",
                "qfmt": (
                    "<div class=\"numeral\">{{Numeral}}</div>"
                    "<div style=\"font-size: medium; color: gray;\">(Lecturas)</div>"
                ),
                "afmt": (
                    "{{FrontSide}}"
                    "<hr id=\"answer\">"
                    "<div class=\"lectura\">{{Lectura A}}<br/>{{Lectura B}}</div>"
                ),
            },
        ],
        css=(
            ".card { font-family: 'Noto Sans JP', Arial, sans-serif; font-size: 28px; text-align: center; }"
            ".numeral { font-size: 42px; font-weight: 700; }"
            ".kanji { font-size: 54px; }"
            ".lectura { font-size: 36px; margin-top: 8px; }"
        ),
    )


def build_deck(items: Iterable[dict]) -> "genanki.Deck":
    deck = genanki.Deck(stable_id(DECK_NAME), DECK_NAME)
    model = build_model()

    for item in items:
        fields = [
            str(item.get("numeral", "")),
            str(item.get("kanji", "")),
            str(item.get("lectura_a", "")),
            str(item.get("lectura_b", "")),
        ]
        tags = ["numeros"]
        item_id = str(item.get("id", "")).strip()
        if item_id:
            tags.append(f"id::{item_id}")

        note = genanki.Note(
            model=model,
            fields=fields,
            tags=tags,
        )
        deck.add_note(note)

    return deck


def main() -> None:
    parser = argparse.ArgumentParser(description="Construye un .apkg desde un YAML")
    parser.add_argument(
        "--yaml",
        default=str(Path(__file__).resolve().parents[1] / "numeros.yaml"),
        help="Ruta al YAML de entrada",
    )
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[1] / "numeros.apkg"),
        help="Ruta de salida del .apkg",
    )
    args = parser.parse_args()

    yaml_path = Path(args.yaml).resolve()
    out_path = Path(args.out).resolve()

    items = load_items(yaml_path)
    deck = build_deck(items)

    package = genanki.Package(deck)
    package.write_to_file(str(out_path))
    print(f"OK: paquete escrito en {out_path}")


if __name__ == "__main__":
    main()
