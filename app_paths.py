import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", ROOT))
ASSETS_DIR = RESOURCE_ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
THEMES_DIR = RESOURCE_ROOT / "themes"


def _user_data_dir():
    """Return a writable location for installed-app data.

    Source checkouts intentionally keep using their local ``srms.db`` so
    developers can work with the checked-in sample database. A frozen Windows
    build must never write beside its executable because that directory may be
    protected (for example, under Program Files).
    """
    if not getattr(sys, "frozen", False):
        return ROOT
    base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home())
    path = base / "SRMS"
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = _user_data_dir()
BACKUPS_DIR = DATA_DIR / "backups"
DATABASE_FILE = DATA_DIR / "srms.db"


def asset_path(*parts):
    return ASSETS_DIR.joinpath(*parts)


def icon_path(name):
    filename = name if "." in name else f"{name}.svg"
    return ICONS_DIR / filename


def resolve_path(value):
    if value in (None, ""):
        return None
    return (DATA_DIR / value).resolve() if not Path(value).is_absolute() else Path(value)
