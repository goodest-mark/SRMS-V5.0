from pathlib import Path


ROOT = Path(__file__).resolve().parent
ASSETS_DIR = ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
THEMES_DIR = ROOT / "themes"
BACKUPS_DIR = ROOT / "backups"
DATABASE_FILE = ROOT / "srms.db"


def asset_path(*parts):
    return ASSETS_DIR.joinpath(*parts)


def icon_path(name):
    filename = name if "." in name else f"{name}.svg"
    return ICONS_DIR / filename


def resolve_path(value):
    if value in (None, ""):
        return None
    return (ROOT / value).resolve() if not Path(value).is_absolute() else Path(value)
