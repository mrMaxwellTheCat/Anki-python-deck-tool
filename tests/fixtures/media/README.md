# Test Media Files

This directory contains minimal valid media files for testing purposes.

## Files

### Images
- `test_image.png`: Minimal 1x1 pixel PNG image (transparent)
- `test_image.jpg`: Minimal 1x1 pixel JPEG image

### Audio
- `test_audio.mp3`: Minimal MP3 audio file (silent)

## Usage

These files are used in tests to verify media file handling functionality:
- Media file validation
- Media file discovery
- Media reference extraction from HTML
- Media file inclusion in Anki packages

The files are intentionally minimal to keep the repository size small while still providing valid media files for testing.

## Creating Additional Test Media

If you need to add more test media files:

```python
# Example: Create a minimal PNG
png_data = (
    b'\x89PNG\r\n\x1a\n'  # PNG signature
    b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'  # IHDR chunk
    b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
    b'\r\n-\xb4'  # IDAT chunk
    b'\x00\x00\x00\x00IEND\xaeB\x60\x82'  # IEND chunk
)
with open('new_image.png', 'wb') as f:
    f.write(png_data)
```

Keep files minimal to avoid bloating the repository.
