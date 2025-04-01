import mido
import playsound
import customtkinter as ctk
import threading  # Import threading to run MIDI listening at the same time as the GUI

# Map MIDI notes to the sounds you want
note_to_drum = {
    48: '/Users/hasan/Documents/the meowening/bass.mp3',
    50: '/Users/hasan/Documents/the meowening/bass.mp3',
    52: '/Users/hasan/Documents/the meowening/snare.wav',
    62: '/Users/hasan/Documents/the meowening/hightom.mp3',
    64: '/Users/hasan/Documents/the meowening/midtom.mp3',
    66: '/Users/hasan/Documents/the meowening/ftom.mp3',
    53: '/Users/hasan/Documents/the meowening/hihatopen.mp3',
    54: '/Users/hasan/Documents/the meowening/hihatclosed.mp3',
    56: '/Users/hasan/Documents/the meowening/rcymbal.mp3',
    57: '/Users/hasan/Documents/the meowening/ccymbal.mp3'
}

# (hopefully) user-configurable midi device name!
keyboard = 'LPK25 mk2'

# GUI Setup starts here >:)
app = ctk.CTk()
app.title("MIDI Config")
app.geometry("800x400")
ctk.set_appearance_mode("system")  #Automatically chooses the theme based on system settings


# Define the instruments for the buttons (Make this easier to do using the GUI)
instruments = [
    {"name": "Bass", "note": 48, "sound": note_to_drum[48], "x": 50, "y": 50},
    {"name": "Snare", "note": 52, "sound": note_to_drum[52], "x": 50, "y": 50},
    {"name": "High Tom", "note": 62, "sound": note_to_drum[62], "x": 50, "y": 50},
    {"name": "Mid Tom", "note": 64, "sound": note_to_drum[64], "x": 50, "y": 50},
    {"name": "Floor Tom", "note": 66, "sound": note_to_drum[66], "x": 50, "y": 50},
    {"name": "Opened Hi-Hat", "note": 53, "sound": note_to_drum[53], "x": 50, "y": 50},
    {"name": "Closed Hi-Hat", "note": 54, "sound": note_to_drum[54], "x": 50, "y": 50},
    {"name": "Ride Cymbal", "note": 56, "sound": note_to_drum[56], "x": 50, "y": 50},
    {"name": "Crash Tom", "note": 57, "sound": note_to_drum[57], "x": 50, "y": 50},
]

# Function to play sound when button is clicked
def play_sound(sound):
    # Define a function to run the sound in a new thread
    def sound_thread():
        playsound.playsound(sound, block=False)

    # Create and start a new thread for each sound played
    threading.Thread(target=sound_thread).start()

# Function to handle MIDI input
def listen_for_midi():
    try:
        # Open MIDI input port to listen for signals
        with mido.open_input(keyboard) as port:
            for message in port:
                if message.type == 'note_on' and message.note in note_to_drum:
                    print(f"Received signal for MIDI note {message.note}, playing {note_to_drum} in response!")
                    # Play the corresponding sound using playsound in a separate thread
                    play_sound(note_to_drum[message.note])
    except KeyboardInterrupt:
        print("MIDI listening interrupted.")

# Create draggable buttons for the instruments
def make_draggable(widget):
    initial_x = 0
    initial_y = 0
    is_dragging = False
    
    def on_drag_start(event):
        nonlocal initial_x, initial_y, is_dragging
        initial_x = event.x_root
        initial_y = event.y_root
        is_dragging = False

    def on_drag(event):
        nonlocal initial_x, initial_y, is_dragging
        if not is_dragging:
            if abs(event.x_root - initial_x) > 10 or abs(event.y_root - initial_y) > 10:
                is_dragging = True
        if is_dragging:
            widget.place(x=event.x_root - widget.winfo_width() // 2, y=event.y_root - widget.winfo_height() // 2)

    widget.bind("<Button-1>", lambda event: widget.place(x=event.x_root - widget.winfo_width() // 2, y=event.y_root - widget.winfo_height() // 2))
    widget.bind("<B1-Motion>", on_drag)
    widget.bind("<ButtonRelease-1>", lambda event: play_sound(widget['text']) if not is_dragging else None)

# Generate positions for the instrument buttons
def position_generator(num_buttons, spacing=120):
    positions = []
    for i in range(num_buttons):
        x = 50 + (i % 5) * spacing
        y = 50 + (i // 5) * 100
        positions.append((x, y))
    return positions

positions = position_generator(len(instruments))

for i, instrument in enumerate(instruments):
    button = ctk.CTkButton(
        app,
        text=instrument["name"],
        width=120, height=60, text_color="black", fg_color="lightblue", hover_color="lightgreen",
        command=lambda i=instrument: play_sound(i["sound"]))
    x, y = positions[i]
    button.place(x=x, y=y)
    make_draggable(button)  # Making the buttons draggable, if that wasn't obvious

# Start the MIDI listening in a separate thread
midi_thread = threading.Thread(target=listen_for_midi, daemon=True)
midi_thread.start()

# Start the GUI loop
app.mainloop()
