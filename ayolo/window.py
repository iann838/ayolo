import sys
from functools import partial
from pathlib import Path
from typing import List, Tuple

from PyQt5 import QtWidgets, QtCore, QtGui
from darktheme.widget_template import DarkPalette

from .background import Background
from .utilities import PropagableLineEdit


class Annotator(QtWidgets.QWidget):
    '''Widget for annotator section (center)'''

    current_annotations: List[Tuple[int, int, int, int, int]]
    current_img_path: Path = None

    def __init__(self, background: Background):
        super().__init__()
        self.background = background
        self.background.annotator = self

        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.img_bounds = (0, 0, 0, 0)
        self.ratio = (1, 1)
        self.drawing = False
        self.deleted = False
        self.nulled = False
        self.current_annotations = []

        self.setMouseTracking(True)
        self.setCursor(QtCore.Qt.CursorShape.BlankCursor)
        self.show()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.current_img_path:
            self.draw_img(painter, self.current_img_path)
        for x1, y1, x2, y2, clas in self.current_annotations:
            rgb = self.background.get_color(clas, self.background.control_panel.classlength)
            self.modify_painter_brush_and_pen(painter, rgb)
            painter.drawRect(QtCore.QRect(self.get_scaled_coordinate(x1, y1), self.get_scaled_coordinate(x2, y2)))
        rgb = self.background.get_color(self.background.control_panel.get_selected_class_id(), self.background.control_panel.classlength)
        self.modify_painter_brush_and_pen(painter, rgb)
        if self.drawing:
            painter.drawRect(QtCore.QRect(self.begin, self.end))
        self.force_bounded_pos(self.end)
        painter.pen().setWidth(1)
        painter.drawLine(self.end.x() + 1, self.img_bounds[1], self.end.x() + 1, self.img_bounds[3])
        painter.drawLine(self.img_bounds[0], self.end.y() + 1, self.img_bounds[2], self.end.y() + 1)
        coordinate_text_pos = QtCore.QPoint(self.end.x() + 1 if self.end.x() < self.img_bounds[2] - 75 else self.end.x() - 75, self.end.y() - 1 if self.end.y() > 20 else self.end.y() + 12)
        real_pos = self.get_real_coordinate(self.end)
        painter.drawText(coordinate_text_pos, f'({real_pos[0]}, {real_pos[1]})')

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            if not self.drawing:
                self.undo_annotation()
            else:
                self.begin = QtCore.QPoint()
                self.end = QtCore.QPoint()
                self.end = event.pos()
                self.drawing = not self.drawing
                self.update()
        elif event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = self.force_bounded_pos(event.pos())
            if not self.drawing:
                self.begin = pos
            else:
                self.current_annotations.append(
                    (
                        *self.force_top_left_corner(self.get_real_coordinate(self.begin), self.get_real_coordinate(self.end)),
                        self.background.control_panel.get_selected_class_id()
                    )
                )
                self.background.control_panel.update_current_annotations_lw(self.current_annotations)
                self.background.control_panel.search.setFocus()
                self.background.control_panel.search.selectAll()
                self.begin = QtCore.QPoint()
                self.end = QtCore.QPoint()
            self.end = pos
            self.drawing = not self.drawing
            self.update()
        elif event.button() == QtCore.Qt.MouseButton.ForwardButton:
            self.background.image_browser.navigate_next()
        elif event.button() == QtCore.Qt.MouseButton.BackButton:
            self.background.image_browser.navigate_prev()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        pos = self.force_bounded_pos(event.pos())
        self.end = pos
        self.update()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        wheelcounter = event.angleDelta()
        current_row = self.background.control_panel.classes_lw.currentRow()
        if wheelcounter.y() / 120 == -1:
            if current_row < self.background.control_panel.classes_lw.count() - 1:
                self.background.control_panel.classes_lw.setCurrentRow(current_row + 1)
        elif wheelcounter.y() / 120 == 1:
            if current_row > 0:
                self.background.control_panel.classes_lw.setCurrentRow(current_row - 1)

    def resizeEvent(self, _):
        self.begin = QtCore.QPoint(self.img_bounds[0], self.img_bounds[1])
        self.end = QtCore.QPoint(self.img_bounds[0], self.img_bounds[1])
        self.drawing = False
        self.update()

    def get_real_coordinate(self, pos: QtCore.QPoint):
        return round((pos.x() - self.img_bounds[0]) * self.ratio[0]), round((pos.y() - self.img_bounds[1]) * self.ratio[1])

    def get_scaled_coordinate(self, x: int, y: int):
        return QtCore.QPoint(round(x / self.ratio[0] + self.img_bounds[0]), round(y / self.ratio[1] + self.img_bounds[1]))

    def force_top_left_corner(self, x: Tuple[int, int], y: Tuple[int, int]):
        return min(x[0], y[0]), min(x[1], y[1]), max(x[0], y[0]), max(x[1], y[1])

    def modify_painter_brush_and_pen(self, painter: QtGui.QPainter, rgb):
        painter.setBrush(QtGui.QBrush(QtGui.QColor(*rgb, 70)))
        pen = QtGui.QPen(QtGui.QColor(*rgb))
        pen.setWidth(2)
        painter.setPen(pen)

    def draw_img(self, painter: QtGui.QPainter, path: Path):
        size = self.size()
        point = QtCore.QPoint(0, 0)
        pixmap = QtGui.QPixmap(str(path))
        original_size = (pixmap.size().width(), pixmap.size().height())
        scaledPix = pixmap.scaled(size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, transformMode=QtCore.Qt.TransformationMode.SmoothTransformation)
        point.setX((size.width() - scaledPix.width())/2)
        point.setY((size.height() - scaledPix.height())/2)
        self.img_bounds = (point.x(), point.y(), point.x() + scaledPix.size().width(), point.y() + scaledPix.size().height())
        try:
            self.ratio = (original_size[0] / scaledPix.width(), original_size[1] / scaledPix.height())
        except ZeroDivisionError:
            msg_box = QtWidgets.QtWidgets.Qtclose = QtWidgets.QMessageBox()
            msg_box.critical(self.background.image_browser, 'Error loading image', "Image not found or it's dimension could not be resolved.", QtWidgets.QMessageBox.StandardButton.Ok)
            painter.end()
            self.background.image_browser.navigate_next()
        painter.drawPixmap(point, scaledPix)

    def force_bounded_pos(self, pos: QtCore.QPoint):
        if pos.x() < self.img_bounds[0]:
            pos.setX(self.img_bounds[0])
        elif pos.x() > self.img_bounds[2]:
            pos.setX(self.img_bounds[2])
        if pos.y() < self.img_bounds[1]:
            pos.setY(self.img_bounds[1])
        elif pos.y() > self.img_bounds[3]:
            pos.setY(self.img_bounds[3])
        return pos

    def clear_annotations(self):
        self.drawing = False
        self.current_annotations = []
        self.background.control_panel.update_current_annotations_lw(self.current_annotations)
        self.update()

    def save_annotations(self, null=False):
        if self.deleted or self.current_img_path is None:
            return
        if null:
            self.background.images.save(self.current_img_path.name, self.current_annotations)
            self.nulled = True
            self.background.image_browser.navigate_next()
        elif len(self.current_annotations):
            self.background.images.save(self.current_img_path.name, self.current_annotations)
        elif not self.nulled:
            self.background.images.pop(self.current_img_path.name)

    def undo_annotation(self):
        try:
            self.current_annotations.pop()
            self.background.control_panel.update_current_annotations_lw(self.current_annotations)
            self.update()
        except IndexError:
            pass

    def open_image(self, path: Path, annotations):
        self.current_img_path = path
        self.current_annotations = annotations
        self.background.control_panel.update_current_annotations_lw(self.current_annotations)
        self.deleted = False
        self.drawing = False
        self.nulled = False
        self.update()

    def update_last_annotation_class(self, clas):
        # try:
        #     last = list(self.current_annotations[-1])
        #     last[-1] = clas
        #     self.current_annotations[-1] = tuple(last)
        #     self.background.control_panel.update_current_annotations_lw(self.current_annotations)
        # except IndexError:
        #     pass
        # THIS WAS REMOVED SINCE v0.2.0 AS YOU SHOULD SELECT CLASS BEFORE ANNOTATING
        self.update()

    def push_back_annotation(self, ind):
        self.current_annotations.append(self.current_annotations.pop(ind))
        self.background.control_panel.update_current_annotations_lw(self.current_annotations)
        self.update()


