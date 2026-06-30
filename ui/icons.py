from pathlib import Path
from PySide6.QtGui import QIcon

ROOT=Path(__file__).resolve().parent.parent

def icon(name):
    p=ROOT/"assets"/"icons"/f"{name}.svg"
    if p.exists():
        return QIcon(str(p))
    return QIcon()
