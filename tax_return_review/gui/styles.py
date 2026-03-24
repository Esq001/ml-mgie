"""UI constants and style definitions."""

# Window
WINDOW_TITLE = "Tax Return Review Tool"
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700
WINDOW_DEFAULT_GEOMETRY = "1100x750"

# Fonts
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 10
FONT_HEADING = (FONT_FAMILY, 12, "bold")
FONT_NORMAL = (FONT_FAMILY, FONT_SIZE)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_MONO = ("Consolas", FONT_SIZE)
FONT_TREE = (FONT_FAMILY, 9)

# Padding
PAD_X = 8
PAD_Y = 4
PAD_FRAME = 10

# Colors for discrepancy levels
COLORS = {
    "match": "#E8F5E9",       # light green
    "warning": "#FFF9C4",     # light yellow
    "error": "#FFCDD2",       # light red
    "missing": "#E0E0E0",     # light gray
    "bg": "#F5F5F5",          # window background
    "panel_bg": "#FFFFFF",    # panel background
    "accent": "#1565C0",      # blue accent
    "text": "#212121",        # dark text
    "text_light": "#757575",  # lighter text
}

# File dialog filters
FILE_FILTERS = [
    ("PDF files", "*.pdf"),
    ("CSV files", "*.csv"),
    ("JSON files", "*.json"),
    ("All files", "*.*"),
]
