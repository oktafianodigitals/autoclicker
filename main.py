import tkinter as tk
from tkinter import ttk
import threading
import time
import pyautogui
import keyboard
import sys

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Clicker")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # Variabel untuk status dan kontrol
        self.clicking = False
        self.target_position = (0, 0)  # Posisi yang akan diklik
        self.time_unit = tk.StringVar(value="detik")
        self.click_interval = tk.DoubleVar(value=1.0)
        self.click_thread = None
        
        # Setup GUI
        self.create_widgets()
        
        # Setup target window
        self.create_target_window()
        
        # Setup keyboard shortcut
        keyboard.add_hotkey('ctrl+m', self.stop_clicking)
        
        # Cleanup handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        # Frame untuk pengaturan
        settings_frame = ttk.LabelFrame(self.root, text="Pengaturan Auto Clicker")
        settings_frame.pack(padx=10, pady=10, fill="x")
        
        # Pengaturan interval
        ttk.Label(settings_frame, text="Interval:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.click_interval, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        # Dropdown untuk unit waktu
        ttk.Label(settings_frame, text="Unit:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        unit_combo = ttk.Combobox(settings_frame, textvariable=self.time_unit, 
                                 values=["milidetik", "detik", "menit"], 
                                 width=10, state="readonly")
        unit_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Status display
        self.status_var = tk.StringVar(value="Status: Siap")
        status_label = ttk.Label(self.root, textvariable=self.status_var, font=("Arial", 10, "bold"))
        status_label.pack(pady=10)
        
        # Position display
        self.position_var = tk.StringVar(value="Posisi Target: (0, 0)")
        position_label = ttk.Label(self.root, textvariable=self.position_var)
        position_label.pack(pady=5)
        
        # Tombol mulai
        start_button = ttk.Button(self.root, text="Mulai Auto Click", command=self.start_clicking)
        start_button.pack(pady=5, fill="x", padx=10)
        
        # Tombol berhenti
        stop_button = ttk.Button(self.root, text="Berhenti (Ctrl+M)", command=self.stop_clicking)
        stop_button.pack(pady=5, fill="x", padx=10)
        
        # Instructions
        instructions = tk.Text(self.root, height=8, width=40, wrap="word")
        instructions.pack(pady=10, padx=10, fill="both", expand=True)
        instructions.insert("1.0", "Petunjuk:\n"
                        "1. Geser lingkaran target ke posisi yang diinginkan\n"
                        "2. Posisi klik berada di TENGAH lingkaran merah\n"
                        "3. Atur interval waktu klik\n"
                        "4. Klik 'Mulai Auto Click' untuk memulai\n"
                        "5. Tekan 'Ctrl+M' atau klik 'Berhenti' untuk menghentikan\n\n"
                        "Lingkaran target dapat dipindahkan dengan cara drag and drop.")
        instructions.config(state="disabled")
    
    def create_target_window(self):
        self.target_window = tk.Toplevel(self.root)
        self.target_window.overrideredirect(True)
        self.target_window.attributes("-topmost", True)
        
        # Ukuran dan posisi window
        window_size = 50
        self.target_window.geometry(f"{window_size}x{window_size}+100+100")
        
        # Membuat lingkaran dengan lubang transparan di tengah
        self.target_canvas = tk.Canvas(self.target_window, width=window_size, height=window_size, 
                                    bg="SystemButtonFace", highlightthickness=0)
        self.target_canvas.pack(fill="both", expand=True)
        
        # Lingkaran target dengan area tengah transparan
        circle_color = "red"
        outer_radius = window_size // 2 - 3
        inner_radius = 10  # Radius lubang tengah, ubah nilai ini untuk mengatur besar lubang tengah
        
        center_x = window_size // 2
        center_y = window_size // 2
        
        # Konfigurasi winfo untuk mendapatkan warna background
        self.target_window.update()
        
        # Menggambar lingkaran luar
        self.target_canvas.create_oval(
            center_x - outer_radius, 
            center_y - outer_radius, 
            center_x + outer_radius, 
            center_y + outer_radius, 
            outline="black", 
            fill=circle_color, 
            width=2
        )
        
        # Menggambar lubang tengah transparan (sebenarnya kita hanya menggambar lingkaran dengan warna background)
        # Inilah bagian yang bisa diubah untuk mengatur besar/kecil lubang tengah
        self.target_canvas.create_oval(
            center_x - inner_radius, 
            center_y - inner_radius, 
            center_x + inner_radius, 
            center_y + inner_radius, 
            outline="black", 
            fill="SystemButtonFace",  # Menggunakan warna background sistem
            width=1
        )
        
        # Membuat window transparan hanya di bagian tengah
        self.target_window.wm_attributes('-transparentcolor', 'SystemButtonFace')
        
        # Bind events untuk drag and drop
        self.target_canvas.bind("<Button-1>", self.start_drag)
        self.target_canvas.bind("<B1-Motion>", self.on_drag)
        self.target_canvas.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Update posisi awal
        self.update_position()
    
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y
    
    def on_drag(self, event):
        x_move = event.x - self.x
        y_move = event.y - self.y
        
        # Mendapatkan posisi saat ini
        x, y = self.target_window.winfo_x(), self.target_window.winfo_y()
        
        # Memindahkan window
        self.target_window.geometry(f"+{x + x_move}+{y + y_move}")
        
        # Update posisi target
        self.update_position()
    
    def stop_drag(self, event):
        self.update_position()
    
    def update_position(self):
        # Mendapatkan posisi tengah dari target (untuk klik)
        window_size = 50
        center_offset = window_size // 2
        x = self.target_window.winfo_x() + center_offset
        y = self.target_window.winfo_y() + center_offset
        self.target_position = (x, y)
        self.position_var.set(f"Posisi Target: ({x}, {y})")
    
    def start_clicking(self):
        if self.clicking:
            return
        
        self.clicking = True
        self.status_var.set("Status: Auto Clicking...")
        
        # Konversi interval ke detik
        interval = self.click_interval.get()
        unit = self.time_unit.get()
        
        if unit == "milidetik":
            interval /= 1000
        elif unit == "menit":
            interval *= 60
        
        # Memulai thread terpisah untuk clicking
        self.click_thread = threading.Thread(target=self.clicking_loop, args=(interval,))
        self.click_thread.daemon = True
        self.click_thread.start()
    
    def clicking_loop(self, interval):
        while self.clicking:
            try:
                # Klik pada posisi target (tengah lingkaran)
                pyautogui.click(self.target_position[0], self.target_position[1])
                
                # Update status setiap klik (opsional)
                self.root.after(0, lambda: self.status_var.set(f"Status: Klik pada {self.target_position}"))
                
                # Tunggu sesuai interval
                time.sleep(interval)
            except Exception as e:
                print(f"Error dalam clicking_loop: {e}")
                self.root.after(0, lambda: self.status_var.set(f"Status: Error - {e}"))
                self.clicking = False
                break
    
    def stop_clicking(self):
        self.clicking = False
        self.status_var.set("Status: Berhenti")
    
    def on_closing(self):
        # Cleanup resources
        self.clicking = False
        keyboard.unhook_all()
        if self.target_window:
            self.target_window.destroy()
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    # Disable PyAutoGUI fail-safe
    pyautogui.FAILSAFE = False
    
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()