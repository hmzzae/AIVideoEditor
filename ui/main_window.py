import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import cv2
from PIL import Image
import pygame
from pipeline import run_full_pipeline

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Video Editor")
        self.geometry("1000x700")
        self.minsize(900, 600)
        
        pygame.mixer.init()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.video_cap = None
        self.is_playing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self, width=950, height=650)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_editor = self.tabview.add("Studio Dashboard")
        self.tab_settings = self.tabview.add("Settings & API")
        
        self.build_settings_tab()
        self.build_editor_tab()

    def build_settings_tab(self):
        ctk.CTkLabel(self.tab_settings, text="Engine Configuration", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))
        key_frame = ctk.CTkFrame(self.tab_settings)
        key_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(key_frame, text="Gemini API Key:").pack(side="left", padx=10, pady=15)
        self.api_key_entry = ctk.CTkEntry(key_frame, show="*", width=400, placeholder_text="Enter your Gemini API key...")
        self.api_key_entry.pack(side="left", padx=10, pady=15)
        def paste_api_key(event=None):
            try:
                clipboard_text = self.clipboard_get()
                self.api_key_entry.insert("insert", clipboard_text)
            except Exception:
                pass
            return "break"  # Prevents double paste on some systems

        # Bind Ctrl+v, Control+v, and middle-click paste for Linux
        self.api_key_entry.bind("<Control-v>", paste_api_key)
        self.api_key_entry.bind("<Control-V>", paste_api_key)
    def build_editor_tab(self):
        self.tab_editor.grid_columnconfigure(0, weight=1) 
        self.tab_editor.grid_columnconfigure(1, weight=1) 
        self.tab_editor.grid_rowconfigure(0, weight=1)
        
        # --- LEFT PANEL (Controls & Logs) ---
        left_panel = ctk.CTkFrame(self.tab_editor, fg_color="transparent")
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        input_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 20))
        
        self.video_path_entry = ctk.CTkEntry(input_row, placeholder_text="Select source video...")
        self.video_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(input_row, text="Browse", command=self.browse_video, width=80).pack(side="right")
        
        self.process_btn = ctk.CTkButton(left_panel, text="Generate a Reel", font=ctk.CTkFont(size=15, weight="bold"), height=40, command=self.start_processing_thread)
        self.process_btn.pack(fill="x", pady=(0, 10))
        
        self.progress_label = ctk.CTkLabel(left_panel, text="Status: Awaiting input...", text_color="gray")
        self.progress_label.pack(anchor="w")
        
        self.progress_bar = ctk.CTkProgressBar(left_panel, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=(5, 20))
        self.progress_bar.set(0) 
        
        ctk.CTkLabel(left_panel, text="Engine Terminal", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        self.log_text = ctk.CTkTextbox(left_panel, state="disabled", fg_color="#121212", text_color="#00FF00", font=("Consolas", 11))
        self.log_text.pack(fill="both", expand=True)

        # --- RIGHT PANEL (Preview) ---
        right_panel = ctk.CTkFrame(self.tab_editor)
        right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(right_panel, text="Playback Preview", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.video_label = ctk.CTkLabel(right_panel, text="No video generated yet.", fg_color="black", width=300, height=533, corner_radius=10)
        self.video_label.pack(pady=10, expand=True)

    def browse_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv")])
        if file_path:
            self.video_path_entry.delete(0, "end")
            self.video_path_entry.insert(0, file_path)
            self.log(f"Selected source video: {file_path}")
            
    def log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_status(self, text):
        self.progress_label.configure(text=f"Status: {text}")

    def start_processing_thread(self):
        api_key = self.api_key_entry.get().strip()
        video_path = self.video_path_entry.get().strip()
        
        if not api_key or not video_path:
            messagebox.showerror("Missing Data", "Check your settings! API Key and Video Path are required.")
            self.tabview.set("Settings & API") 
            return
            
        if not os.path.exists(video_path):
            messagebox.showerror("File Error", "The specified input video file does not exist.")
            return

        self.process_btn.configure(state="disabled")
        self.progress_bar.start()
        
        self.is_playing = False
        pygame.mixer.music.stop()
        if self.video_cap:
            self.video_cap.release()
            self.video_label.configure(image="", text="Processing new video...")
        
        # Launch the engine in the background
        worker = threading.Thread(target=self.run_pipeline_thread, args=(video_path, api_key))
        worker.daemon = True 
        worker.start()

    def run_pipeline_thread(self, video_path, api_key):
        # Pass the UI update functions directly into the orchestrator
        run_full_pipeline(
            video_path=video_path, 
            api_key=api_key, 
            log_callback=self.log, 
            status_callback=self.update_status, 
            on_complete=self.on_pipeline_complete
        )

    def on_pipeline_complete(self, final_video_path):
        self.progress_bar.stop()
        self.process_btn.configure(state="normal")
        
        if final_video_path and os.path.exists(final_video_path):
            self.log("[UI] Launching synced audio/video preview...")
            self.play_video(final_video_path)

    # --- DUAL-ENGINE PLAYBACK LOGIC ---
    def play_video(self, video_path):
        self.video_cap = cv2.VideoCapture(video_path)
        self.is_playing = True
        
        try:
            pygame.mixer.music.load(video_path)
            pygame.mixer.music.play()
        except Exception as e:
            self.log(f"[Warning] Audio engine failed to load track: {e}")
            
        self.update_frame()

    def update_frame(self):
        if self.is_playing and self.video_cap and self.video_cap.isOpened():
            ret, frame = self.video_cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                ctk_image = ctk.CTkImage(light_image=img, size=(300, 533))
                
                self.video_label.configure(image=ctk_image, text="")
                self.after(33, self.update_frame)
            else:
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                pygame.mixer.music.play()
                self.after(33, self.update_frame)

    def on_closing(self):
        self.is_playing = False
        pygame.mixer.music.stop() 
        if self.video_cap:
            self.video_cap.release()
        self.destroy()