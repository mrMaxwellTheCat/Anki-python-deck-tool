"""Convert example files from legacy format to new single-file format.

This script converts all examples from the old format (separate config.yaml and
data.yaml files) to the new single-file format (deck.yaml).
"""

from pathlib import Path

import yaml


def str_representer(dumper, data):
    """Custom YAML representer to preserve multi-line strings."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def convert_example(example_dir: Path) -> None:
    """Convert an example directory to the new format.

    Args:
        example_dir: Path to the example directory.
    """
    config_file = example_dir / "config.yaml"
    data_file = example_dir / "data.yaml"
    output_file = example_dir / "deck.yaml"

    if not config_file.exists() or not data_file.exists():
        print(f"  Skipping {example_dir.name} (missing config or data file)")
        return

    print(f"  Converting {example_dir.name}...")

    # Load config and data
    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    with open(data_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Determine deck name based on example type
    deck_name_map = {
        "basic": "Basic Vocabulary",
        "language-learning": "Language Learning::Vocabulary",
        "math": "Mathematics",
        "technical": "Technical Terms",
        "medical": "Medical Terminology",
        "historical": "Historical Events",
        "cloze": "Cloze Deletion Practice",
        "audio": "Pronunciation Practice",
    }

    deck_name = deck_name_map.get(
        example_dir.name, config.get("name", "Generated Deck")
    )

    # Determine media folder based on whether it exists
    media_dir = example_dir / "media"
    media_folder = "./media/" if media_dir.exists() else None

    # Get field names from config for mapping
    fields = config.get("fields", [])

    # Transform data: map lowercase keys to match field names
    transformed_data = []
    if data:
        for item in data:
            transformed_item = {}
            # Create a mapping of lowercase field names to actual field names
            field_map = {field.lower(): field for field in fields}

            for key, value in item.items():
                # Map the key to the correct field name (case-sensitive)
                # If key matches a lowercase field name, use the properly cased version
                # Otherwise, keep the original key (for tags, id, etc.)
                if key.lower() in field_map:
                    transformed_item[field_map[key.lower()]] = value
                else:
                    transformed_item[key] = value

            transformed_data.append(transformed_item)

    # Build new format
    new_format = {
        "config": {
            "name": config.get("name"),
            "deck-name": deck_name,
            "css": config.get("css", ""),
            "fields": fields,
            "templates": config.get("templates", []),
        },
        "data": transformed_data,
    }

    # Add media-folder if it exists
    if media_folder:
        new_format["config"]["media-folder"] = media_folder

    # Write new format
    with open(output_file, "w", encoding="utf-8") as f:
        # Register custom representer for multi-line strings
        yaml.add_representer(str, str_representer)
        yaml.dump(
            new_format,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=float("inf"),
        )

    print(f"    Created {output_file.name}")


def main():
    """Convert all examples to the new format."""
    project_root = Path(__file__).parent.parent
    examples_dir = project_root / "examples"

    print("Converting examples to new single-file format...")
    print()

    # Get all example directories
    example_dirs = [
        d for d in examples_dir.iterdir() if d.is_dir() and d.name != "__pycache__"
    ]

    for example_dir in sorted(example_dirs):
        convert_example(example_dir)

    print()
    print("Conversion complete!")
    print()
    print("Note: The old config.yaml and data.yaml files are still present.")
    print("You can remove them after verifying the new deck.yaml files work correctly.")


if __name__ == "__main__":
    main()
