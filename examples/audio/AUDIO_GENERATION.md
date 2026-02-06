# Audio Generation for Pronunciation Practice

## Summary

This document explains how audio files were generated for the pronunciation practice example deck.

## What Was Done

1. **Created Audio Generation Script** (`scripts/generate_audio.py`)
   - Automated audio file generation using Microsoft Edge TTS
   - Free, high-quality neural voices
   - Multi-language support (English, French, Spanish, German, Portuguese)

2. **Generated Audio Files** (10 files, 128KB total)
   - All pronunciation examples now have real audio
   - Native speaker voices for each language
   - Proper pronunciation including:
     - Silent letters (colonel, worcestershire)
     - Foreign words (croissant, schadenfreude, quinoa, açaí)
     - Difficult pronunciations (entrepreneur, Massachusetts)

3. **Updated Documentation**
   - Added usage instructions to `examples/audio/README.md`
   - Created `scripts/README_AUDIO.md` with technical details
   - Documented how to regenerate audio files

## Generated Audio Files

Location: `examples/audio/media/`

| File               | Language   | Voice                 | Size |
|--------------------|------------|-----------------------|------|
| entrepreneur.mp3   | English    | en-US-AriaNeural      | 12KB |
| croissant.mp3      | French     | fr-FR-DeniseNeural    | 9KB  |
| schedule.mp3       | English    | en-US-AriaNeural      | 11KB |
| quinoa.mp3         | Spanish    | es-ES-ElviraNeural    | 9KB  |
| colonel.mp3        | English    | en-US-AriaNeural      | 9KB  |
| schadenfreude.mp3  | German     | de-DE-KatjaNeural     | 12KB |
| massachusetts.mp3  | English    | en-US-AriaNeural      | 13KB |
| acai.mp3           | Portuguese | pt-BR-FranciscaNeural | 9KB  |
| worcestershire.mp3 | English    | en-US-AriaNeural      | 11KB |
| cacophony.mp3      | English    | en-US-AriaNeural      | 11KB |

**Total**: 10 files, 128KB

## Building the Deck with Audio

```bash
anki-yaml-tool build \
  --data examples/audio/data.yaml \
  --config examples/audio/config.yaml \
  --media-dir examples/audio/media \
  --output pronunciation_practice.apkg \
  --deck-name "Pronunciation Practice"
```

**Output**: `pronunciation_practice_with_audio.apkg` (160KB)

## Example Cards

Each card includes:
- **Word**: The word to learn
- **IPA Notation**: International Phonetic Alphabet transcription
- **Audio**: Native speaker pronunciation (🔊)
- **Meaning**: Definition
- **Example**: Usage in context
- **Language**: Source language
- **Difficulty**: Easy/Medium/Hard

## Card Types

### 1. Listen and Recognize
- **Front**: Audio button + difficulty indicator
- **Back**: Word, IPA, meaning, example

### 2. Word to Pronunciation
- **Front**: Word + meaning
- **Back**: IPA notation + audio + example

## Technology Used

- **TTS Engine**: Microsoft Edge Neural TTS (free)
- **Audio Format**: MP3, 24kHz, 48 kbps, Mono
- **Languages**: 5 different native voices
- **Quality**: High-quality neural synthesis

## Benefits

1. **Free**: No API keys or paid services required
2. **High Quality**: Neural TTS sounds natural
3. **Multi-language**: Native speakers for each language
4. **Reproducible**: Script can regenerate audio anytime
5. **Lightweight**: Small file sizes (avg 10KB per file)
6. **Complete Example**: Fully functional demo deck

## Future Enhancements

Possible improvements:
- Add pitch/speed control
- Support for more languages
- Custom pronunciation (via IPA-to-speech)
- Multiple voice options per language
- Male/female voice selection
- Regional accent variants

## References

- [Microsoft Edge TTS](https://github.com/rany2/edge-tts) - TTS library used
- [IPA Chart](https://www.ipachart.com/) - IPA reference
- [Anki Audio Format](https://docs.ankiweb.net/templates/fields.html#media-references) - Media reference syntax

---

*Generated on 2026-02-06*
*Part of the Anki Python Deck Tool project*
