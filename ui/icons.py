from PySide6.QtGui import QIcon

from app_paths import icon_path

def icon(name):
    p = icon_path(name)
    if p.exists():
        return QIcon(str(p))
    return QIcon()
