from pathlib import Path
from .background import ImageList


def fix_corners(dir_path: str):

    def force_top_left(x1, y1, x2, y2, clas):
        return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), clas

    images = ImageList(Path(dir_path))
    for name, annotations in images.annotations.items():
        images.save(name, [force_top_left(*ann) for ann in annotations])
