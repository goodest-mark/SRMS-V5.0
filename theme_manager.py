from pathlib import Path

THEME_DIR = Path(__file__).parent / "themes"

CURRENT_THEME = "blue"


def apply_theme(app, name):
    global CURRENT_THEME

    file = THEME_DIR / f"{name}.qss"

    if file.exists():
        app.setStyleSheet(file.read_text())
        CURRENT_THEME = name
        print(f"[THEME] Loaded {name}")
    else:
        print(f"[THEME] Theme not found: {name}")