class ControlPanel(QtWidgets.QWidget):
    '''Widget for control panel section (right)'''

    def __init__(self, background: Background):        
        super().__init__()
        self.background = background
        self.background.control_panel = self
        self.classnames = self.background.classes
        self.classnames_lower_set = set(clas.lower() for clas in self.classnames)
        self.classlength = len(self.classnames)
        self.sorted_class_ids_by_name = sorted(list(range(self.classlength)), key=lambda x: self.classnames[x])
        self.search_result_class_ids = list(range(self.classlength))

        layout = QtWidgets.QVBoxLayout()

        self.search = PropagableLineEdit()
        self.classes_lw = QtWidgets.QListWidget()
        
        self.current_annotations_lb = QtWidgets.QLabel('Current Annotations')
        self.current_annotations_lw = QtWidgets.QListWidget()
        self.current_annotations_lw.currentRowChanged.connect(self.current_annotations_row_changed)

        self.save_btn = QtWidgets.QPushButton('Save (S)')
        self.save_btn.clicked.connect(self.background.annotator.save_annotations)
        self.null_btn = QtWidgets.QPushButton('Null (N)')
        self.null_btn.clicked.connect(partial(self.background.annotator.save_annotations, null=True))
        self.undo_btn = QtWidgets.QPushButton('Undo (Z)')
        self.undo_btn.clicked.connect(self.background.annotator.undo_annotation)
        self.delete_btn = QtWidgets.QPushButton('Delete (D)')
        self.delete_btn.clicked.connect(self.delete_current_image)
        self.clear_btn = QtWidgets.QPushButton('Clear (X)')
        self.clear_btn.clicked.connect(self.background.annotator.clear_annotations)

        layout.addWidget(self.current_annotations_lb)
        layout.addWidget(self.current_annotations_lw)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.null_btn)
        layout.addWidget(self.undo_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.clear_btn)
        layout.addWidget(QtWidgets.QLabel('Class Search'))
        layout.addWidget(self.search)
        layout.addWidget(self.classes_lw)

        self.search.textChanged.connect(self.update_search_results)
        self.classes_lw.currentRowChanged.connect(self.selected_class_id_changed)

        self.update_search_results("")
        layout.setContentsMargins(20, 0, 20, 0)
        self.setLayout(layout)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        current_row = self.classes_lw.currentRow()
        if event.key() == QtCore.Qt.Key.Key_Down:
            if current_row < self.classes_lw.count() - 1:
                self.classes_lw.setCurrentRow(current_row + 1)
        elif event.key() == QtCore.Qt.Key.Key_Up:
            if current_row > 0:
                self.classes_lw.setCurrentRow(current_row - 1)
        elif event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            if current_row == self.classes_lw.count() - 1 and "Create class " in self.classes_lw.currentItem().text():
                self.background.classes.create_class(self.search.text())
                self.update_classes_vars()
                self.update_search_results(self.search.text())

    def update_classes_vars(self):
        self.classnames_lower_set = set(clas.lower() for clas in self.classnames)
        self.classlength = len(self.classnames)
        self.sorted_class_ids_by_name = sorted(list(range(self.classlength)), key=lambda x: self.classnames[x])
        self.search_result_class_ids = list(range(self.classlength))

    def update_search_results(self, text: str):
        self.classes_lw.currentRowChanged.disconnect()
        self.classes_lw.clear()
        self.search_result_class_ids = []
        for clas in (self.sorted_class_ids_by_name if text else range(self.classlength)):
            if self.classnames[clas].lower().startswith(text.lower()):
                list_item = QtWidgets.QListWidgetItem(f"{self.classnames[clas]} (#{clas})")
                color = self.background.get_color(clas, self.classlength)
                list_item.setForeground(QtGui.QColor(*color))
                self.classes_lw.addItem(list_item)
                self.search_result_class_ids.append(clas)
        if text not in self.classnames_lower_set and "Create class " not in self.search.text():
            list_item = QtWidgets.QListWidgetItem(f'Create class "{self.search.text()}" (Enter)')
            self.classes_lw.addItem(list_item)
        self.classes_lw.setCurrentRow(0)
        self.classes_lw.currentRowChanged.connect(self.selected_class_id_changed)
        self.selected_class_id_changed()
        self.update()

    def update_current_annotations_lw(self, annotations):
        self.current_annotations_lw.clear()
        for x1, y1, x2, y2, clas in annotations:
            list_item = QtWidgets.QListWidgetItem(f"{self.classnames[clas]} ({x1}, {y1}) * ({x2}, {y2})")
            color = self.background.get_color(clas, self.classlength)
            list_item.setForeground(QtGui.QColor(*color))
            self.current_annotations_lw.addItem(list_item)
        self.update()

    def current_annotations_row_changed(self, ind: int):
        if ind == self.current_annotations_lw.count() - 1:
            return
        self.background.annotator.push_back_annotation(ind)
        self.current_annotations_lw.setCurrentRow(self.current_annotations_lw.count() - 1)

    def get_selected_class_id(self):
        row = self.classes_lw.currentRow()
        if row < self.classes_lw.count() and "Create class " not in self.classes_lw.currentItem().text():
            return self.search_result_class_ids[self.classes_lw.currentRow()]
        return -1

    def selected_class_id_changed(self):
        self.background.annotator.update_last_annotation_class(self.get_selected_class_id())

    def navigate_prev_image(self):
        self.background.image_browser.navigate_prev()

    def navigate_next_image(self):
        self.background.image_browser.navigate_next()

    def delete_current_image(self):
        self.background.annotator.deleted = True
        self.background.images.remove(self.background.annotator.current_img_path.name)
        self.navigate_next_image()

    def mark_current_image_unannotate(self):
        self.background.images.remove(self.background.annotator.current_img_path.name)
        self.background.annotator.clear_annotations()


