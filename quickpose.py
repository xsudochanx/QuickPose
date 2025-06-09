import os
import random
import shutil
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from screeninfo import get_monitors
import pygame
import subprocess
import sys

CONFIG_FILE = "quickpose_config.json"

class QuickPoseApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()

        # ✅ Create autorun settings before loading config
        self.autorun_paths = [tk.StringVar() for _ in range(5)]
        self.autorun_enabled = [tk.BooleanVar(value=True) for _ in range(5)]

        self.load_config()         # ✅ Now it can set values properly
        self.create_widgets()
        pygame.mixer.init()


        
    def setup_window(self):
        self.root.title("QuickPose - Gesture Timer")
        self.root.geometry("800x600")
        self.root.minsize(500, 400)
        self.root.configure(bg='#f0f0f0')
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                print(f"Failed to set icon: {e}")
   
    def load_config(self):
        self.config = {
            "last_folder": "",
            "last_csp_file": "",
            "display_time": 60,
            "image_count": 10,
            "last_monitor": 0
        }

        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    self.config.update(json.load(f))

            # Load autorun settings into StringVars and BooleanVars
            for i in range(5):
                self.autorun_paths[i].set(self.config.get(f"autorun_path_{i}", ""))
                self.autorun_enabled[i].set(self.config.get(f"autorun_enabled_{i}", True))

        except Exception as e:
            print(f"Error loading config: {e}")



    def save_config(self):
        for i in range(5):
            self.config[f"autorun_path_{i}"] = self.autorun_paths[i].get()
            self.config[f"autorun_enabled_{i}"] = self.autorun_enabled[i].get()

        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Timer Settings
        settings_frame = ttk.LabelFrame(main_frame, text="Timer Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings_frame, text="Seconds per image:").grid(row=0, column=0, sticky=tk.W)
        self.time_var = tk.IntVar(value=self.config["display_time"])
        ttk.Spinbox(settings_frame, from_=1, to=999, width=5, textvariable=self.time_var).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(settings_frame, text="Number of images:").grid(row=1, column=0, sticky=tk.W)
        self.count_var = tk.IntVar(value=self.config["image_count"])
        ttk.Spinbox(settings_frame, from_=1, to=999, width=5, textvariable=self.count_var).grid(row=1, column=1, sticky=tk.W)
        
        # Monitor Selection
        monitor_frame = ttk.LabelFrame(main_frame, text="Display Monitor", padding=10)
        monitor_frame.pack(fill=tk.X, pady=5)
        
        self.monitor_var = tk.IntVar(value=self.config["last_monitor"])
        monitors = get_monitors()
        for i, monitor in enumerate(monitors):
            ttk.Radiobutton(
                monitor_frame, 
                text=f"Monitor {i+1}: {monitor.width}x{monitor.height}",
                variable=self.monitor_var,
                value=i
            ).pack(anchor=tk.W)
        
        # Folder Selection
        folder_frame = ttk.LabelFrame(main_frame, text="Image Folder", padding=10)
        folder_frame.pack(fill=tk.X, pady=5)
        
        self.folder_var = tk.StringVar(value=self.config["last_folder"])
        ttk.Entry(folder_frame, textvariable=self.folder_var, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(folder_frame, text="Browse...", command=self.select_folder).pack(side=tk.RIGHT)
        
        # Autorun Section (formerly CSP file)
        autorun_frame = ttk.LabelFrame(main_frame, text="Autoruns", padding=10)
        autorun_frame.pack(fill=tk.BOTH, pady=5)

        ttk.Label(autorun_frame, text="Use to run things on startup, like template files, timers, music players, etc.").pack(anchor=tk.W, pady=(0, 5))
        
        for i in range(5):
            row = ttk.Frame(autorun_frame)
            row.pack(fill=tk.X, pady=2)

            check = ttk.Checkbutton(row, variable=self.autorun_enabled[i])
            check.pack(side=tk.LEFT)

            entry = ttk.Entry(row, textvariable=self.autorun_paths[i], state='readonly')
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            browse = ttk.Button(row, text="Browse...", command=lambda idx=i: self.select_autorun_file(idx))
            browse.pack(side=tk.RIGHT)

        
        # Start Button
        ttk.Button(main_frame, text="Start Session", command=self.start_session, style='Accent.TButton').pack(pady=20)
        
        # Style configuration
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='black', background='#0078d7')
        
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.config["last_folder"])
        if folder:
            self.folder_var.set(folder)
            self.config["last_folder"] = folder
            
    def select_autorun_file(self, index):
        file = filedialog.askopenfilename(
            title="Select Autorun File",
            filetypes=[("All files", "*.*")]
        )
        if file:
            self.autorun_paths[index].set(file)

            
    def start_session(self):
        # Save settings
        self.config["display_time"] = self.time_var.get()
        self.config["image_count"] = self.count_var.get()
        self.config["last_monitor"] = self.monitor_var.get()
        self.save_config()
        
        # Validate inputs
        if not os.path.isdir(self.folder_var.get()):
            messagebox.showerror("Error", "Please select a valid image folder")
            return
            
        # Launch autorun files
        for i in range(5):
            if self.autorun_enabled[i].get():
                path = self.autorun_paths[i].get()
                if path and os.path.exists(path):
                    try:
                        if os.name == 'nt':
                            os.startfile(path)
                        else:
                            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                            subprocess.Popen([opener, path])
                    except Exception as e:
                        print(f"Failed to launch autorun file {path}: {e}")

        
        # Start the image display session
        self.run_image_session()
        
    def run_image_session(self):
        from PIL import ImageTk

        monitors = get_monitors()
        if not monitors:
            messagebox.showerror("Error", "No monitors detected")
            return

        monitor_index = min(self.monitor_var.get(), len(monitors)-1)
        monitor = monitors[monitor_index]

        session_window = tk.Toplevel(self.root)
        session_window.title("QuickPose - Session")
        session_window.geometry(f"800x600+{monitor.x}+{monitor.y}")
        session_window.minsize(400, 300)
        session_window.configure(bg='black')

        image_files = [
            f for f in os.listdir(self.folder_var.get())
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
        ]
        random.shuffle(image_files)
        image_files = image_files[:self.config["image_count"]]

        if not image_files:
            messagebox.showerror("Error", "No images found in selected folder")
            session_window.destroy()
            return

        # SESSION STATE
        self.session_window = session_window
        self.img_files = image_files
        self.img_index = 0
        self.timer_seconds = self.config["display_time"]
        self.timer_id = None
        self.timer_paused = False

        main_container = tk.Frame(session_window, bg="black")
        main_container.grid(row=0, column=0, sticky="nsew")

        session_window.rowconfigure(0, weight=1)
        session_window.columnconfigure(0, weight=1)

        main_container.rowconfigure(0, weight=1)  # Image area gets extra space
        main_container.rowconfigure(1, weight=0)  # Control bar is fixed
        main_container.columnconfigure(0, weight=1)

        self.img_frame = tk.Frame(main_container, bg="black")
        self.img_frame.grid(row=0, column=0, sticky="nsew")

        self.img_label = tk.Label(self.img_frame, bg='black')
        self.img_label.pack(fill=tk.BOTH, expand=True)

        control_frame = tk.Frame(main_container, height=50, bg='gray')
        control_frame.grid(row=1, column=0, sticky="ew")
        control_frame.pack_propagate(False)


        btn_frame = tk.Frame(control_frame, bg='gray')
        btn_frame.pack(fill=tk.X, expand=True, pady=5)

        self.progress_var = tk.StringVar()
        progress_label = tk.Label(btn_frame, textvariable=self.progress_var, bg='gray', fg='white')
        progress_label.pack(side=tk.LEFT, padx=10)

        btn_prev = tk.Button(btn_frame, text="⏮ Previous", command=self.prev_image, bg='#555555', fg='white')
        btn_prev.pack(side=tk.LEFT, padx=5)

        self.btn_pause_var = tk.StringVar(value="⏸ Pause")
        btn_pause = tk.Button(btn_frame, textvariable=self.btn_pause_var, command=self.toggle_pause, bg='#555555', fg='white')
        btn_pause.pack(side=tk.LEFT, padx=5)

        btn_next = tk.Button(btn_frame, text="⏭ Next", command=self.next_image, bg='#555555', fg='white')
        btn_next.pack(side=tk.LEFT, padx=5)

        self.timer_var = tk.StringVar()
        timer_label = tk.Label(btn_frame, textvariable=self.timer_var, bg='gray', fg='white')
        timer_label.pack(side=tk.RIGHT, padx=10)

        # Key bindings
        session_window.bind('<Right>', lambda e: self.next_image())
        session_window.bind('<Left>', lambda e: self.prev_image())
        session_window.bind('<space>', lambda e: self.toggle_pause())
        session_window.bind('<Escape>', lambda e: session_window.destroy())

        def on_resize(event):
            if event.widget == self.img_frame:
                self.update_image(resize_only=True)


        self.img_frame.bind('<Configure>', on_resize)


        # Start session
        session_window.after(100, self.update_image)


        
    def resize_preserve_aspect(self, img, max_width, max_height):
        original_width, original_height = img.size
        ratio = min(max_width / original_width, max_height / original_height)
        new_size = (int(original_width * ratio), int(original_height * ratio))
        return img.resize(new_size, Image.Resampling.LANCZOS)
        
    def play_sound(self):
        try:
            sound_file = os.path.join(os.path.dirname(__file__), "next.mp3")
            if os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
            
    def update_image(self, resize_only=False):
        if not (0 <= self.img_index < len(self.img_files)):
            return

        # Move previously shown image to 'used' folder (if not just resizing)
        if not resize_only and self.img_index > 0:
            previous_path = os.path.join(self.folder_var.get(), self.img_files[self.img_index - 1])
            used_dir = os.path.join(self.folder_var.get(), "used")
            os.makedirs(used_dir, exist_ok=True)
            dest_path = os.path.join(used_dir, os.path.basename(previous_path))

            try:
                if os.path.exists(previous_path):
                    shutil.move(previous_path, dest_path)
            except Exception as e:
                print(f"Error moving image to used folder: {e}")

        # Load current image
        img_path = os.path.join(self.folder_var.get(), self.img_files[self.img_index])
        try:
            self.session_window.update_idletasks()
            win_width = max(self.img_frame.winfo_width(), 400)
            win_height = max(self.img_frame.winfo_height(), 300)

            img = Image.open(img_path)
            img = self.resize_preserve_aspect(img, win_width, win_height)
            photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=photo)
            self.img_label.image = photo
        except Exception as e:
            print(f"Error loading image: {e}")
            return

        if not resize_only:
            self.play_sound("next.mp3")
            self.progress_var.set(f"Image {self.img_index + 1}/{len(self.img_files)}")
            self.timer_seconds = self.config["display_time"]
            self.timer_var.set(f"{self.timer_seconds}s")

            if self.timer_id:
                self.session_window.after_cancel(self.timer_id)
            if not self.timer_paused:
                self.timer_id = self.session_window.after(1000, self.update_timer)


    
    def update_timer(self):
        if self.timer_paused:
            return

        self.timer_seconds -= 1
        self.timer_var.set(f"{self.timer_seconds}s")

        if self.timer_seconds <= 0:
            self.next_image()
        else:
            self.timer_id = self.session_window.after(1000, self.update_timer)

    def next_image(self):
        if self.img_index < len(self.img_files) - 1:
            self.img_index += 1
            self.update_image()
        else:
            # Move final image to used/
            final_path = os.path.join(self.folder_var.get(), self.img_files[self.img_index])
            used_dir = os.path.join(self.folder_var.get(), "used")
            os.makedirs(used_dir, exist_ok=True)
            dest_path = os.path.join(used_dir, os.path.basename(final_path))

            try:
                if os.path.exists(final_path):
                    shutil.move(final_path, dest_path)
            except Exception as e:
                print(f"Error moving final image: {e}")

            self.play_sound("end.mp3")
            self.session_window.destroy()
            messagebox.showinfo("Session Complete", "All images have been displayed")



    def prev_image(self):
        if self.img_index > 0:
            self.img_index -= 1
            self.update_image()

    def toggle_pause(self):
        self.timer_paused = not self.timer_paused
        self.btn_pause_var.set("▶ Resume" if self.timer_paused else "⏸ Pause")
        if not self.timer_paused:
            self.timer_id = self.session_window.after(1000, self.update_timer)

    def play_sound(self, filename):
        try:
            sound_file = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = QuickPoseApp(root)
    root.mainloop()