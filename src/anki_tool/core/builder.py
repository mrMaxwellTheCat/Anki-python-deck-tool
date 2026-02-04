import hashlib
import genanki
import yaml
from pathlib import Path
from typing import List, Dict, Any


class AnkiBuilder:
    def __init__(self, deck_name: str, model_config: Dict[str, Any]):
        self.deck_name = deck_name
        self.model_config = model_config
        self.model = self._build_model()
        self.deck = genanki.Deck(self.stable_id(deck_name), deck_name)
        self.media_files = []

    @staticmethod
    def stable_id(name: str) -> int:
        digest = hashlib.md5(name.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    def _build_model(self) -> genanki.Model:
        return genanki.Model(
            self.stable_id(self.model_config["name"]),
            self.model_config["name"],
            fields=[{"name": f} for f in self.model_config["fields"]],
            templates=self.model_config["templates"],
            css=self.model_config.get("css", ""),
        )

    def add_note(self, field_values: List[str], tags: List[str] = None):
        note = genanki.Note(model=self.model, fields=field_values, tags=tags or [])
        self.deck.add_note(note)

    def add_media(self, file_path: Path):
        if file_path.exists():
            self.media_files.append(str(file_path.absolute()))

    def write_to_file(self, output_path: Path):
        package = genanki.Package(self.deck)
        package.media_files = self.media_files
        package.write_to_file(str(output_path))