class ImageBrowser(QtWidgets.QWidget):
    '''Widget for image browser section (left)'''

    def __init__(self, background: Background):
        super().__init__()
        self.background = background
        self.background.image_browser = self
        self.images_states = self.background.images.image_annotation_counts
        self.image_names = {}
        self.current_image_name = None
        self.updating = False
        self.current_lw = None
        self.current_lw_index = None

        layout = QtWidgets.QVBoxLayout()

        self.annotated_lw = QtWidgets.QListWidget()
        self.unannotated_lw = QtWidgets.QListWidget()

        self.prev_btn = QtWidgets.QPushButton('Prev <<')
        self.prev_btn.clicked.connect(self.navigate_prev)
        self.next_btn = QtWidgets.QPushButton('Next >>')
        self.next_btn.clicked.connect(self.navigate_next)
        self.annotated_lw.currentRowChanged.connect(partial(self.selected_image_changed, 0))
        self.unannotated_lw.currentRowChanged.connect(partial(self.selected_image_changed, 1))
        self.annotated_lb = QtWidgets.QLabel('Annotated')
        self.unannotated_lb = QtWidgets.QLabel('Unannotated')

        self.lw_list: List[QtWidgets.QListWidget] = [self.annotated_lw, self.unannotated_lw]

        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.annotated_lb)
        layout.addWidget(self.annotated_lw)
        layout.addWidget(self.unannotated_lb)
        layout.addWidget(self.unannotated_lw)

        layout.setContentsMargins(20, 0, 20, 0)
        self.setLayout(layout)
        self.update_list_widgets()
        if self.unannotated_lw.count():
            self.unannotated_lw.setCurrentRow(0)
        elif self.annotated_lw.count():
            self.annotated_lw.setCurrentRow(0)

    def selected_image_changed(self, lw_index: int, row: int):
        if row == -1 or self.updating:
            return
        self.background.annotator.save_annotations()
        self.background.annotator.clear_annotations()
        this_lw = self.lw_list[lw_index]
        img_name = self.image_names[this_lw.currentItem().text()] # Switch back (when item name != item path)
        other_ind = (lw_index + 1) % len(self.lw_list)
        other_lw = self.lw_list[other_ind]
        if other_lw.currentRow() != -1:
            other_lw.clearSelection()
        self.load_image(img_name)

    def update_list_widgets(self):
        self.updating = True
        self.annotated_lw.clear()
        self.unannotated_lw.clear()
        self.image_names = {}
        for img_name, count in self.images_states.items():
            if count is None:
                title = img_name
                self.unannotated_lw.addItem(QtWidgets.QListWidgetItem(title))
                self.image_names[title] = img_name
                if img_name == self.current_image_name:
                    self.unannotated_lw.setCurrentRow(self.unannotated_lw.count() - 1)
                    self.current_lw = self.unannotated_lw
                    self.current_lw_index = 1
            else:
                title = f"{img_name} ({count})"
                self.annotated_lw.addItem(QtWidgets.QListWidgetItem(title))
                self.image_names[title] = img_name
                if img_name == self.current_image_name:
                    self.annotated_lw.setCurrentRow(self.annotated_lw.count() - 1)
                    self.current_lw = self.annotated_lw
                    self.current_lw_index = 0
        self.annotated_lb.setText(f"Annotated ({self.annotated_lw.count()})")
        self.unannotated_lb.setText(f"Unannotated ({self.unannotated_lw.count()})")
        self.update()
        self.updating = False

    def load_image(self, img_name):
        self.background.annotator.open_image(self.background.dir_path / img_name, self.background.images.annotations.get(img_name, []))
        self.current_image_name = img_name
        self.update_list_widgets()

    def other_lw(self, index):
        return self.lw_list[(index + 1) % len(self.lw_list)]

    def navigate_prev(self):
        other_lw = self.other_lw(self.current_lw_index)
        if self.current_lw.currentRow() - 1 < 0 and other_lw.count():
            other_lw.setCurrentRow(other_lw.count() - 1)
        else:
            self.current_lw.setCurrentRow((self.current_lw.currentRow() - 1) % self.current_lw.count())

    def navigate_next(self):
        other_lw = self.other_lw(self.current_lw_index)
        if self.current_lw.currentRow() + 1 >= self.current_lw.count() and other_lw.count():
            other_lw.setCurrentRow(0)
        else:
            self.current_lw.setCurrentRow((self.current_lw.currentRow() + 1) % self.current_lw.count())


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, dir_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Ayolo - Annotating tool for yolo v4 datasets")

        widget = QtWidgets.QWidget(self)
        self.resize(1800, 900)
        self.setCentralWidget(widget)
        self.center_self()

        layout = QtWidgets.QHBoxLayout()

        self.background = Background(dir_path)
        self.annotator = Annotator(self.background)
        self.control_panel = ControlPanel(self.background)
        self.image_browser = ImageBrowser(self.background)

        self.save_sc = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.save_sc.activated.connect(self.control_panel.save_btn.animateClick)
        self.null_sc = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.null_sc.activated.connect(self.control_panel.null_btn.animateClick)
        self.undo_sc = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self)
        self.undo_sc.activated.connect(self.control_panel.undo_btn.animateClick)
        self.delete_sc = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+D"), self)
        self.delete_sc.activated.connect(self.control_panel.delete_btn.animateClick)
        self.clear_sc = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+X"), self)
        self.clear_sc.activated.connect(self.control_panel.save_btn.animateClick)
        self.nav_prev_sc = QtWidgets.QShortcut(QtCore.Qt.Key.Key_PageUp, self)
        self.nav_prev_sc.activated.connect(self.image_browser.prev_btn.animateClick)
        self.nav_next_sc = QtWidgets.QShortcut(QtCore.Qt.Key.Key_PageDown, self)
        self.nav_next_sc.activated.connect(self.image_browser.next_btn.animateClick)

        layout.setContentsMargins(0, 20, 0, 20)

        layout.addWidget(self.image_browser, 2)
        layout.addWidget(self.annotator, 8)
        layout.addWidget(self.control_panel, 2)

        widget.setLayout(layout)
        self.background.control_panel.search.setFocus()
        self.activateWindow()

    def closeEvent(self, event):
        close = QtWidgets.QMessageBox()
        close.setText("Are you sure you want to exit ?")
        close.setWindowTitle("Exit")
        close.setIcon(QtWidgets.QMessageBox.Icon.Question)
        close.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        close = close.exec()

        if close == QtWidgets.QMessageBox.Yes:
            self.annotator.save_annotations()
            event.accept()
        else:
            event.ignore()

    def center_self(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    @classmethod
    def run(cls, dir_path):
        app = QtWidgets.QApplication(sys.argv)

        app.setStyle("Fusion")
        app.setPalette(DarkPalette())
        app.setStyleSheet("QToolTip { color: #ffffff; background-color: grey; border: 1px solid white; }")

        main = cls(dir_path)
        main.show()

        sys.exit(app.exec_())
