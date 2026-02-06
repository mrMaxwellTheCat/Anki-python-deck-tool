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

If you have audio files:

```bash
anki-yaml-tool build \
  --data examples/audio/data.yaml \
  --config examples/audio/config.yaml \
  --media-dir /path/to/audio/files \
  --output pronunciation.apkg \
  --deck-name "Pronunciation Practice"
```

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

Expected audio files:
- `entrepreneur.mp3`
- `croissant.mp3`
- `schedule.mp3`
- `quinoa.mp3`
- `colonel.mp3`
- `schadenfreude.mp3`
- `massachusetts.mp3`
- `acai.mp3`
- `worcestershire.mp3`
- `cacophony.mp3`

## Creating Audio Files

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
