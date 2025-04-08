import mido
import playsound
import threading
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QFileDialog, QMenu
import os

#Map MIDI notes to the sounds you want
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

#GUI Coding (sobbing)
class DrumModuleApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MIDI Config")
        self.setGeometry(100, 100, 800, 400)

        #Set appearance mode to system (Light/Dark based on system)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
            }
        """)

        #Preload the background image using QPixmap
        bg_image = QPixmap("/Users/hasan/Documents/Mayflower-Drum-Module-Utility/Background/Phospilled.png")
        bg_image_resized = bg_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)

        #Create a QLabel for background
        self.bg_label = QLabel(self)
        self.bg_label.setPixmap(bg_image_resized)
        self.bg_label.setGeometry(0, 0, 800, 400)

        #Define instrument buttons
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

        self.position_buttons()

    def position_buttons(self):
        #Position buttons for the instruments
        positions = self.position_generator(len(self.instruments))
        for i, instrument in enumerate(self.instruments):
            button = QPushButton(instrument["name"], self)
            button.setStyleSheet("""
             QPushButton {
                background-color: #1970fc;
                color: black;
                font-size: 12px;
                padding: 10px;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #6bffbc;
            }
            """)
            button.setGeometry(positions[i][0], positions[i][1], 100, 40)
        
            #Connecting the button click to the preview_sound function
            button.clicked.connect(lambda _, sound=instrument["sound"]: self.preview_sound(sound))
        
            #Make buttons draggable
            self.make_draggable(button)
        
            #Set up right-click context menu for changing sound
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda _, btn=button, instrument=instrument: self.show_context_menu(_, btn, instrument))


    def position_generator(self, num_buttons, spacing=120):
        #Generate positions for buttons
        positions = []
        for i in range(num_buttons):
            x = 50 + (i % 5) * spacing
            y = 50 + (i // 5) * 100
            positions.append((x, y))
        return positions

    def preview_sound(self, sound):
        #review sound by playing it when a button is clicked
        def sound_thread():
            playsound.playsound(sound, block=False)

        threading.Thread(target=sound_thread).start()

    def make_draggable(self, widget):
        #Enable dragging for PyQt6 widgets
        widget.setMouseTracking(True)

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

    def show_context_menu(self, event, button, instrument):
        #Display the context menu on right-click
        context_menu = QMenu(self)

        #Add an option to change the sound
        change_sound_action = context_menu.addAction("Change Sound")
        change_sound_action.triggered.connect(lambda: self.change_sound(button, instrument))

        #Use the position where the right-click occurred to show the context menu
        context_menu.exec(self.mapToGlobal(QPoint(event.x(), event.y())))

    def change_sound(self, button, instrument):
       #Allow the user to change the sound for the button
        new_sound, _ = QFileDialog.getOpenFileName(self, "Select New Sound", "", "Audio Files (*.mp3 *.wav)")

        if new_sound:
            instrument["sound"] = new_sound
            button.setText(f"{instrument['name']} (Custom)")

    def listen_for_midi(self):
        #Listen for MIDI input and trigger appropriate sound
        try:
            with mido.open_input(keyboard) as port:
                for message in port:
                    if message.type == 'note_on' and message.note in note_to_drum:
                        self.preview_sound(note_to_drum[message.note])
        except KeyboardInterrupt:
            print("MIDI listening interrupted.")


def run_midi_thread():
    #Start listening for MIDI input in a separate thread
    app.listen_for_midi()


if __name__ == "__main__":
    #Initialize the PyQt6 application
    app = QApplication([])

    #Create the main window and show it
    window = DrumModuleApp()
    window.show()

    #Start the MIDI listening in a separate thread
    midi_thread = threading.Thread(target=run_midi_thread, daemon=True)
    midi_thread.start()

    #Start the event loop for the application
    app.exec()
