"""Helper script to print colored text cross-platform."""

import sys

try:
    import colorama

    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


def print_colored(text, color_code):
    """Print colored text using colorama for cross-platform support."""
    if HAS_COLORAMA:
        # Map color codes to colorama colors
        color_map = {
            "30": colorama.Fore.BLACK,
            "31": colorama.Fore.RED,
            "32": colorama.Fore.GREEN,
            "33": colorama.Fore.YELLOW,
            "34": colorama.Fore.BLUE,
            "35": colorama.Fore.MAGENTA,
            "36": colorama.Fore.CYAN,
            "37": colorama.Fore.WHITE,
        }
        color = color_map.get(color_code, "")
        print(f"{color}{text}{colorama.Style.RESET_ALL}")
    else:
        # Fallback to plain text
        print(text)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: print_color.py <color_code> <text>")
        sys.exit(1)

    color_code = sys.argv[1]
    text = sys.argv[2]
    print_colored(text, color_code)
