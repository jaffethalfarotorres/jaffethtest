# IBM Presentation Timer
# Created by Jaffeth Alfaro Torres - Jaffeth.Alfaro@ibm.com
# Using playsound module for audio playback

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import sys
import webbrowser
from playsound import playsound
import threading

# Constants
BG_COLOR = "#1E1E1E"  # Dark gray background
FG_COLOR = "#FFFFFF"  # White text
BUTTON_BG_COLOR = "#2E2E2E"  # Slightly lighter gray for buttons
BUTTON_FG_COLOR = "#FFFFFF"  # White text for buttons
BUTTON_OUTLINE_COLOR = "#7F3FBF"  # Purple outline for buttons
FONT_NAME = "Arial Black"
DEFAULT_FONT_SIZE = 20
FLASH_COLOR = "#0530AD"  # Light blue for flashing
FLASH_THRESHOLD = 10  # Flash timer when 10 seconds remain

def resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Use the directory of the script as the base path
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Sound options
SOUND_OPTIONS = {
    "Sound1": resource_path("sounds/Sound1.wav"),
    "Sound2": resource_path("sounds/Sound2.wav"),
}

class PresentationTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("IBM Presentation Timer")
        self.root.geometry("300x200")
        self.root.attributes('-topmost', True)
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # Initialize variables
        self.time_left = 0
        self.running = False
        self.agenda = []
        self.current_agenda = 0
        self.font_size = DEFAULT_FONT_SIZE
        self.font = (FONT_NAME, self.font_size)
        self.sound_playing = False

        # Verify sound files at startup
        self.verify_sound_files()

        # Allow window dragging
        self.dragging = False
        self.dragging_item = False
        self.offset_x = 0
        self.offset_y = 0
        self.root.bind("<Button-1>", self.on_press)
        self.root.bind("<B1-Motion>", self.on_drag)
        
        # Create UI
        self.create_widgets()
        
        # Start update thread
        self.update_timer()

    def verify_sound_files(self):
        """Check if sound files exist at startup."""
        for name, path in SOUND_OPTIONS.items():
            if not os.path.exists(path):
                messagebox.showwarning(
                    "Missing Sound File",
                    f"Sound file not found: {path}\n"
                    f"Sound '{name}' will not work."
                )

    def create_widgets(self):
        """Create and arrange all UI widgets."""
        # Timer display
        self.timer_label = tk.Label(self.root, text="00:00", font=self.font, fg=FG_COLOR, bg=BG_COLOR)
        self.timer_label.pack(pady=10)
        
        # Agenda display
        self.agenda_label = tk.Label(self.root, text="No Agenda Items", font=(FONT_NAME, 12), fg=FG_COLOR, bg=BG_COLOR)
        self.agenda_label.pack()
        
        # Control buttons
        self.button_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.button_frame.pack(pady=5)
        
        self.toggle_button = self.create_rounded_button(
            self.button_frame, 
            text="Expand", 
            command=self.toggle_options
        )
        self.toggle_button.pack(side=tk.LEFT, padx=5)
        
        self.toggle_timer_btn = self.create_rounded_button(
            self.button_frame, 
            text="Start", 
            command=self.toggle_timer
        )
        self.toggle_timer_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = self.create_rounded_button(
            self.button_frame, 
            text="Reset", 
            command=self.reset_timer
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Agenda controls
        self.controls_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.controls_frame.pack()
        
        self.agenda_listbox = tk.Listbox(self.controls_frame, height=5, bg=BG_COLOR, fg=FG_COLOR, borderwidth=0)
        self.agenda_listbox.pack()
        
        # Bind events
        self.agenda_listbox.bind("<Button-1>", self.on_item_press)
        self.agenda_listbox.bind("<B1-Motion>", self.on_item_drag)
        self.agenda_listbox.bind("<ButtonRelease-1>", self.on_item_release)
        self.agenda_listbox.bind("<Double-Button-1>", self.on_agenda_item_double_click)
        
        # Bottom buttons
        self.bottom_button_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.bottom_button_frame.pack(pady=5)
        
        self.add_agenda_btn = self.create_rounded_button(
            self.bottom_button_frame, 
            text="Add", 
            command=self.add_agenda_item, 
            width=8
        )
        self.add_agenda_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_agenda_btn = self.create_rounded_button(
            self.bottom_button_frame, 
            text="Delete", 
            command=self.delete_agenda_item, 
            width=8
        )
        self.delete_agenda_btn.pack(side=tk.LEFT, padx=5)
        
        self.increase_font_btn = self.create_rounded_button(
            self.bottom_button_frame, 
            text="Increase", 
            command=self.increase_font_size, 
            width=8
        )
        self.increase_font_btn.pack(side=tk.LEFT, padx=5)
        
        self.decrease_font_btn = self.create_rounded_button(
            self.bottom_button_frame, 
            text="Decrease", 
            command=self.decrease_font_size, 
            width=8
        )
        self.decrease_font_btn.pack(side=tk.LEFT, padx=5)
        
        # Info button
        self.info_button = self.create_rounded_button(
            self.root, 
            text="i", 
            command=self.show_info,
            width=2
        )
        self.info_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)

    def create_rounded_button(self, parent, text, command, width=None):
        """Create a rounded button with a modern style."""
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=BUTTON_BG_COLOR,
            fg=BUTTON_FG_COLOR,
            font=(FONT_NAME, 10),
            borderwidth=2,
            relief=tk.FLAT,
            highlightbackground=BUTTON_OUTLINE_COLOR,
            highlightthickness=2,
            width=width
        )

    def play_sound(self, sound_key):
        """Play sound using playsound in a non-blocking way."""
        if self.sound_playing:
            return
            
        sound = SOUND_OPTIONS.get(sound_key)
        if sound:
            try:
                self.sound_playing = True
                # Check if file exists
                if not os.path.exists(sound):
                    raise FileNotFoundError(f"Sound file not found: {sound}")
                
                # Use a thread to prevent UI blocking
                def play():
                    try:
                        playsound(sound, block=True)
                    except Exception as e:
                        print(f"Error playing sound: {e}")
                        self.root.bell()
                    finally:
                        self.sound_playing = False
                
                threading.Thread(target=play, daemon=True).start()
                
            except Exception as e:
                print(f"Sound error: {e}")
                self.sound_playing = False
                self.root.bell()  # Fallback to system bell

    def update_timer(self):
        """Update the timer every second with sound handling."""
        if self.running and self.time_left > 0:
            self.time_left -= 1
            self.timer_label.config(text=self.format_time(self.time_left))
            
            # Play sounds at specific thresholds
            if self.time_left == 10:
                self.play_sound("Sound1")
            
            if self.time_left == 0:
                self.play_sound("Sound2")
                if self.current_agenda < len(self.agenda) - 1:
                    self.current_agenda += 1
                    self.time_left = self.agenda[self.current_agenda][1]
                    self.agenda_label.config(text=self.agenda[self.current_agenda][0])
            elif self.time_left <= FLASH_THRESHOLD:
                current_color = self.timer_label.cget("fg")
                new_color = FLASH_COLOR if current_color != FLASH_COLOR else FG_COLOR
                self.timer_label.config(fg=new_color)
        
        self.root.after(1000, self.update_timer)

    def on_press(self, event):
        """Handle mouse press event for window dragging."""
        if not self.dragging_item:
            self.dragging = True
            self.offset_x = event.x
            self.offset_y = event.y

    def on_drag(self, event):
        """Handle mouse drag event for window dragging."""
        if self.dragging and not self.dragging_item:
            x = self.root.winfo_x() - self.offset_x + event.x
            y = self.root.winfo_y() - self.offset_y + event.y
            self.root.geometry(f"+{x}+{y}")
    
    def on_item_press(self, event):
        """Handle mouse press event for agenda item dragging."""
        self.dragging_item = True
        self.dragged_item_index = self.agenda_listbox.nearest(event.y)
    
    def on_item_drag(self, event):
        """Handle mouse drag event for agenda item dragging."""
        if self.dragging_item:
            new_index = self.agenda_listbox.nearest(event.y)
            if new_index != self.dragged_item_index:
                # Swap items in the agenda list
                self.agenda[self.dragged_item_index], self.agenda[new_index] = (
                    self.agenda[new_index], self.agenda[self.dragged_item_index]
                )
                # Refresh the Listbox
                self.refresh_agenda()
                # Update the dragged item index
                self.dragged_item_index = new_index
    
    def on_item_release(self, event):
        """Handle mouse release event for agenda item dragging."""
        self.dragging_item = False
        self.reset_agenda()

    def format_time(self, seconds):
        """Format seconds into MM:SS."""
        mins, secs = divmod(seconds, 60)
        return f"{mins:02}:{secs:02}"

    def toggle_timer(self):
        """Start or pause the timer."""
        if self.running:
            self.running = False
            self.toggle_timer_btn.config(text="Start")
        else:
            if not self.agenda:
                messagebox.showinfo("No Agenda Items", "Please add an agenda item first.")
                return
            self.running = True
            self.toggle_timer_btn.config(text="Pause")
            if self.time_left == 0 or self.current_agenda >= len(self.agenda):
                self.current_agenda = 0
                self.time_left = self.agenda[self.current_agenda][1]
                self.agenda_label.config(text=self.agenda[self.current_agenda][0])

    def add_agenda_item(self):
        """Add a new agenda item (topic and time)."""
        agenda_topic = simpledialog.askstring("Agenda Item", "Enter agenda item:")
        if not agenda_topic:
            return

        agenda_time = simpledialog.askinteger("Agenda Time", "Enter time for this item (minutes):")
        if not agenda_time or agenda_time <= 0:
            messagebox.showerror("Invalid Input", "Please provide a valid time (greater than 0).")
            return

        self.agenda.append((agenda_topic, agenda_time * 60))
        self.agenda_listbox.insert(tk.END, f"{agenda_topic} - {agenda_time} min")
        if len(self.agenda) == 1:
            self.reset_agenda()
    
    def delete_agenda_item(self):
        """Delete the selected agenda item."""
        selected_index = self.agenda_listbox.curselection()
        if not selected_index:
            messagebox.showinfo("No Selection", "Please select an agenda item to delete.")
            return
        
        index = selected_index[0]
        del self.agenda[index]
        self.refresh_agenda()
        self.reset_agenda()
        messagebox.showinfo("Success", "Agenda item deleted.")
    
    def refresh_agenda(self):
        """Refresh the agenda listbox."""
        self.agenda_listbox.delete(0, tk.END)
        for topic, time_seconds in self.agenda:
            self.agenda_listbox.insert(tk.END, f"{topic} - {time_seconds // 60} min")
    
    def toggle_options(self):
        """Expand or collapse additional controls."""
        if self.controls_frame.winfo_ismapped():
            self.controls_frame.pack_forget()
            self.bottom_button_frame.pack_forget()
            self.toggle_button.config(text="Expand")
        else:
            self.controls_frame.pack()
            self.bottom_button_frame.pack()
            self.toggle_button.config(text="Collapse")
        self.auto_resize()
    
    def auto_resize(self):
        """Resize the window to fit its contents."""
        self.root.geometry("")

    def on_agenda_item_double_click(self, event):
        """Edit the selected agenda item on double-click."""
        selected_index = self.agenda_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            agenda_topic, agenda_time = self.agenda[index]
            new_topic = simpledialog.askstring("Edit Agenda Item", "Enter new item:", initialvalue=agenda_topic)
            new_time = simpledialog.askinteger("Edit Agenda Item", "Enter new time (minutes):", initialvalue=agenda_time // 60)
            if new_topic and new_time:
                self.agenda[index] = (new_topic, new_time * 60)
                self.refresh_agenda()
                if self.current_agenda == index:
                    self.time_left = new_time * 60
                    self.timer_label.config(text=self.format_time(self.time_left))
                    self.agenda_label.config(text=new_topic)
                    if self.running:
                        self.running = False
                        self.toggle_timer_btn.config(text="Start")

    def reset_timer(self):
        """Reset the timer without deleting the agenda items."""
        self.running = False
        self.toggle_timer_btn.config(text="Start")
        self.time_left = 0
        self.current_agenda = 0
        if self.agenda:
            self.agenda_label.config(text=self.agenda[self.current_agenda][0])
        else:
            self.agenda_label.config(text="No Agenda Items")
        self.timer_label.config(text="00:00")

    def reset_agenda(self):
        """Reset the timer to the first agenda item."""
        self.current_agenda = 0
        if self.agenda:
            self.time_left = self.agenda[self.current_agenda][1]
            self.agenda_label.config(text=self.agenda[self.current_agenda][0])
        else:
            self.time_left = 0
            self.agenda_label.config(text="No Agenda Items")
        self.timer_label.config(text=self.format_time(self.time_left))

    def increase_font_size(self):
        """Increase the font size of the timer."""
        self.font_size += 2
        self.update_font()

    def decrease_font_size(self):
        """Decrease the font size of the timer."""
        if self.font_size > 10:
            self.font_size -= 2
            self.update_font()

    def update_font(self):
        """Update the font of the timer label."""
        self.font = (FONT_NAME, self.font_size)
        self.timer_label.config(font=self.font)

    def show_info(self):
        """Display information about the program."""
        info_window = tk.Toplevel(self.root)
        info_window.title("About")
        info_window.geometry("300x200")
        info_window.configure(bg=BG_COLOR)
        
        info_text = tk.Text(info_window, wrap=tk.WORD, bg=BG_COLOR, fg=FG_COLOR, font=(FONT_NAME, 10), borderwidth=0)
        info_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        info_text.insert(tk.END, "IBM Presentation Timer\n\n")
        info_text.insert(tk.END, "Author: Jaffeth Alfaro Torres\n")
        info_text.insert(tk.END, "Email: Jaffeth.Alfaro@ibm.com\n")
        info_text.insert(tk.END, "Slack: @jalfaro\n")
        info_text.insert(tk.END, "Last Update: 3-19-2025\n\n")
        info_text.insert(tk.END, "License: MIT\n")
        info_text.insert(tk.END, "GitHub: ")
        info_text.insert(tk.END, "https://github.ibm.com/Jaffeth-Alfaro/Presentation-Timer", "hyperlink")
        info_text.insert(tk.END, "\n\nDownload the latest version from the GitHub repository.")
        
        info_text.tag_configure("hyperlink", foreground="blue", underline=True)
        info_text.tag_bind("hyperlink", "<Button-1>", lambda e: webbrowser.open("https://github.ibm.com/Jaffeth-Alfaro/Presentation-Timer"))
        info_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = PresentationTimer(root)
    root.mainloop()