import mido, threading, json, shutil
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QEvent, QSize, QTimer
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog, QMenu, QMessageBox, QComboBox
from pathlib import Path
from playsound import playsound

# Assign MIDI notes (the numbers) to their respective drum sounds
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

b_positions_file = "button_positions.json" # File for storing button placement
base_dir = Path(__file__).parent # Base directory (easier to refer to it this way)


class DrumModuleApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MIDI Config") # Window title
        self.setGeometry(100, 100, 800, 400) # Base resolution

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Add MIDI Device selector
        self.midi_device_selector = QComboBox(self)
        self.midi_device_selector.setGeometry(10, 10, 200, 30)
        self.midi_device_selector.addItem("Select MIDI Device")

        # Add available devices to the dropdown menu
        self.refresh_midi_devices()
        self.midi_device_selector.currentIndexChanged.connect(self.on_midi_device_selected)

        self.central_widget.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
            }
        """)

        self.central_widget.setMouseTracking(True)

        self.bg_label = QLabel(self.central_widget)
        self.update_background()

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
        self.sound_cache = {}
        self.load_all_sounds()

        self.buttons = []
        self.position_buttons()
        self.load_positions()
        self.create_menu()

        # Reset button coding
        self.reset_button = QPushButton("Reset Positions", self.central_widget)
        self.reset_button.setStyleSheet("""
            QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    font-size: 10px;
                    padding: 5px; 
                    border-radius: 12px;
                    border: 2px solid transparent;
            }          
            QPushButton:hover {
                background-color: #ff6659;
                border: 2px solid #ffffff;               
            }                                        
        """)
        self.reset_button.raise_() # To make sure it's on top of the button
        self.reset_button.clicked.connect(self.confirm_reset)
        self.reset_button.resize(120,35)
        self.position_reset_button()

    def notify_device_disconncted(self):
        def show_warning():
            QMessageBox.warning(self, "Device Disconnected!", "The MIDI device was disconnected!")
            self.device_label.setText("No device selected")
            self.connect_button.setText("Connect to Device")
            self.connect_button.setEnabled(True)
        QTimer.singleShot(0, show_warning)

    def refresh_midi_devices(self):
        # Get available MIDI input devices using mido
        midi_devices = mido.get_input_names()
        self.midi_device_selector.clear()
        self.midi_device_selector.addItem("Select MIDI Device")
        self.midi_device_selector.addItems(midi_devices)

    def on_midi_device_selected(self):
        selected_device = self.midi_device_selector.currentText()
        if selected_device != "Select MIDI Device":
            self.selected_midi_device = selected_device
            print(f"Selected MIDI Device: {self.selected_midi_device}")
            self.start_midi_listening()

    def start_midi_listening(self):
        if hasattr(self, 'selected_midi_device'):
            print(f"Listening for MIDI on {self.selected_midi_device}...")
            # Start the MIDI thread with the selected device
            self.midi_listening = True
            self.midi_thread = threading.Thread(target=self.listen_for_midi)
            self.midi_thread.daemon = True
            self.midi_thread.start()
    
    def reset_positions(self):
        positions = self.position_generator(len(self.instruments))
        for i, button in enumerate(self.buttons):
            button.move(positions[i][0], positions[i][1])
        
        # Delete saved positions file, if it exists
        try:
            Path(b_positions_file).unlink()
            print("[Reset] Positions file deleted!")
        except FileNotFoundError:
            print("[Reset] No saved positions file to delete :(")

    def position_reset_button(self):
        margin = 20
        x = self.width() - self.reset_button.width() - margin
        y = self.height() - self.reset_button.height() - margin
        self.reset_button.move(x, y)

    def confirm_reset(self):
        reply = QMessageBox.question(
            self,
            "Reset the position of the buttons?",
            "Are you sure you want to reset all button positions to default?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.reset_positions()

    def load_all_sounds(self):
        for instrument in self.instruments:
            sound_path = instrument.get("sound")
            full_path = Path(base_dir / "Sounds" / sound_path)
            
            if full_path.exists():
                try:
                    print(f"[Debug] Sound found: {full_path}")
                    # No need to load or cache the sound
                except Exception as e:
                    print(f"[Load Error] Could not handle sound {full_path}: {e}")
            else:
                print(f"[Load Error] Could not find sound: {full_path}")

    # Resolution menu
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

    # Function to scale the background with the window size
    def update_background(self):
        bg_path = base_dir / "Background" / "Phospilled.png"
        bg_image = QPixmap(str(bg_path))
        resized_bg = bg_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        self.bg_label.setPixmap(resized_bg)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    # Change resize event to work with some of the other functions
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background()
        self.position_reset_button() # Move reset button based on resolution
        self.midi_device_selector.setGeometry(10, 10, self.width() - 20,30) #Change MIDI device selector based on resolution

    def set_resolution(self, width, height):
        self.resize(width, height)
        self.update_background()

    # Load button position file
    def load_positions(self):
        try:
            with open(b_positions_file, "r") as f:
                loaded_positions = json.load(f)
                if len(loaded_positions) == len(self.instruments):
                    for button, pos in zip(self.buttons, loaded_positions):
                        button.move(pos[0], pos[1])
                else:
                    print("Mismatch in saved positions count")
        except (FileNotFoundError, json.JSONDecodeError):
            print("No saved positions found or error loading positions.")

    # Button sound preview
    def make_click_sound_callback(self, instrument):
        def callback():
            sound = instrument.get("sound")
            if sound:
                self.preview_sound(sound)
        return callback

    # Absolute hell (Button formatting and positioning)
    def position_buttons(self):
        positions = self.position_generator(len(self.instruments))
        for i, instrument in enumerate(self.instruments):
            button = QPushButton(instrument["name"], self.central_widget)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #1970fc;
                    color: white;
                    font-size: 10px;
                    padding: 10px;
                    border-radius: 16px;
                    border: 2px solid transparent;
                }
                QPushButton:hover {
                    background-color: #6bffbc;
                    border: 2px solid #ffffff;
                }
            """)
            # Don't mess with anything here!
            button.setMouseTracking(True)
            button.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            button.setGeometry(positions[i][0], positions[i][1], 100, 40)

            button.clicked.connect(self.make_click_sound_callback(instrument))
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda _, btn=button, instrument=instrument: self.show_context_menu(_, btn, instrument))

            self.make_draggable(button)
            self.buttons.append(button)

    # Button position generator
    def position_generator(self, num_buttons, spacing=130):
        positions = []
        for i in range(num_buttons):
            x = 50 + (i % 5) * spacing
            y = 50 + (i // 5) * 100
            positions.append((x, y))
        return positions

    # Function to play sounds in response to MIDI notes
    def preview_sound(self, sound):
        def play_sound():
            full_path = Path(base_dir / "Sounds" / sound)
            print(f"[Debug] Trying to play: {full_path}")
        
            # Check if file exists
            if not full_path.exists():
                print(f"[Sound Error] File not found: {full_path}")
                return
        
            try:
                # Play sound using playsound
                print(f"[Debug] Playing sound: {full_path}")
                playsound(str(full_path)) 
            except Exception as e:
                print(f"[Sound Error] Could not play sound: {e}")
        
        # Run the play_sound function in a separate thread to avoid blocking
        threading.Thread(target=play_sound, daemon=True).start()


    # Function to make the buttons... draggable
    def make_draggable(self, widget):
        widget.setMouseTracking(True)
        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if isinstance(watched, QPushButton):
            if event.type() == QEvent.Type.Enter:
                anim = QPropertyAnimation(watched, b"size")
                anim.setDuration(150)
                anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                anim.setStartValue(watched.size())
                anim.setEndValue(QSize(int(watched.width() * 1.2), int(watched.height() * 1.2)))
                anim.start()
                watched._hover_anim = anim

                watched.setStyleSheet("""
                    QPushButton {
                        background-color: #6bffbc;
                        color: white;
                        font-size: 10px;
                        padding: 10px;
                        border-radius: 16px;
                        border: 2px solid #ffffff;
                    }
                """)
                return True

            elif event.type() == QEvent.Type.Leave:
                anim = QPropertyAnimation(watched, b"size")
                anim.setDuration(150)
                anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                anim.setStartValue(watched.size())
                anim.setEndValue(QSize(100, 40))
                anim.start()
                watched._hover_anim = anim

                watched.setStyleSheet("""
                    QPushButton {
                        background-color: #1970fc;
                        color: white;
                        font-size: 10px;
                        padding: 10px;
                        border-radius: 16px;
                        border: 2px solid transparent;
                    }
                """)
                return True

            elif event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.drag_position = event.globalPosition()
                    return False  

            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() == Qt.MouseButton.LeftButton:
                    delta = event.globalPosition() - self.drag_position
                    new_position = watched.pos() + delta.toPoint()
                    watched.move(new_position)
                    self.drag_position = event.globalPosition()
                    return True

        return super().eventFilter(watched, event)

    # Save the positions of the buttons to the b_position_file tingie
    def save_positions(self):
        positions = [(button.pos().x(), button.pos().y()) for button in self.buttons]
        with open(b_positions_file, "w") as f:
            json.dump(positions, f)
        print(f"[Debug] Positions saved upon closing! :3")

    def closeEvent(self,event):
        self.save_positions()
        super().closeEvent(event)

    def show_context_menu(self, event, button, instrument):
        context_menu = QMenu(self)
        change_sound_action = context_menu.addAction("Change Sound")
        change_sound_action.triggered.connect(lambda: self.change_sound(button, instrument))
        context_menu.exec(self.mapToGlobal(QPoint(event.x(), event.y())))

    # For changing the sounds of the instruments
    def change_sound(self, button, instrument):
        new_sound, _ = QFileDialog.getOpenFileName(self, "Select New Sound", "", "Audio Files (*.mp3 *.wav)")
        if new_sound:
            # Copy the file to the sounds folder if it's not already there
            target_path = base_dir / "Sounds" / Path(new_sound).name
            if not target_path.exists():
                shutil.copy(new_sound, target_path)
            instrument["sound"] = Path(new_sound).name
            button.setText(f"{instrument['name']} (Custom)")


    def listen_for_midi(self):
        with mido.open_input(self.selected_midi_device) as inport:
            for msg in inport:
                if msg.type == "note_on":
                    sound = note_to_drum.get(msg.note)
                    if sound:
                        self.preview_sound(sound) # Plays sound

    def run(self):
        self.listener.listen_for_midi()

if __name__ == "__main__":
    app = QApplication([])
    window = DrumModuleApp()
    window.show()
    # Start MIDI listening after the window pops up
    if hasattr(window, 'selected_midi_device'):
        window.start_midi_listening() # Start listening for MIDI signals directly on the selected device
    app.exec()
