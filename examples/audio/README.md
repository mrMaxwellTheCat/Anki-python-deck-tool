# Audio Pronunciation Example

This example demonstrates a deck for learning pronunciation with audio support, IPA notation, and listening comprehension.

## Files

- `config.yaml` - "Pronunciation Practice" note type with audio templates
- `data.yaml` - Sample pronunciation cards with IPA and audio references

## Features

- **Bidirectional cards**: Listen-to-recognize and word-to-pronunciation
- **IPA notation**: International Phonetic Alphabet for accurate pronunciation
- **Audio integration**: References audio files in Anki format
- **Difficulty levels**: Categorize words by pronunciation difficulty
- **Multiple languages**: English, French, German, Spanish, Portuguese
- **Context examples**: Usage examples for each word
- **Visual audio prompt**: Clear indication when audio should be played

## Usage

### With audio files

The example includes pre-generated audio files for all pronunciation samples:

```bash
anki-yaml-tool build \
  --data examples/audio/data.yaml \
  --config examples/audio/config.yaml \
  --media-dir examples/audio/media \
  --output pronunciation.apkg \
  --deck-name "Pronunciation Practice"
```

#### Regenerating Audio Files

To regenerate audio files with updated pronunciations:

```bash
# From project root
python scripts/generate_audio.py
```

This will:
- Use Microsoft Edge TTS (free, high-quality)
- Generate native pronunciations for each language
- Save audio files to `examples/audio/media/`
- Use appropriate voices: English (US), French, Spanish, German, Portuguese

The script requires: `pip install edge-tts pyyaml`

### Without audio files (IPA only)

```bash
anki-yaml-tool build \
  --data examples/audio/data.yaml \
  --config examples/audio/config.yaml \
  --output pronunciation.apkg \
  --deck-name "Pronunciation Practice"
```

## Audio File Format

The example uses Anki's audio format: `[sound:filename.mp3]`

**Included audio files (pre-generated):**
- `entrepreneur.mp3` - American English pronunciation
- `croissant.mp3` - French pronunciation
- `schedule.mp3` - American English pronunciation
- `quinoa.mp3` - Spanish pronunciation
- `colonel.mp3` - American English pronunciation
- `schadenfreude.mp3` - German pronunciation
- `massachusetts.mp3` - American English pronunciation
- `acai.mp3` - Brazilian Portuguese pronunciation
- `worcestershire.mp3` - American English pronunciation
- `cacophony.mp3` - American English pronunciation

All audio files are located in `examples/audio/media/` and are automatically included when building with `--media-dir`.

## Creating Audio Files

### Automated Generation (Recommended)

Use the provided script to generate audio for all words:

```bash
python scripts/generate_audio.py
```

This uses Microsoft Edge TTS with native speakers for each language:
- **English**: American English (Aria Neural)
- **French**: French (Denise Neural)
- **Spanish**: Spanish (Elvira Neural)
- **German**: German (Katja Neural)
- **Portuguese**: Brazilian Portuguese (Francisca Neural)

### Option 1: Text-to-Speech (TTS)

Use online TTS services or tools:
- Google Text-to-Speech
- Amazon Polly
- Microsoft Azure TTS
- macOS `say` command: `say -o output.aiff "word" && ffmpeg -i output.aiff output.mp3`

### Option 2: Recording

- Record native speakers
- Use Forvo.com for crowdsourced pronunciations
- Extract from pronunciation dictionaries

### Option 3: Existing Resources

- Merriam-Webster audio pronunciations
- Cambridge Dictionary audio
- Oxford Learner's Dictionaries

## Customization

### Field suggestions

Consider adding:
- `syllables` - Break down into syllables
- `stress_pattern` - Indicate which syllables are stressed
- `common_errors` - Typical mispronunciations to avoid
- `origin` - Etymology of the word
- `alternate_pronunciations` - Regional variations

### Additional categories

Extend with:
- Medical terminology
- Legal terminology
- Scientific terms
- Place names
- Personal names
- Technical jargon

## IPA Resources

Learning IPA (International Phonetic Alphabet):
- [Interactive IPA Chart](https://www.ipachart.com/)
- [Wikipedia IPA Guide](https://en.wikipedia.org/wiki/International_Phonetic_Alphabet)
- [Pronunciation guides](https://dictionary.cambridge.org/)

### IPA Font Installation

For best display of IPA characters, install one or more of these free fonts:

**Recommended IPA Fonts:**
- **Doulos SIL** - [Download from SIL](https://software.sil.org/doulos/)
- **Charis SIL** - [Download from SIL](https://software.sil.org/charis/)
- **Gentium Plus** - [Download from SIL](https://software.sil.org/gentium/)
- **Noto Sans** - [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans)

**Installation:**
- **Windows**: Double-click the `.ttf` file and click "Install"
- **macOS**: Double-click the `.ttf` file and click "Install Font"
- **Linux**: Copy to `~/.fonts/` or use Font Manager

The cards will automatically use the best available IPA font.

## Tags

The example uses tags to organize words by:
- Language (english, french, german, etc.)
- Category (food, business, geography, etc.)
- Difficulty (easy, medium, hard)
- Feature (silent-letters, loanwords, etc.)

## Tips for Effective Learning

1. **Listen actively**: Play audio multiple times
2. **Shadow speech**: Repeat immediately after hearing
3. **Record yourself**: Compare with native pronunciation
4. **Use IPA**: Learn to read phonetic transcription
5. **Practice regularly**: Consistent daily practice works best
