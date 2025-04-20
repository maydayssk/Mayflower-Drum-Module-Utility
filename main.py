import mido
import playsound
import threading
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog, QMenu
import os

note_to_drum = {
    48: 'bass.mp3',
    50: 'bass.mp3',
    52: 'snare.wav',
    62: 'hightom.mp3',
    64: 'midtom.mp3',
    66: 'ftom.mp3',
    53: 'hihatopen.mp3',
    54: 'hihatclosed.mp3',
    56: 'rcymbal.mp3',
    57: 'ccymbal.mp3'
}

keyboard = 'LPK25 mk2'

class DrumModuleApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MIDI Config")
        self.setGeometry(100, 100, 800, 400)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.central_widget.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
            }
        """)

        # Background image
        self.bg_label = QLabel(self.central_widget)
        self.update_background()

        # Instrument config
        self.instruments = [
            {"name": "Bass", "note": 48, "sound": note_to_drum[48]},
            {"name": "Snare", "note": 52, "sound": note_to_drum[52]},
            {"name": "High Tom", "note": 62, "sound": note_to_drum[62]},
            {"name": "Mid Tom", "note": 64, "sound": note_to_drum[64]},
            {"name": "Floor Tom", "note": 66, "sound": note_to_drum[66]},
            {"name": "Opened Hi-Hat", "note": 53, "sound": note_to_drum[53]},
            {"name": "Closed Hi-Hat", "note": 54, "sound": note_to_drum[54]},
            {"name": "Ride Cymbal", "note": 56, "sound": note_to_drum[56]},
            {"name": "Crash Cymbal", "note": 57, "sound": note_to_drum[57]},
        ]

        self.buttons = []
        self.position_buttons()

        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")

        resolutions = [
            ("800 x 400", 800, 400),
            ("1024 x 576", 1024, 576),
            ("1280 x 720", 1280, 720),
            ("1920 x 1080", 1920, 1080),
        ]

        for label, width, height in resolutions:
            action = QAction(label, self)
            action.triggered.connect(lambda _, w=width, h=height: self.set_resolution(w, h))
            view_menu.addAction(action)

    def update_background(self):
        bg_image = QPixmap("/Users/hasan/Documents/Mayflower-Drum-Module-Utility/Background/Phospilled.png")
        resized_bg = bg_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        self.bg_label.setPixmap(resized_bg)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_resolution(self, width, height):
        self.resize(width, height)
        self.update_background()

    def position_buttons(self):
        positions = self.position_generator(len(self.instruments))
        for i, instrument in enumerate(self.instruments):
            button = QPushButton(instrument["name"], self.central_widget)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #1970fc;
                    color: white;
                    font-size: 12px;
                    padding: 10px;
                    border-radius: 16px;
                    border: 2px solid transparent;
                }
                QPushButton:hover {
                    background-color: #6bffbc;
                    border: 2px solid #ffffff;
                }
            """)
            button.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            button.setGeometry(positions[i][0], positions[i][1], 100, 40)

            button.clicked.connect(lambda _, sound=instrument["sound"]: self.preview_sound(sound))
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda _, btn=button, instrument=instrument: self.show_context_menu(_, btn, instrument))

            self.make_draggable(button)
            self.buttons.append(button)

    def position_generator(self, num_buttons, spacing=120):
        positions = []
        for i in range(num_buttons):
            x = 50 + (i % 5) * spacing
            y = 50 + (i // 5) * 100
            positions.append((x, y))
        return positions

    def preview_sound(self, sound):
        def sound_thread():
            playsound.playsound(sound, block=False)

        threading.Thread(target=sound_thread).start()

    def make_draggable(self, widget):
        widget.setMouseTracking(True)
        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        def on_drag_start(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.drag_position = event.globalPosition()

        def on_drag_move(event):
            if event.buttons() == Qt.MouseButton.LeftButton:
                delta = event.globalPosition() - self.drag_position
                widget.move(widget.pos() + delta.toPoint())
                self.drag_position = event.globalPosition()

        widget.mousePressEvent = on_drag_start
        widget.mouseMoveEvent = on_drag_move
        widget.installEventFilter(self)
        widget.original_geometry = widget.geometry()

    def eventFilter(self, watched, event):
        if isinstance(watched, QPushButton):
            if event.type() == QEvent.Type.Enter:
                anim = QPropertyAnimation(watched, b"geometry")
                anim.setDuration(150)
                anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                anim.setStartValue(watched.geometry())
                anim.setEndValue(watched.geometry().adjusted(-5, -5, 5, 5))
                anim.start()
                watched._hover_anim = anim

            elif event.type() == QEvent.Type.Leave:
                if hasattr(watched, "original_geometry"):
                    anim = QPropertyAnimation(watched, b"geometry")
                    anim.setDuration(150)
                    anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                    anim.setStartValue(watched.geometry())
                    anim.setEndValue(watched.original_geometry)
                    anim.start()
                    watched._hover_anim = anim

        return super().eventFilter(watched, event)

    def show_context_menu(self, event, button, instrument):
        context_menu = QMenu(self)
        change_sound_action = context_menu.addAction("Change Sound")
        change_sound_action.triggered.connect(lambda: self.change_sound(button, instrument))
        context_menu.exec(self.mapToGlobal(QPoint(event.x(), event.y())))

    def change_sound(self, button, instrument):
        new_sound, _ = QFileDialog.getOpenFileName(self, "Select New Sound", "", "Audio Files (*.mp3 *.wav)")
        if new_sound:
            instrument["sound"] = new_sound
            button.setText(f"{instrument['name']} (Custom)")

    def listen_for_midi(self):
        try:
            with mido.open_input(keyboard) as port:
                for message in port:
                    if message.type == 'note_on' and message.note in note_to_drum:
                        self.preview_sound(note_to_drum[message.note])
        except KeyboardInterrupt:
            print("MIDI listening interrupted.")

def run_midi_thread():
    window.listen_for_midi()

if __name__ == "__main__":
    app = QApplication([])
    window = DrumModuleApp()
    window.show()
    midi_thread = threading.Thread(target=run_midi_thread, daemon=True)
    midi_thread.start()
    app.exec()
