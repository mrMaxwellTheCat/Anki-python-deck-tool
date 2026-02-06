# Medical Terminology Example

This example demonstrates a deck for learning medical terminology with comprehensive information including etymology and usage examples.

## Files

- `config.yaml` - "Medical Terminology" note type with bidirectional templates
- `data.yaml` - Sample medical terms with definitions, etymologies, and examples

## Features

- **Bidirectional cards**: Learn both term-to-definition and definition-to-term
- **Etymology**: Greek/Latin roots help with retention
- **Clinical examples**: Real-world usage contexts
- **Tags by specialty**: Organize by medical specialty (cardiology, nephrology, etc.)

## Usage

Build the deck:

```bash
anki-yaml-tool build \
  --data examples/medical/data.yaml \
  --config examples/medical/config.yaml \
  --output medical_terminology.apkg \
  --deck-name "Medical Terminology"
```

## Customization

### Adding more specialties

Extend the data file with terms from other specialties:
- Neurology
- Dermatology
- Endocrinology
- Psychiatry
- Oncology

### Field suggestions

Consider adding:
- `pronunciation` - Phonetic guide
- `abbreviation` - Common medical abbreviations
- `related_terms` - Associated terminology
- `image` - Anatomical diagrams or illustrations

## Tags

The example uses tags to organize terms by:
- Medical specialty (cardiology, hematology, etc.)
- Category (symptoms, conditions, treatment, etc.)
