"""Generate audio files for pronunciation practice examples.

This script generates audio files for the words in the pronunciation
practice example deck using Microsoft Edge's TTS service (free).
"""

import asyncio
from pathlib import Path

import edge_tts
import yaml

# Voice mapping for different languages
VOICES = {
    "English": "en-US-AriaNeural",  # American English
    "French": "fr-FR-DeniseNeural",
    "Spanish": "es-ES-ElviraNeural",
    "German": "de-DE-KatjaNeural",
    "Portuguese": "pt-BR-FranciscaNeural",
}


async def generate_audio(text: str, output_file: Path, voice: str) -> None:
    """Generate audio file from text using edge-tts.

    Args:
        text: The text to convert to speech.
        output_file: Path where the audio file will be saved.
        voice: The voice ID to use for generation.
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_file))


async def main():
    """Generate audio files for all pronunciation examples."""
    # Paths
    project_root = Path(__file__).parent.parent
    data_file = project_root / "examples" / "audio" / "data.yaml"
    media_dir = project_root / "examples" / "audio" / "media"

    # Create media directory
    media_dir.mkdir(exist_ok=True)

    # Load data
    with open(data_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    print(f"Generating audio files for {len(data)} words...")
    print(f"Output directory: {media_dir}")
    print()

    # Generate audio for each word
    for i, item in enumerate(data, 1):
        word = item["word"]
        language = item["language"]
        audio_filename = item["audio"]

        # Output path
        output_path = media_dir / audio_filename

        # Get appropriate voice for language
        voice = VOICES.get(language, VOICES["English"])

        print(f"[{i}/{len(data)}] Generating: {word} ({language})")
        print(f"  Voice: {voice}")
        print(f"  Output: {audio_filename}")

        try:
            await generate_audio(word, output_path, voice)
            print("  ✓ Success")
        except Exception as e:
            print(f"  ✗ Failed: {e}")

        print()

    print("=" * 50)
    print("Audio generation complete!")
    print(f"Generated {len(data)} audio files in: {media_dir}")
    print()
    print("To build the deck with audio:")
    print("  anki-yaml-tool build \\")
    print("    --data examples/audio/data.yaml \\")
    print("    --config examples/audio/config.yaml \\")
    print("    --media-dir examples/audio/media \\")
    print("    --output pronunciation_practice.apkg \\")
    print("    --deck-name 'Pronunciation Practice'")


if __name__ == "__main__":
    asyncio.run(main())
