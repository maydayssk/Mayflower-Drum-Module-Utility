import mido
import playsound
import customtkinter as ctk
import tkinter as tk
from customtkinter import filedialog
import threading  # Import threading to run MIDI listening at the same time as the GUI
from PIL import Image, ImageTk
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

#(hopefully) user-configurable MIDI device name!
keyboard = 'LPK25 mk2'

# GUI Setup starts here >:)
app = ctk.CTk()

app.title("MIDI Config") #Window title
app.geometry("800x400") #Starting window size (same as Raspberry Pi Touchscreen)

app.update()

#Make note of the window 
window_width = app.winfo_width()
window_height = app.winfo_height()

bg_label = ctk.CTkLabel(app)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

#Function to resize background image
def update_bg_image(event=None):
    window_width = app.winfo_width()
    window_height = app.winfo_height()
    
    # Open the image and resize it to the window's current size
    image = Image.open("/Users/hasan/Documents/DrumModule/Mayflower-Drum-Module-Utility/Background/bleh.jpg")
    image_resized = image.resize((window_width, window_height))  # Resize to the window's resolution
    
    # Convert the image to a format that can be used in a Tkinter label
    app.bg_image = ImageTk.PhotoImage(image_resized)
    
    # Update the background image
    bg_label.configure(image=app.bg_image)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

update_bg_image

app.bind("<Configure>", update_bg_image)

ctk.set_appearance_mode("system")  #Automatically chooses the theme based on system settings


#Define the instruments for the buttons (Note to self: Make it easier to add instruments using the GUI (eventually))
instruments = [
    {"name": "Bass", "note": 48, "sound": note_to_drum[48], "x": 50, "y": 50},
    {"name": "Snare", "note": 52, "sound": note_to_drum[52], "x": 50, "y": 50},
    {"name": "High Tom", "note": 62, "sound": note_to_drum[62], "x": 50, "y": 50},
    {"name": "Mid Tom", "note": 64, "sound": note_to_drum[64], "x": 50, "y": 50},
    {"name": "Floor Tom", "note": 66, "sound": note_to_drum[66], "x": 50, "y": 50},
    {"name": "Opened Hi-Hat", "note": 53, "sound": note_to_drum[53], "x": 50, "y": 50},
    {"name": "Closed Hi-Hat", "note": 54, "sound": note_to_drum[54], "x": 50, "y": 50},
    {"name": "Ride Cymbal", "note": 56, "sound": note_to_drum[56], "x": 50, "y": 50},
    {"name": "Crash Cymbal", "note": 57, "sound": note_to_drum[57], "x": 50, "y": 50},
]

#Function to play sound when GUI button is pressed
def play_sound(sound):
    #Define a function to run the sound in a new thread
    def sound_thread():
        playsound.playsound(sound, block=False)

    #Create and start a new thread for each sound played
    threading.Thread(target=sound_thread).start()

#Function to handle MIDI input
def listen_for_midi():
    try:
        #Open MIDI input port to listen for signals
        with mido.open_input(keyboard) as port:
            for message in port:
                if message.type == 'note_on' and message.note in note_to_drum:
                    print(f"Received signal for MIDI note {message.note}, playing {note_to_drum} in response!")
                    #Play the corresponding sound using playsound in a separate thread
                    play_sound(note_to_drum[message.note])
    except KeyboardInterrupt:
        print("MIDI listening interrupted.")

#Create draggable buttons for the instruments
def make_draggable(widget):
    initial_x = 0
    initial_y = 0
    is_dragging = False
    
    #Checks to see if the mouse is gonna drag it or not
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

#Sample sound changing function >:)
def change_sample_sound(instrument):
    print(f"Attempting to change sound for {instrument['name']}...")
    file_path = filedialog.askopenfilename(title="Select a new sample")

    print(f"File selected: {file_path}")

    #Checking if the file path is valid (not empty or none)
    if file_path and file_path !="":
        note_to_drum[instrument["note"]] = file_path
        instrument["sound"] = file_path #Update the instrument's sound
        print(f"Updated sound for {instrument['name']} to {file_path}")
    else:
        print("No valid file selected")

#Generate positions for the instrument buttons
def position_generator(num_buttons, spacing=120):
    positions = []
    for i in range(num_buttons):
        x = 50 + (i % 5) * spacing
        y = 50 + (i // 5) * 100
        positions.append((x, y))
    return positions

#Function to show right-click menu for changing samples
def show_context_menu(event, instrument):
    context_menu = tk.Menu(app, tearoff=0)
    context_menu.add_command(label="Change Sound", command=lambda: change_sample_sound(instrument))
    context_menu.post(event.x_root, event.y_root) #Positions menu at the cursor


positions = position_generator(len(instruments))
 
for i, instrument in enumerate(instruments):
    button = ctk.CTkButton(
        app,
        text=instrument["name"],
        width=60,
        height=30,
        text_color="black",
        fg_color=("#6fa5fc", "#1970fc"), #Foreground colours, light and dark mode respectively 
        hover_color=("#19d6fc", "#6bffbc"), #Colours for the buttons when they get hovored, light and dark mode respectively
        corner_radius=16, #Round-i-ness of the buttons :p
        border_color=None,
        border_width=0,
        command=lambda instrument=instrument: play_sound(instrument["sound"]))
    
    #Open right click menu to change sample sounds, Button-2 for macOS users for no reason lol, Button-3 for normal people (make these macOS things smth you can change with a toggle!)
    button.bind("<Button-2>", lambda event, instrument=instrument: show_context_menu(event, instrument))


    #Give the buttons the positions that were generated from above
    x, y = positions[i]
    button.place(x=x, y=y)
    make_draggable(button)  # Making the buttons draggable, if that wasn't obvious

#Start the MIDI listening in a separate thread (commented out for when the bastard keyboard isn't plugged in)
#midi_thread = threading.Thread(target=listen_for_midi, daemon=True)
#midi_thread.start()


#Start the GUI loop
app.mainloop()
