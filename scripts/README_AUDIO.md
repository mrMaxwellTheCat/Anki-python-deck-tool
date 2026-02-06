# Audio Generation Script

Generate high-quality pronunciation audio files for the audio example deck.

## Features

- Uses Microsoft Edge TTS (free, no API key required)
- Native speaker voices for each language
- Automatic voice selection based on language
- High-quality 24kHz MP3 output

## Requirements

```bash
pip install edge-tts pyyaml
```

## Usage

From the project root directory:

```bash
python scripts/generate_audio.py
```

This will:
1. Read pronunciation data from `examples/audio/data.yaml`
2. Generate audio for each word using appropriate language voices
3. Save MP3 files to `examples/audio/media/`

## Supported Languages

- **English**: American English (Aria Neural)
- **French**: French from France (Denise Neural)
- **Spanish**: Spanish from Spain (Elvira Neural)
- **German**: German (Katja Neural)
- **Portuguese**: Brazilian Portuguese (Francisca Neural)

## Output

The script generates MP3 files with the following naming convention:
- `entrepreneur.mp3` - matches the format in data YAML
- `[sound:entrepreneur.mp3]` - Anki audio format

All files are saved to `examples/audio/media/` directory.

## Building the Deck with Audio

After generating audio files:

```bash
anki-yaml-tool build \
  --data examples/audio/data.yaml \
  --config examples/audio/config.yaml \
  --media-dir examples/audio/media \
  --output pronunciation_practice.apkg \
  --deck-name "Pronunciation Practice"
```

## Adding New Words

1. Add new entries to `examples/audio/data.yaml`
2. Include the audio reference: `audio: "[sound:wordname.mp3]"`
3. Run the script to generate audio files
4. Build the deck with `--media-dir` flag

## Technical Details

- **TTS Engine**: Microsoft Edge Neural TTS
- **Audio Format**: MP3, 24kHz, 48 kbps, Mono
- **Average File Size**: 9-13 KB per word
- **Generation Time**: ~1 second per word

## Alternative Voices

To use different voices, edit the `VOICES` dictionary in `generate_audio.py`:

```python
VOICES = {
    "English": "en-GB-SoniaNeural",  # British English
    "French": "fr-CA-SylvieNeural",   # Canadian French
    # ... etc
}
```

List available voices:
```bash
python -m edge_tts --list-voices
```

## Troubleshooting

**Module not found error:**
```bash
pip install edge-tts pyyaml
```

**Network errors:**
- Ensure internet connection is active
- Edge TTS requires internet to generate audio
- Files are cached locally after generation

**Audio quality:**
- Edge TTS provides high-quality neural voices
- For even higher quality, consider:
  - Azure Cognitive Services (paid)
  - Google Cloud TTS (paid)
  - Recording native speakers
