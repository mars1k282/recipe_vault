import sys
from pathlib import Path


def get_base_path() -> Path:
    """Возвращает базовый путь"""

    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent
