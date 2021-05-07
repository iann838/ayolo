import os
import re
import math
from pathlib import Path
from typing import List, TypeVar, TYPE_CHECKING

from .constants import COLORS, IMG_EXTENSIONS

if TYPE_CHECKING:
    from .window import Annotator, ImageBrowser, ControlPanel

T = TypeVar('T')


class ImageList:

    def __init__(self, path: Path) -> None:
        self.path = path.parent
        self.annotation_path = path
        self.modified = False
        self.image_annotation_counts = {}
        self.annotations = {}
        self.image_names = []

        for f in Background.sorted_paths_alphanumeric(self.path.glob("**/*")):
            if f.name.endswith(IMG_EXTENSIONS):
                self.image_annotation_counts[f.name] = None
                self.image_names.append(f.name)

        if not os.path.isfile(self.annotation_path):
            with open(self.annotation_path, 'w+') as f:
                pass
        with open(self.annotation_path, 'r') as f:
            for line in f.readlines():
                if not line:
                    continue
                img_name, annotations = self.annotation_deserialize(line.strip())
                self.annotations[img_name] = annotations
                self.image_annotation_counts[img_name] = len(annotations)

    def remove(self, name: str):
        self.image_annotation_counts.pop(name)
        self.annotations.pop(name, None)
        self.image_names.remove(name)
        os.remove(self.path / name)

    def pop(self, name: str):
        self.image_annotation_counts[name] = None
        self.annotations.pop(name, None)
        with open(self.annotation_path, 'w') as f:
            f.writelines([self.annotation_serialize(img_name, boxes) for img_name, boxes in self.annotations.items()])

    def save(self, name: str, annotations):
        self.image_annotation_counts[name] = len(annotations)
        self.annotations[name] = annotations
        with open(self.annotation_path, 'w') as f:
            f.writelines([self.annotation_serialize(img_name, boxes) for img_name, boxes in self.annotations.items()])

    @staticmethod
    def annotation_deserialize(line):
        splits = line.split()
        img_path = splits[0]
        boxes = list(tuple(int(b) for b in box.split(',')) for box in splits[1:])
        return img_path, boxes

    @staticmethod
    def annotation_serialize(img_path: str, boxes):
        return f"{img_path} {' '.join(','.join(str(b) for b in box) for box in boxes)}\n"


class ClassList(list):

    def __init__(self, path: str, *args, **kwargs):
        self.path = path
        with open(path, 'r') as f:
            for line in f.readlines():
                if "Create class " in line:
                    line.replace("Create class ", "Maybe stop messing around with ")
                if line:
                    self.append(line.strip())

    def create_class(self, name: str):
        with open(self.path, 'a') as f:
            f.write(name + '\n')
        self.append(name)

    def save(self):
        with open(self.path, 'w') as f:
            for clas in self:
                f.write(clas + '\n')


class Background:

    annotator: 'Annotator'
    control_panel: 'ControlPanel'
    image_browser: 'ImageBrowser'

    def __init__(self, dir_path: str) -> None:
        self.dir_path = Path(dir_path)
        self.images = ImageList(self.dir_path / "annotations.txt")
        self.classes = ClassList(self.dir_path / 'classes.txt')
        self.img_paths = self.sorted_paths_alphanumeric(f for f in self.dir_path.glob('**/*') if f.name.endswith(('.jpg', '.png')))

    @staticmethod
    def sorted_paths_alphanumeric(data: List[Path]):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key.name)] 
        return sorted(data, key=alphanum_key)

    @classmethod
    def get_color(cls, cls_id, clas_len, format="rgb"):
        if cls_id == -1:
            return (0, 0, 0)

        def _get_weight(c, x, max_val):
            ratio = float(x) / max_val * 5
            i = int(math.floor(ratio))
            j = int(math.ceil(ratio))
            ratio = ratio - i
            r = (1 - ratio) * COLORS[i][c] + ratio * COLORS[j][c]
            return int(r * 255)

        offset = cls_id * 123457 % clas_len
        red = _get_weight(2, offset, clas_len)
        green = _get_weight(1, offset, clas_len)
        blue = _get_weight(0, offset, clas_len)
        if format.lower() == "rgb":
            return (red, green, blue)
        if format.lower() == "bgr":
            return (blue, green, red)
        raise ValueError('Invalid color format')
