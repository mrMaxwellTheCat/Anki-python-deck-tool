"""Importa un .apkg en Anki vía AnkiConnect."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path
from typing import Any, Dict

try:
    import requests
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "Falta requests. Instala con: pip install requests"
    ) from exc


ANKI_CONNECT_URL = "http://127.0.0.1:8765"


def invoke(action: str, params: Dict[str, Any] | None = None) -> Any:
    payload = {
        "action": action,
        "version": 6,
        "params": params or {},
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data.get("result")


def store_apkg_to_media(apkg_path: Path, filename: str) -> None:
    raw = apkg_path.read_bytes()
    encoded = base64.b64encode(raw).decode("utf-8")
    invoke("storeMediaFile", {"filename": filename, "data": encoded})


def main() -> None:
    parser = argparse.ArgumentParser(description="Sube e importa un .apkg en Anki")
    parser.add_argument(
        "--apkg",
        default=str(Path(__file__).resolve().parents[1] / "numeros.apkg"),
        help="Ruta al .apkg",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Ejecuta sync al final",
    )
    args = parser.parse_args()

    apkg_path = Path(args.apkg).resolve()
    if not apkg_path.exists():
        raise SystemExit(f"No existe el archivo: {apkg_path}")

    # Usamos la ruta absoluta para que Anki encuentre el archivo localmente.
    # store_apkg_to_media(apkg_path, filename) solo sería necesario si Anki
    # corre en remoto y importPackage soportara leer de media, pero
    # importPackage suele requerir ruta de sistema de archivos.
    invoke("importPackage", {"path": str(apkg_path)})
    invoke("reloadCollection")

    if args.sync:
        invoke("sync")

    print("OK: paquete importado en Anki")


if __name__ == "__main__":
    main()
