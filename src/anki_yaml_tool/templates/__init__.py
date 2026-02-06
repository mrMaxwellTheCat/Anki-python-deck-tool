"""Init command templates for project scaffolding.

This module provides template data for the `init` command.
"""

# Template configurations for different project types
TEMPLATES = {
    "basic": {
        "description": "A simple flashcard deck with Front/Back fields",
        "deck_name": "My Deck",
        "config": {
            "name": "Basic",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Card 1",
                    "qfmt": "<div class='front'>{{Front}}</div>",
                    "afmt": "{{FrontSide}}<hr id=answer><div class='back'>{{Back}}</div>",
                }
            ],
            "css": """.card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: black;
  background-color: white;
}

.front, .back {
  padding: 20px;
}
""",
        },
        "data": [
            {
                "front": "What is the capital of France?",
                "back": "Paris",
                "tags": ["geography", "example"],
            },
            {
                "front": "What year did World War II end?",
                "back": "1945",
                "tags": ["history", "example"],
            },
        ],
    },
    "language-learning": {
        "description": "Vocabulary cards with word, translation, and example sentence",
        "deck_name": "Language Vocabulary",
        "config": {
            "name": "Vocabulary",
            "fields": ["Word", "Translation", "Example", "Pronunciation"],
            "templates": [
                {
                    "name": "Word → Translation",
                    "qfmt": """<div class='word'>{{Word}}</div>
{{#Pronunciation}}<div class='pronunciation'>[{{Pronunciation}}]</div>{{/Pronunciation}}""",
                    "afmt": """{{FrontSide}}
<hr id=answer>
<div class='translation'>{{Translation}}</div>
{{#Example}}<div class='example'>{{Example}}</div>{{/Example}}""",
                },
                {
                    "name": "Translation → Word",
                    "qfmt": "<div class='translation'>{{Translation}}</div>",
                    "afmt": """{{FrontSide}}
<hr id=answer>
<div class='word'>{{Word}}</div>
{{#Pronunciation}}<div class='pronunciation'>[{{Pronunciation}}]</div>{{/Pronunciation}}
{{#Example}}<div class='example'>{{Example}}</div>{{/Example}}""",
                },
            ],
            "css": """.card {
  font-family: arial;
  font-size: 24px;
  text-align: center;
  color: #333;
  background-color: #f5f5f5;
}

.word {
  font-size: 32px;
  font-weight: bold;
  color: #2196F3;
  margin: 20px 0;
}

.translation {
  font-size: 28px;
  color: #4CAF50;
  margin: 15px 0;
}

.pronunciation {
  font-size: 18px;
  color: #666;
  font-style: italic;
}

.example {
  font-size: 16px;
  color: #555;
  margin-top: 15px;
  padding: 10px;
  background: #fff;
  border-left: 3px solid #2196F3;
}
""",
        },
        "data": [
            {
                "word": "Bonjour",
                "translation": "Hello / Good morning",
                "example": "Bonjour, comment allez-vous?",
                "pronunciation": "bɔ̃ʒuʁ",
                "tags": ["french", "greetings"],
            },
            {
                "word": "Merci",
                "translation": "Thank you",
                "example": "Merci beaucoup!",
                "pronunciation": "mɛʁsi",
                "tags": ["french", "common"],
            },
        ],
    },
    "technical": {
        "description": "Programming and technical concepts with code examples",
        "deck_name": "Technical Notes",
        "config": {
            "name": "Technical Concept",
            "fields": ["Concept", "Definition", "Example", "Notes"],
            "templates": [
                {
                    "name": "Concept Card",
                    "qfmt": "<div class='concept'>{{Concept}}</div>",
                    "afmt": """{{FrontSide}}
<hr id=answer>
<div class='definition'>{{Definition}}</div>
{{#Example}}<div class='example'><pre><code>{{Example}}</code></pre></div>{{/Example}}
{{#Notes}}<div class='notes'>{{Notes}}</div>{{/Notes}}""",
                }
            ],
            "css": """.card {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 18px;
  text-align: left;
  color: #e0e0e0;
  background-color: #1e1e1e;
  padding: 20px;
}

.concept {
  font-size: 24px;
  font-weight: bold;
  color: #569cd6;
  text-align: center;
  margin-bottom: 20px;
}

.definition {
  line-height: 1.6;
  margin: 15px 0;
}

.example {
  background: #2d2d2d;
  border-radius: 5px;
  padding: 15px;
  margin: 15px 0;
  overflow-x: auto;
}

.example pre {
  margin: 0;
  white-space: pre-wrap;
}

.example code {
  font-family: 'Consolas', 'Courier New', monospace;
  color: #dcdcaa;
}

.notes {
  font-size: 14px;
  color: #808080;
  border-top: 1px solid #444;
  padding-top: 10px;
  margin-top: 15px;
}
""",
        },
        "data": [
            {
                "concept": "List Comprehension",
                "definition": "A concise way to create lists in Python using a single line of code.",
                "example": "squares = [x**2 for x in range(10)]",
                "notes": "More readable than equivalent for-loop for simple transformations.",
                "tags": ["python", "syntax"],
            },
            {
                "concept": "Big O Notation",
                "definition": "Mathematical notation that describes the limiting behavior of an algorithm's time or space complexity.",
                "example": "O(1) - Constant\nO(log n) - Logarithmic\nO(n) - Linear\nO(n²) - Quadratic",
                "notes": "Always consider worst-case complexity for algorithm analysis.",
                "tags": ["algorithms", "complexity"],
            },
        ],
    },
}

# README template for scaffolded projects
README_TEMPLATE = """# {deck_name}

A deck created with anki-yaml-tool.

## Getting Started

### Build the deck

```bash
anki-yaml-tool build --file deck.yaml --output {deck_name}.apkg
```

### Push to Anki

Make sure Anki is running with AnkiConnect addon installed.

```bash
anki-yaml-tool push --apkg {deck_name}.apkg
```

### Validate

```bash
anki-yaml-tool validate --file deck.yaml
```

## Editing

Edit `deck.yaml` to add, remove, or modify cards. The file has two sections:

- `config`: Defines the note type (fields, templates, CSS)
- `data`: Contains the actual card content

## Resources

- [anki-yaml-tool documentation](https://github.com/yourusername/anki-yaml-tool)
- [AnkiConnect API](https://foosoft.net/projects/anki-connect/)
"""


def get_template_names() -> list[str]:
    """Return list of available template names."""
    return list(TEMPLATES.keys())


def get_template(name: str) -> dict:
    """Get template data by name.

    Args:
        name: Template name (basic, language-learning, technical)

    Returns:
        Template dictionary with config, data, and metadata

    Raises:
        KeyError: If template name is not found
    """
    if name not in TEMPLATES:
        raise KeyError(
            f"Template '{name}' not found. Available: {get_template_names()}"
        )
    return TEMPLATES[name]


def generate_readme(deck_name: str) -> str:
    """Generate README content for a project.

    Args:
        deck_name: Name of the deck

    Returns:
        README content as string
    """
    return README_TEMPLATE.format(deck_name=deck_name)
