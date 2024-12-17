import threading
import time
import json
import os
from pynput import mouse, keyboard
from pynput.keyboard import Key, KeyCode, Listener as KeyboardListener, Controller as KeyboardController
from pynput.mouse import Listener as MouseListener, Controller as MouseController
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk
from tkinter import font

# Constants for the unified stop hotkey
STOP_HOTKEY = {Key.esc}

# Directory to store recordings
RECORDINGS_DIR = "recordings"

# Path to the configuration file
CONFIG_FILE = "config.json"

# Ensure the recordings directory exists
if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)


class Recorder:
    def __init__(self):
        self.events = []
        self.start_time = None
        self.recording = False
        self.keyboard_listener = None
        self.mouse_listener = None

    def start(self):
        self.events = []
        self.start_time = time.time()
        self.recording = True

        self.keyboard_listener = KeyboardListener(on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener = MouseListener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)

        self.keyboard_listener.start()
        self.mouse_listener.start()

        print("Recording started...")

    def stop(self):
        self.recording = False
        if self.keyboard_listener is not None:
            self.keyboard_listener.stop()
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
        print("Recording stopped.")

    def on_press(self, key):
        if not self.recording:
            return
        if key in STOP_HOTKEY:
            # Don't record the stop hotkey
            return
        event = {
            'type': 'keyboard',
            'action': 'press',
            'key': self.get_key_name(key),
            'time': time.time() - self.start_time
        }
        self.events.append(event)
        print(f"Recorded Keyboard Press: {event}")

    def on_release(self, key):
        if not self.recording:
            return
        if key in STOP_HOTKEY:
            # Don't record the stop hotkey
            return
        event = {
            'type': 'keyboard',
            'action': 'release',
            'key': self.get_key_name(key),
            'time': time.time() - self.start_time
        }
        self.events.append(event)
        print(f"Recorded Keyboard Release: {event}")

    def on_move(self, x, y):
        if not self.recording:
            return
        event = {
            'type': 'mouse',
            'action': 'move',
            'position': (x, y),
            'time': time.time() - self.start_time
        }
        self.events.append(event)
        print(f"Recorded Mouse Move: {event}")

    def on_click(self, x, y, button, pressed):
        if not self.recording:
            return
        event = {
            'type': 'mouse',
            'action': 'click',
            'position': (x, y),
            'button': button.name,
            'pressed': pressed,
            'time': time.time() - self.start_time
        }
        self.events.append(event)
        action = "Pressed" if pressed else "Released"
        print(f"Recorded Mouse {action} Click: {event}")

    def on_scroll(self, x, y, dx, dy):
        if not self.recording:
            return
        event = {
            'type': 'mouse',
            'action': 'scroll',
            'position': (x, y),
            'scroll': (dx, dy),
            'time': time.time() - self.start_time
        }
        self.events.append(event)
        print(f"Recorded Mouse Scroll: {event}")

    def get_key_name(self, key):
        try:
            return key.char
        except AttributeError:
            return str(key)

    def save_events(self, name):
        # Sanitize the recording name
        safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).rstrip()
        if not safe_name:
            safe_name = f"recording_{int(time.time())}"
        filename = os.path.join(RECORDINGS_DIR, f"recording_{safe_name}.json")
        try:
            with open(filename, 'w') as f:
                json.dump(self.events, f, indent=4)
            print(f"Events saved to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving events: {e}")
            messagebox.showerror("Error", f"Failed to save events: {e}")
            return None

    def load_events(self, filename):
        try:
            with open(filename, 'r') as f:
                self.events = json.load(f)
            print(f"Events loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"No recorded events found. Please record actions first.")
            messagebox.showerror("Error", f"No recorded events found. Please record actions first.")
            return False
        except json.JSONDecodeError:
            print(f"Recorded events file is corrupted.")
            messagebox.showerror("Error", f"Recorded events file is corrupted.")
            return False
        except Exception as e:
            print(f"Error loading events: {e}")
            messagebox.showerror("Error", f"Failed to load events: {e}")
            return False


class Player:
    def __init__(self, events, loop=False, speed=1.0, progress_callback=None):
        self.events = events
        self.playing = False
        self.loop = loop
        self.speed = speed
        self.keyboard_controller = KeyboardController()
        self.mouse_controller = MouseController()
        self.play_thread = None
        self.progress_callback = progress_callback  # Callback to update progress bar

    def start(self):
        if not self.events:
            print("No events to play.")
            messagebox.showwarning("Warning", "No recorded events to play.")
            return
        self.playing = True
        self.play_thread = threading.Thread(target=self.play_loop, daemon=True)
        self.play_thread.start()
        print("Playback started...")
        if self.progress_callback:
            self.progress_callback(0)  # Initialize progress

    def stop(self):
        self.playing = False
        print("Playback stopped.")

    def play_loop(self):
        while self.playing:
            try:
                previous_time = 0
                total_time = self.events[-1]['time'] if self.events else 0
                print("Starting playback iteration...")
                for event in self.events:
                    if not self.playing:
                        print("Playback interrupted by user.")
                        break
                    delay = (event['time'] - previous_time) / self.speed
                    if delay > 0:
                        print(f"Sleeping for {delay:.4f} seconds before executing event.")
                        # Implement a shorter sleep interval to allow quicker interruption
                        start_sleep = time.time()
                        while time.time() - start_sleep < delay:
                            if not self.playing:
                                print("Playback interrupted during sleep.")
                                return
                            time.sleep(0.01)  # Sleep in small intervals to check for stop
                    else:
                        print(f"No delay needed before executing event: {event}")
                    self.execute_event(event)
                    previous_time = event['time']
                    # Update progress
                    if self.progress_callback and total_time > 0:
                        progress = (previous_time / total_time) * 100
                        self.progress_callback(progress)
                if self.loop and self.playing:
                    print("Completed one loop. Restarting playback...")
                else:
                    print("Completed playback without looping.")
                    self.playing = False  # Stop after one iteration if not looping
                    if self.progress_callback:
                        self.progress_callback(100)  # Ensure progress is complete
            except Exception as e:
                print(f"Error during playback: {e}")
                self.playing = False
                messagebox.showerror("Error", f"An error occurred during playback: {e}")

    def execute_event(self, event):
        try:
            if event['type'] == 'keyboard':
                key = self.parse_key(event['key'])
                if event['action'] == 'press':
                    self.keyboard_controller.press(key)
                    print(f"Executed Keyboard Press: {key}")
                elif event['action'] == 'release':
                    self.keyboard_controller.release(key)
                    print(f"Executed Keyboard Release: {key}")
            elif event['type'] == 'mouse':
                if event['action'] == 'move':
                    x, y = event['position']
                    self.mouse_controller.position = (x, y)
                    print(f"Executed Mouse Move to: ({x}, {y})")
                elif event['action'] == 'click':
                    x, y = event['position']
                    button = self.get_button(event['button'])
                    self.mouse_controller.position = (x, y)
                    if event['pressed']:
                        self.mouse_controller.press(button)
                        print(f"Executed Mouse Press: {button} at ({x}, {y})")
                    else:
                        self.mouse_controller.release(button)
                        print(f"Executed Mouse Release: {button} at ({x}, {y})")
                elif event['action'] == 'scroll':
                    dx, dy = event['scroll']
                    self.mouse_controller.scroll(dx, dy)
                    print(f"Executed Mouse Scroll: ({dx}, {dy})")
        except Exception as e:
            print(f"Error executing event {event}: {e}")
            raise e  # Re-raise exception to be caught in play_loop

    def parse_key(self, key_str):
        try:
            if len(key_str) == 1:
                return key_str
            else:
                # Remove 'Key.' prefix and get the attribute from Key
                key_attr = key_str.replace('Key.', '')
                return getattr(Key, key_attr)
        except AttributeError:
            print(f"Unknown key: {key_str}")
            return key_str

    def get_button(self, button_str):
        try:
            return getattr(mouse.Button, button_str)
        except AttributeError:
            print(f"Unknown mouse button: {button_str}")
            return mouse.Button.left  # Default to left button


class HotkeyListener:
    def __init__(self, callback, keys):
        self.callback = callback
        self.keys = keys
        self.current_keys = set()
        self.listener = KeyboardListener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        self.current_keys.add(key)
        if self.keys.issubset(self.current_keys):
            print("Hotkey pressed.")
            self.callback()

    def on_release(self, key):
        if key in self.current_keys:
            self.current_keys.remove(key)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoWiz")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")  # Light gray background for a modern look

        # Center the main window
        self.center_window(700, 700)

        self.recorder = Recorder()
        self.player = None
        self.stop_listener = None
        self.start_listener = None  # Listener for 'R' key
        self.compact_mode = False

        # Create frames that will be used in both modes
        self.regular_frame = tk.Frame(self, bg="#f0f0f0")
        self.regular_frame.pack(fill="both", expand=True)  # Pack the regular frame initially
        
        self.compact_frame = tk.Frame(self, bg="#f0f0f0")
        
        # Create compact mode widgets
        self.create_compact_widgets()
        
        # Initially hide compact frame
        self.compact_frame.pack_forget()

        self.create_widgets()
        # Bind 'R' key within the app's focus (optional redundancy)
        self.bind_all("<r>", self.handle_r_key)

        # Initialize HotkeyListeners
        self.init_hotkey_listeners()

        # Check configuration and show disclaimer if needed
        if not self.has_agreed_disclaimer():
            self.show_disclaimer()

        # Handle window closing to stop listeners
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self, width, height):
        """Centers the window on the screen."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def center_child_window(self, child_window, width, height):
        """Centers a child window relative to the main window."""
        self.update_idletasks()
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()

        x = main_x + (main_width // 2) - (width // 2)
        y = main_y + (main_height // 2) - (height // 2)
        child_window.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        # Create regular mode frame
        self.regular_frame = tk.Frame(self, bg="#f0f0f0")
        self.regular_frame.pack(fill="both", expand=True)
        
        # Create compact mode frame
        self.compact_frame = tk.Frame(self, bg="#f0f0f0")
        
        # Create regular mode widgets
        self.create_regular_widgets()
        
        # Create compact mode widgets
        self.create_compact_widgets()
        
        # Initially hide compact frame
        self.compact_frame.pack_forget()
        
        # Initialize status
        self.update_status("Idle", "blue")

    def create_compact_widgets(self):
        # Status frame (top)
        self.compact_status_frame = tk.Frame(self.compact_frame, bg="#f0f0f0")
        self.compact_status_frame.pack(fill="x", pady=(5, 5))
        
        # Create separate status indicator and label for compact mode
        self.compact_status_indicator = tk.Canvas(self.compact_status_frame, width=20, height=20, 
                                                highlightthickness=0, bg="#f0f0f0")
        self.compact_status_indicator.pack(side="left", padx=2)
        self.compact_status_circle = self.compact_status_indicator.create_oval(2, 2, 18, 18, fill="blue")
        
        self.compact_status_label = tk.Label(self.compact_status_frame, text="Idle", 
                                           font=("Helvetica", 12, "bold"), fg="blue", bg="#f0f0f0")
        self.compact_status_label.pack(side="left", padx=2)
        
        # Buttons frame (middle)
        self.compact_button_frame = tk.Frame(self.compact_frame, bg="#f0f0f0")
        self.compact_button_frame.pack(fill="x", pady=5)
        
        # Create separate buttons for compact mode
        self.compact_record_button = tk.Button(self.compact_button_frame, text="Record", 
                                             command=lambda: self.start_recording_and_update(), width=8, 
                                             bg="#e74c3c", fg="white", 
                                             font=("Helvetica", 10, "bold"))
        self.compact_record_button.pack(side="left", padx=2)
        
        self.compact_play_button = tk.Button(self.compact_button_frame, text="Play", 
                                           command=self.start_playback, width=8, 
                                           bg="#2ecc71", fg="white", 
                                           font=("Helvetica", 10, "bold"))
        self.compact_play_button.pack(side="left", padx=2)
        
        # Create stop button that handles both recording and playback
        self.compact_stop_button = tk.Button(self.compact_button_frame, text="Stop", 
                                           command=self.stop_current_action, width=8, 
                                           bg="#95a5a6", fg="white", 
                                           font=("Helvetica", 10, "bold"))
        self.compact_stop_button.pack(side="left", padx=2)
        self.compact_stop_button.config(state='disabled')
        
        # Regular mode button (bottom)
        self.compact_mode_button = tk.Button(self.compact_frame, text="Regular Mode", 
                                           command=self.toggle_compact_mode, width=15, 
                                           bg="#34495e", fg="white", 
                                           font=("Helvetica", 10, "bold"))
        self.compact_mode_button.pack(side="bottom", pady=5)

    def start_recording_and_update(self):
        """Wrapper method to ensure status is updated in compact mode."""
        self.start_recording()
        self.update_status("Recording", "#e74c3c")  # Force status update

    def create_regular_widgets(self):
        # Header Frame
        header_frame = tk.Frame(self.regular_frame, bg="#4a90e2")
        header_frame.pack(fill="x")
        header_label = tk.Label(header_frame, text="AutoWiz", font=("Helvetica", 24, "bold"), bg="#4a90e2", fg="white")
        header_label.pack(pady=10)

        # Frame for Recording Controls
        record_frame = tk.LabelFrame(self.regular_frame, text="Recording Controls", padx=10, pady=10, bg="#f0f0f0")
        record_frame.pack(padx=20, pady=10, fill="x")

        # Record Button
        self.record_button = tk.Button(record_frame, text="Record (R)", command=self.start_recording, width=20, height=2, bg="#e74c3c", fg="white", font=("Helvetica", 12, "bold"))
        self.record_button.pack(pady=5)

        # Play Button
        self.play_button = tk.Button(record_frame, text="Play", command=self.start_playback, width=20, height=2, bg="#2ecc71", fg="white", font=("Helvetica", 12, "bold"))
        self.play_button.pack(pady=5)

        # Stop Button - Updated to handle both recording and playback
        self.stop_button = tk.Button(record_frame, text="Stop", command=self.stop_current_action, 
                                   width=20, height=2, bg="#95a5a6", fg="white", 
                                   font=("Helvetica", 12, "bold"))
        self.stop_button.pack(pady=5)
        self.stop_button.config(state='disabled')  # Initially disabled

        # Loop Playback Checkbox
        self.loop_var = tk.BooleanVar()
        self.loop_var.set(True)  # Default to loop playback
        self.loop_checkbox = tk.Checkbutton(
            record_frame,
            text="Loop Playback",
            variable=self.loop_var,
            bg="#f0f0f0",
            font=("Helvetica", 10)
        )
        self.loop_checkbox.pack(pady=5)

        # Playback Speed Control
        speed_frame = tk.Frame(record_frame, bg="#f0f0f0")
        speed_frame.pack(pady=5, fill="x")
        speed_label = tk.Label(speed_frame, text="Playback Speed:", bg="#f0f0f0", font=("Helvetica", 10))
        speed_label.pack(side="left", padx=(0,10))
        self.speed_var = tk.DoubleVar()
        self.speed_var.set(1.0)  # Default speed
        self.speed_slider = tk.Scale(speed_frame, from_=0.5, to=2.0, resolution=0.1, orient='horizontal',
                                     variable=self.speed_var, bg="#f0f0f0", length=200)
        self.speed_slider.pack(side="left")

        # Frame for Recording Management
        manage_frame = tk.LabelFrame(self.regular_frame, text="Manage Recordings", padx=10, pady=10, bg="#f0f0f0")
        manage_frame.pack(padx=20, pady=10, fill="x")

        # Dropdown to select recordings
        recordings = self.get_all_recordings()
        self.selected_recording = tk.StringVar()
        if recordings and recordings[0] != "No Recordings":
            self.selected_recording.set(recordings[0])
        else:
            self.selected_recording.set("No Recordings")
        self.recording_dropdown = ttk.Combobox(manage_frame, textvariable=self.selected_recording, values=recordings, state='readonly', width=30)
        self.recording_dropdown.pack(pady=5)
        self.recording_dropdown.bind("<<ComboboxSelected>>", self.on_recording_selected)

        # Save Recording Button
        self.save_button = tk.Button(manage_frame, text="Save Recording", command=self.save_recording, width=20, bg="#3498db", fg="white", font=("Helvetica", 10, "bold"))
        self.save_button.pack(pady=5)

        # Load Recording Button
        self.load_button = tk.Button(manage_frame, text="Load Recording", command=self.load_recording, width=20, bg="#9b59b6", fg="white", font=("Helvetica", 10, "bold"))
        self.load_button.pack(pady=5)

        # Delete Recording Button
        self.delete_button = tk.Button(manage_frame, text="Delete Recording", command=self.delete_recording, width=20, bg="#e67e22", fg="white", font=("Helvetica", 10, "bold"))
        self.delete_button.pack(pady=5)

        # Frame for Additional Controls
        additional_frame = tk.Frame(self.regular_frame, bg="#f0f0f0")
        additional_frame.pack(padx=20, pady=10, fill="x")

        # Always on Top Checkbox
        self.always_on_top_var = tk.BooleanVar()
        self.always_on_top_var.set(False)
        self.always_on_top_checkbox = tk.Checkbutton(
            additional_frame,
            text="Always on Top",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
            bg="#f0f0f0",
            font=("Helvetica", 10)
        )
        self.always_on_top_checkbox.pack(side="left", padx=5)

        # Compact Mode Toggle Button
        self.compact_button = tk.Button(additional_frame, text="Compact Mode", command=self.toggle_compact_mode, width=15, bg="#34495e", fg="white", font=("Helvetica", 10, "bold"))
        self.compact_button.pack(side="left", padx=5)

        # Help Button
        self.help_button = tk.Button(additional_frame, text="Help", command=self.show_help, width=10, bg="#1abc9c", fg="white", font=("Helvetica", 10, "bold"))
        self.help_button.pack(side="right", padx=5)

        # About Button
        self.about_button = tk.Button(additional_frame, text="About", command=self.show_about, width=10, bg="#e74c3c", fg="white", font=("Helvetica", 10, "bold"))
        self.about_button.pack(side="right", padx=5)

        # Exit Button
        self.exit_button = tk.Button(additional_frame, text="Exit", command=self.on_closing, width=10, bg="#e74c3c", fg="white", font=("Helvetica", 10, "bold"))
        self.exit_button.pack(side="right", padx=5)

        # Status Label with Color-Coded Indicator
        status_frame = tk.Frame(self.regular_frame, bg="#f0f0f0")
        status_frame.pack(pady=10)
        self.status_indicator = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0, bg="#f0f0f0")
        self.status_indicator.pack(side="left", padx=(0, 10))
        self.status_circle = self.status_indicator.create_oval(2, 2, 18, 18, fill="blue")  # Default to Idle

        self.status_label = tk.Label(status_frame, text="Idle", font=("Helvetica", 14, "bold"), fg="blue", bg="#f0f0f0")
        self.status_label.pack(side="left")

        # Progress Bar
        self.progress = ttk.Progressbar(self.regular_frame, orient='horizontal', length=600, mode='determinate')
        self.progress.pack(pady=10)

        # Instructions Label
        instructions = (
            "Instructions:\n"
            "- Click 'Record' or press 'R' to start recording actions.\n"
            "- Perform desired actions.\n"
            "- Press ESC to stop recording.\n"
            "- After stopping, you can play back the recording before saving.\n"
            "- To save the recording, click 'Save Recording'.\n"
            "- Select a recording from the dropdown and click 'Play' to start playback.\n"
            "- Adjust 'Playback Speed' as needed.\n"
            "- Playback will loop based on the 'Loop Playback' option and can be stopped by pressing ESC.\n"
            "- Use 'Delete Recording' to remove unwanted recordings.\n"
            "- Toggle 'Compact Mode' to simplify the UI.\n"
            "- Click 'Exit' or the X button to close the application."
        )
        self.instructions_label = tk.Label(self.regular_frame, text=instructions, justify="left", padx=20, pady=10, bg="#f0f0f0", font=("Helvetica", 10))
        self.instructions_label.pack(pady=10)

    def get_all_recordings(self):
        try:
            files = os.listdir(RECORDINGS_DIR)
            recordings = [f.replace("recording_", "").replace(".json", "") for f in files if f.startswith("recording_") and f.endswith(".json")]
            if not recordings:
                return ["No Recordings"]
            return recordings
        except Exception as e:
            print(f"Error accessing recordings directory: {e}")
            messagebox.showerror("Error", f"Error accessing recordings directory: {e}")
            return ["No Recordings"]

    def refresh_recordings(self):
        recordings = self.get_all_recordings()
        if recordings and recordings[0] != "No Recordings":
            self.recording_dropdown['values'] = recordings
            if self.selected_recording.get() not in recordings:
                self.selected_recording.set(recordings[0])
        else:
            self.recording_dropdown['values'] = ["No Recordings"]
            self.selected_recording.set("No Recordings")

    def on_recording_selected(self, event):
        selected = self.selected_recording.get()
        if selected == "No Recordings":
            return
        print(f"Selected Recording: {selected}")

    def save_recording(self):
        if not self.recorder.events:
            messagebox.showwarning("Warning", "No events to save. Please record actions first.")
            return
            
        # Temporarily stop hotkey listeners
        if hasattr(self, 'stop_listener') and self.stop_listener and hasattr(self.stop_listener, 'listener'):
            self.stop_listener.listener.stop()
        if hasattr(self, 'start_listener') and self.start_listener and hasattr(self.start_listener, 'listener'):
            self.start_listener.listener.stop()
            
        # Prompt user for a recording name
        name = simpledialog.askstring("Save Recording", "Enter a name for the recording:")
        
        # Restart hotkey listeners
        if not self.recorder.recording and not (self.player and self.player.playing):
            # Only restart listeners if we're not recording or playing
            self.stop_listener = HotkeyListener(self.stop_current_action, STOP_HOTKEY)
            START_HOTKEY = {KeyCode.from_char('r')}
            self.start_listener = HotkeyListener(self.start_recording_if_idle, START_HOTKEY)
            
        if name:
            # Sanitize and check for duplicates
            safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).rstrip()
            if not safe_name:
                safe_name = f"recording_{int(time.time())}"
            filename = os.path.join(RECORDINGS_DIR, f"recording_{safe_name}.json")
            if os.path.exists(filename):
                overwrite = messagebox.askyesno("Overwrite Recording", f"A recording named '{safe_name}' already exists. Do you want to overwrite it?")
                if not overwrite:
                    return  # Exit without saving
            # Proceed to save
            saved_filename = self.recorder.save_events(safe_name)
            if saved_filename:
                messagebox.showinfo("Success", f"Recording saved as '{safe_name}'.")
                self.refresh_recordings()
        else:
            messagebox.showwarning("Warning", "Recording not saved. No name provided.")

    def load_recording(self):
        selected = self.selected_recording.get()
        if selected == "No Recordings":
            messagebox.showwarning("Warning", "No recordings available to load.")
            return
        filename = os.path.join(RECORDINGS_DIR, f"recording_{selected}.json")
        success = self.recorder.load_events(filename)
        if success:
            messagebox.showinfo("Success", f"Recording '{selected}' loaded successfully.")

    def delete_recording(self):
        selected = self.selected_recording.get()
        if selected == "No Recordings":
            messagebox.showwarning("Warning", "No recordings available to delete.")
            return
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the recording '{selected}'?")
        if confirm:
            filename = os.path.join(RECORDINGS_DIR, f"recording_{selected}.json")
            try:
                os.remove(filename)
                messagebox.showinfo("Deleted", f"Recording '{selected}' has been deleted.")
                self.refresh_recordings()
            except Exception as e:
                print(f"Error deleting recording: {e}")
                messagebox.showerror("Error", f"Failed to delete recording '{selected}': {e}")

    def toggle_always_on_top(self):
        self.attributes("-topmost", self.always_on_top_var.get())
        print(f"Always on Top set to {self.always_on_top_var.get()}")

    def toggle_compact_mode(self):
        self.compact_mode = not self.compact_mode
        if self.compact_mode:
            # Hide regular frame
            self.regular_frame.pack_forget()
            
            # Show compact frame
            self.compact_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Set minimal window size
            self.geometry("300x120")
            
            # Get current status from regular mode
            current_status = self.status_label.cget("text")
            current_color = self.status_label.cget("fg")
            
            # Update compact mode with current status
            self.update_status(current_status, current_color)
            
        else:
            # Hide compact frame
            self.compact_frame.pack_forget()
            
            # Show regular frame
            self.regular_frame.pack(fill="both", expand=True)
            
            # Get current status from compact mode
            current_status = self.compact_status_label.cget("text")
            current_color = self.compact_status_label.cget("fg")
            
            # Update regular mode with current status
            self.update_status(current_status, current_color)
            
            # Resize window back to original size
            self.center_window(700, 700)

    def update_status(self, state, color):
        """Update status in both regular and compact modes."""
        # Update regular mode status
        if hasattr(self, 'status_label'):
            self.status_label.config(text=state, fg=color)
            self.status_indicator.itemconfig(self.status_circle, fill=color)
        
        # Update compact mode status
        if hasattr(self, 'compact_status_label'):
            self.compact_status_label.config(text=state, fg=color)
            self.compact_status_indicator.itemconfig(self.compact_status_circle, fill=color)
            
        # Update button states based on status
        self.update_button_states(state)
        
    def update_button_states(self, state):
        """Update button states in both modes based on current status."""
        if state == "Recording":
            # Regular mode buttons
            if hasattr(self, 'record_button'):
                self.record_button.config(bg="#c0392b")
                self.play_button.config(state='disabled')
                self.save_button.config(state='disabled')
                self.load_button.config(state='disabled')
                self.delete_button.config(state='disabled')
                self.stop_button.config(state='normal', text="Stop Recording")
            
            # Compact mode buttons
            if hasattr(self, 'compact_record_button'):
                self.compact_record_button.config(bg="#c0392b")
                self.compact_play_button.config(state='disabled')
                self.compact_stop_button.config(state='normal')
                
        elif state == "Playing":
            # Regular mode buttons
            if hasattr(self, 'record_button'):
                self.record_button.config(state='disabled')
                self.play_button.config(bg="#27ae60")
                self.save_button.config(state='disabled')
                self.load_button.config(state='disabled')
                self.delete_button.config(state='disabled')
                self.stop_button.config(state='normal', text="Stop Playback")
            
            # Compact mode buttons
            if hasattr(self, 'compact_record_button'):
                self.compact_record_button.config(state='disabled')
                self.compact_play_button.config(bg="#27ae60")
                self.compact_stop_button.config(state='normal')
                
        elif state == "Ready to Preview":
            # Regular mode buttons
            if hasattr(self, 'record_button'):
                self.record_button.config(bg="#e74c3c", state='normal')
                self.play_button.config(state='normal', text="Preview Recording", bg="#2ecc71")
                self.save_button.config(state='normal')
                self.load_button.config(state='disabled')
                self.delete_button.config(state='disabled')
                self.stop_button.config(state='disabled', text="Stop")
            
            # Compact mode buttons
            if hasattr(self, 'compact_record_button'):
                self.compact_record_button.config(bg="#e74c3c", state='normal')
                self.compact_play_button.config(state='normal', text="Preview")
                self.compact_stop_button.config(state='disabled')
                
        else:  # Idle state
            # Regular mode buttons
            if hasattr(self, 'record_button'):
                self.record_button.config(bg="#e74c3c", state='normal')
                self.play_button.config(state='normal', text="Play", bg="#2ecc71")
                self.save_button.config(state='normal')
                self.load_button.config(state='normal')
                self.delete_button.config(state='normal')
                self.stop_button.config(state='disabled', text="Stop")
            
            # Compact mode buttons
            if hasattr(self, 'compact_record_button'):
                self.compact_record_button.config(bg="#e74c3c", state='normal')
                self.compact_play_button.config(state='normal', text="Play", bg="#2ecc71")
                self.compact_stop_button.config(state='disabled')

    def sync_status_to_compact(self):
        # Sync the status from regular mode to compact mode
        current_status = self.status_label.cget("text")
        current_color = self.status_label.cget("fg")
        self.compact_status_label.config(text=current_status, fg=current_color)
        self.compact_status_indicator.itemconfig(self.compact_status_circle, fill=current_color)

    def show_help(self):
        help_window = tk.Toplevel(self)
        help_window.title("Help - AutoWiz")
        help_window.geometry("600x500")  # Increased size to prevent text cutoff
        help_window.configure(bg="#f0f0f0")
        # Center the help window
        self.center_child_window(help_window, 600, 500)
        help_window.transient(self)
        help_window.grab_set()

        # Create a frame with padding for content
        content_frame = tk.Frame(help_window, bg="#f0f0f0", padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)

        help_label = tk.Label(content_frame, text="AutoWiz Help", font=("Helvetica", 16, "bold"), bg="#f0f0f0")
        help_label.pack(pady=(0, 10))
        
        # Create a frame for the scrollable text
        text_frame = tk.Frame(content_frame, bg="#f0f0f0")
        text_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        help_text = (
            "AutoWiz is an automation tool that allows you to record and playback keyboard and mouse actions.\n\n"
            "Features:\n"
            "- Record Actions: Click 'Record' or press 'R' to start recording your keyboard and mouse actions.\n"
            "- Stop Recording: Press ESC to stop recording.\n"
            "- Review Recording: After stopping, playback your recording without saving to ensure it performs as expected.\n"
            "- Save Recording: Click 'Save Recording' to save your recorded actions for future use.\n"
            "- Playback Recording: Select a recording from the dropdown and click 'Play' to execute the actions.\n"
            "- Playback Speed: Adjust the playback speed using the slider.\n"
            "- Loop Playback: Enable or disable looping of the playback.\n"
            "- Manage Recordings: Load, delete, and organize your recordings.\n"
            "- Compact Mode: Toggle compact mode to simplify the UI.\n\n"
            "Controls:\n"
            "- R Key: Start recording.\n"
            "- ESC Key: Stop recording or playback.\n\n"
            "Please ensure that AutoWiz has the necessary permissions to control your keyboard and mouse."
        )
        
        # Add text widget with scrollbar
        text_widget = tk.Text(text_frame, wrap="word", bg="#f0f0f0", font=("Helvetica", 10), 
                            width=50, height=15, padx=10, pady=10)
        scrollbar = tk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        text_widget.insert("1.0", help_text)
        text_widget.configure(state="disabled")  # Make text read-only

        # Add Okay button
        ok_button = tk.Button(content_frame, text="Okay", command=help_window.destroy,
                            width=10, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        ok_button.pack(pady=(0, 10))

    def show_about(self):
        about_window = tk.Toplevel(self)
        about_window.title("About - AutoWiz")
        about_window.geometry("400x350")  # Increased height to accommodate button
        about_window.configure(bg="#f0f0f0")
        # Center the about window
        self.center_child_window(about_window, 400, 350)
        about_window.transient(self)
        about_window.grab_set()

        # Create a frame with padding for content
        content_frame = tk.Frame(about_window, bg="#f0f0f0", padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)

        about_label = tk.Label(content_frame, text="About AutoWiz", font=("Helvetica", 16, "bold"), bg="#f0f0f0")
        about_label.pack(pady=(0, 10))
        
        about_text = (
            "AutoWiz v1.0\n\n"
            "AutoWiz is a powerful automation tool designed to record and playback keyboard and mouse actions.\n\n"
            "Developed by: TechRay Apps LLC\n"
            "Contact: support@techray.dev\n\n"
            "© 2024 AutoWiz. All rights reserved."
        )
        about_label = tk.Label(content_frame, text=about_text, justify="center", bg="#f0f0f0", 
                             font=("Helvetica", 10), wraplength=360)
        about_label.pack(pady=(0, 20))

        # Add Okay button
        ok_button = tk.Button(content_frame, text="Okay", command=about_window.destroy,
                            width=10, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        ok_button.pack(pady=(0, 10))

    def show_disclaimer(self):
        """Show the disclaimer window if not already agreed."""
        disclaimer_window = tk.Toplevel(self)
        disclaimer_window.title("Disclaimer - AutoWiz")
        disclaimer_window.geometry("700x500")  # Increased size
        disclaimer_window.configure(bg="#ffffff")
        disclaimer_window.transient(self)  # Set to be on top of the main window
        disclaimer_window.grab_set()  # Make it modal
        self.center_child_window(disclaimer_window, 700, 500)

        # Create main content frame with padding
        content_frame = tk.Frame(disclaimer_window, bg="#ffffff", padx=40, pady=30)
        content_frame.pack(fill="both", expand=True)

        # Header
        header_font = font.Font(family="Helvetica", size=18, weight="bold")
        disclaimer_label = tk.Label(content_frame, text="Disclaimer", font=header_font, bg="#ffffff", fg="#333333")
        disclaimer_label.pack(pady=(0, 20))

        # Disclaimer Text
        text_font = font.Font(family="Helvetica", size=11)
        disclaimer_text = (
            "By using AutoWiz, you agree to the following terms:\n\n"
            "1. Responsibility: You are solely responsible for how you use this tool.\n\n"
            "2. Compliance: Ensure that your use of AutoWiz complies with all applicable laws and regulations.\n\n"
            "3. Ethical Use: Do not use AutoWiz for malicious purposes, such as automating actions to deceive or harm others.\n\n"
            "4. Permissions: Ensure that AutoWiz has the necessary permissions to control your keyboard and mouse.\n\n"
            "Do you agree to these terms?"
        )
        
        # Create Text widget for better text display
        text_widget = tk.Text(content_frame, wrap="word", bg="#ffffff", fg="#333333", 
                            font=text_font, width=50, height=12, relief="flat",
                            padx=20, pady=20)
        text_widget.insert("1.0", disclaimer_text)
        text_widget.configure(state="disabled")  # Make text read-only
        text_widget.pack(fill="both", expand=True, pady=(0, 20))

        # Buttons frame with padding
        button_frame = tk.Frame(content_frame, bg="#ffffff")
        button_frame.pack(pady=(0, 20))

        # Style buttons
        button_font = font.Font(family="Helvetica", size=10, weight="bold")
        agree_button = tk.Button(
            button_frame,
            text="I Agree",
            command=lambda: self.agree_disclaimer(disclaimer_window),
            width=15,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=button_font,
            cursor="hand2"
        )
        agree_button.pack(side="left", padx=20)

        decline_button = tk.Button(
            button_frame,
            text="I Decline",
            command=self.decline_disclaimer,
            width=15,
            height=2,
            bg="#f44336",
            fg="white",
            font=button_font,
            cursor="hand2"
        )
        decline_button.pack(side="left", padx=20)

    def agree_disclaimer(self, window):
        self.set_disclaimer_agreed()
        window.destroy()

    def decline_disclaimer(self):
        messagebox.showinfo("Declined", "You have declined the terms. AutoWiz will now exit.")
        self.destroy()

    def has_agreed_disclaimer(self):
        """Check if the user has already agreed to the disclaimer."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                return config.get("agreed_disclaimer", False)
            except Exception as e:
                print(f"Error reading config file: {e}")
                return False
        return False

    def set_disclaimer_agreed(self):
        """Set the disclaimer as agreed in the config file."""
        config = {"agreed_disclaimer": True}
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            print("Disclaimer agreement saved.")
        except Exception as e:
            print(f"Error writing to config file: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def handle_r_key(self, event):
        # This method is bound to the 'R' key within the app's focus
        # It's redundant with the global HotkeyListener but kept for completeness
        pass  # No action needed as we use HotkeyListener

    def init_hotkey_listeners(self):
        # Initialize HotkeyListener for stopping (ESC key)
        self.stop_listener = HotkeyListener(self.stop_current_action, STOP_HOTKEY)
        # Initialize HotkeyListener for starting recording ('r' key)
        START_HOTKEY = {KeyCode.from_char('r')}
        self.start_listener = HotkeyListener(self.start_recording_if_idle, START_HOTKEY)

    def start_recording_if_idle(self):
        if not self.recorder.recording and (not self.player or not self.player.playing):
            # Schedule the recording to start in the main thread
            self.after(0, self.start_recording)
            # Immediately update status to ensure UI responsiveness
            self.after(0, lambda: self.update_status("Recording", "#e74c3c"))
        else:
            print("Cannot start recording. App is not idle.")

    def start_recording(self):
        if self.recorder.recording:
            messagebox.showwarning("Warning", "Already recording.")
            return
        # Ensure that playback is not active
        if self.player and self.player.playing:
            messagebox.showwarning("Warning", "Cannot start recording while playback is active.")
            return
            
        self.recorder.start()
        # Update status first to ensure both modes are synchronized
        self.update_status("Recording", "#e74c3c")  # Red color
        print("Recording started from GUI.")
        
        # Set up hotkey to stop recording
        if self.stop_listener:
            self.stop_listener.listener.stop()
        self.stop_listener = HotkeyListener(self.stop_current_action, STOP_HOTKEY)

    def stop_recording(self):
        if self.recorder.recording:
            self.recorder.stop()
            # Use update_status to handle all UI updates
            self.update_status("Ready to Preview", "#f39c12")  # Orange color to indicate preview state
            print("Recording stopped. Ready for preview.")
            
        # Stop the hotkey listener
        if self.stop_listener:
            self.stop_listener.listener.stop()
            self.stop_listener = None

    def start_playback(self):
        if self.recorder.recording:
            messagebox.showwarning("Warning", "Cannot play while recording.")
            return
        if self.player and self.player.playing:
            messagebox.showwarning("Warning", "Playback is already running.")
            return

        # Check if we're playing a saved recording or previewing
        if not self.recorder.events:  # If no events in memory, load from file
            selected = self.selected_recording.get()
            if selected == "No Recordings":
                messagebox.showwarning("Warning", "No recordings available to play.")
                return
            filename = os.path.join(RECORDINGS_DIR, f"recording_{selected}.json")
            success = self.recorder.load_events(filename)
            if not success:
                return

        loop = self.loop_var.get()
        speed = self.speed_var.get()
        self.player = Player(self.recorder.events, loop=loop, speed=speed, progress_callback=self.update_progress)
        self.player.start()
        self.update_status("Playing", "#2ecc71")  # Green color
        print(f"Playback started with loop={'On' if loop else 'Off'}, speed={speed}x.")
        
        # Update regular mode buttons
        self.play_button.config(bg="#27ae60", text="Play")  # Reset text back to "Play"
        self.record_button.config(state='disabled')
        self.save_button.config(state='disabled')  # Disable save during playback
        self.load_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.stop_button.config(state='normal', text="Stop Playback")
        
        # Update compact mode buttons
        self.compact_play_button.config(bg="#27ae60", text="Play")  # Reset text back to "Play"
        self.compact_record_button.config(state='disabled')
        self.compact_stop_button.config(state='normal')
        
        # Set up hotkey to stop playback
        if self.stop_listener:
            self.stop_listener.listener.stop()
        self.stop_listener = HotkeyListener(self.stop_current_action, STOP_HOTKEY)

    def stop_playback(self):
        if self.player and self.player.playing:
            self.player.stop()
            self.update_status("Idle", "blue")
            print("Playback stopped.")
            
            # Update regular mode buttons
            self.play_button.config(bg="#2ecc71", text="Play")
            self.record_button.config(state='normal')
            
            # If there are unsaved events in memory, enable save button and show message
            if self.recorder.events:
                self.save_button.config(state='normal')
                self.load_button.config(state='disabled')  # Keep load disabled until saved or cleared
                self.delete_button.config(state='disabled')  # Keep delete disabled until saved or cleared
                messagebox.showinfo("Preview Complete", "You can now save the recording if desired, or record a new one.")
            else:
                self.save_button.config(state='normal')
                self.load_button.config(state='normal')
                self.delete_button.config(state='normal')
            
            self.stop_button.config(state='disabled', text="Stop")
            
            # Update compact mode buttons
            self.compact_play_button.config(bg="#2ecc71", text="Play")
            self.compact_record_button.config(state='normal')
            self.compact_stop_button.config(state='disabled')
            
        # Stop the hotkey listener
        if self.stop_listener:
            self.stop_listener.listener.stop()
            self.stop_listener = None

    def update_progress(self, value):
        self.progress['value'] = value

    def on_closing(self):
        # Stop all listeners before closing
        if self.recorder.recording:
            self.recorder.stop()
        if self.player and self.player.playing:
            self.player.stop()
        if self.stop_listener:
            self.stop_listener.listener.stop()
        if self.start_listener:
            self.start_listener.listener.stop()
        self.destroy()

    def stop_current_action(self):
        """Unified method to stop either recording or playback."""
        if self.recorder.recording:
            self.stop_recording()
        elif self.player and self.player.playing:
            self.stop_playback()


def main():
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
