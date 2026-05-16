# ui.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from multiprocessing import Manager
import queue

import sv_ttk
import utils
import processing_logic

class ApplicationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FreeRembg by Logical True")
        self.root.geometry("650x600")
        self.root.resizable(False, False)
        self.ventana_progreso = None
        self.label_progreso = None
        self.progressbar = None
        self.proceso_hilo = None
        
        self._crear_widgets()
        self._cargar_configuracion_inicial()

    def _toggle_theme(self):
        if self.theme_switch_var.get():
            sv_ttk.set_theme("dark")
        else:
            sv_ttk.set_theme("light")
        self._guardar_configuracion_actual()

    def _crear_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(expand=True, fill="both")

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        self.theme_switch_var = tk.BooleanVar()
        theme_switch = ttk.Checkbutton(
            header_frame, 
            text="Modo Oscuro 🌓", 
            variable=self.theme_switch_var, 
            command=self._toggle_theme,
            style="Switch.TCheckbutton"
        )
        theme_switch.pack(side="right")

        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True, fill="both")

        self.frame_imagenes = ttk.Frame(notebook, padding=(10, 15))
        self.frame_videos = ttk.Frame(notebook, padding=(10, 15))
        
        notebook.add(self.frame_imagenes, text=" Procesamiento de Lotes 🖼️ ")
        notebook.add(self.frame_videos, text=" Extractor de Frames 🎬 ")

        self._crear_pestaña_imagenes()
        self._crear_pestaña_videos()

    def _crear_pestaña_imagenes(self):
        files_labelframe = ttk.LabelFrame(self.frame_imagenes, text="1. Selección de Carpetas", padding=(15, 10))
        files_labelframe.pack(fill="x")
        ttk.Label(files_labelframe, text="Carpeta de ENTRADA:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.entry_input_img = ttk.Entry(files_labelframe)
        self.entry_input_img.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        ttk.Button(files_labelframe, text="Examinar...", command=lambda: self._seleccionar_carpeta(self.entry_input_img)).grid(row=1, column=1)
        ttk.Label(files_labelframe, text="Carpeta de SALIDA:").grid(row=2, column=0, sticky="w", pady=(10, 5))
        self.entry_output_img = ttk.Entry(files_labelframe)
        self.entry_output_img.grid(row=3, column=0, sticky="ew", padx=(0, 10))
        ttk.Button(files_labelframe, text="Examinar...", command=lambda: self._seleccionar_carpeta(self.entry_output_img)).grid(row=3, column=1)
        files_labelframe.columnconfigure(0, weight=1)

        options_labelframe = ttk.LabelFrame(self.frame_imagenes, text="2. Opciones de Procesamiento", padding=(15, 10))
        options_labelframe.pack(fill="x", pady=20)
        self.resize_img_var = tk.BooleanVar()
        self.width_img_var = tk.StringVar(value="512")
        self.height_img_var = tk.StringVar(value="512")
        self.anchor_bottom_center_var = tk.BooleanVar()
        check_resize = ttk.Checkbutton(options_labelframe, text="Definir tamaño del lienzo:", variable=self.resize_img_var, command=self._toggle_resize_entries_img)
        check_resize.grid(row=0, column=0, sticky="w")
        self.entry_ancho_img = ttk.Entry(options_labelframe, width=7, textvariable=self.width_img_var, state=tk.DISABLED)
        self.entry_ancho_img.grid(row=0, column=1, padx=(10, 5))
        self.entry_alto_img = ttk.Entry(options_labelframe, width=7, textvariable=self.height_img_var, state=tk.DISABLED)
        self.entry_alto_img.grid(row=0, column=2)
        check_anchor = ttk.Checkbutton(options_labelframe, text="Anclar al centro inferior", variable=self.anchor_bottom_center_var, command=self._toggle_resize_entries_img)
        check_anchor.grid(row=1, column=0, columnspan=3, sticky="w", pady=(10,0))

        # ####################################################################
        # CORRECCIÓN DE LAYOUT AQUÍ
        # ####################################################################
        # Usamos un frame para darle espacio y control al botón
        execute_frame = ttk.Frame(self.frame_imagenes)
        execute_frame.pack(fill="x", expand=True, side="bottom", pady=(10, 0))

        self.btn_ejecutar_img = ttk.Button(execute_frame, text="¡Ejecutar Proceso de IMÁGENES!", style="Accent.TButton", command=self.iniciar_proceso_imagenes)
        self.btn_ejecutar_img.pack(fill="x", ipady=10)
        
    def _crear_pestaña_videos(self):
        files_labelframe = ttk.LabelFrame(self.frame_videos, text="1. Selección de Archivos", padding=(15, 10))
        files_labelframe.pack(fill="x")
        ttk.Label(files_labelframe, text="Archivo de VIDEO de ENTRADA:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.entry_video_input = ttk.Entry(files_labelframe)
        self.entry_video_input.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        ttk.Button(files_labelframe, text="Examinar...", command=self._seleccionar_video).grid(row=1, column=1)
        ttk.Label(files_labelframe, text="Carpeta de SALIDA (Frames):").grid(row=2, column=0, sticky="w", pady=(10, 5))
        self.entry_video_output_frames = ttk.Entry(files_labelframe)
        self.entry_video_output_frames.grid(row=3, column=0, sticky="ew", padx=(0, 10))
        ttk.Button(files_labelframe, text="Examinar...", command=lambda: self._seleccionar_carpeta(self.entry_video_output_frames)).grid(row=3, column=1)
        files_labelframe.columnconfigure(0, weight=1)

        options_labelframe = ttk.LabelFrame(self.frame_videos, text="2. Opciones de Procesamiento", padding=(15, 10))
        options_labelframe.pack(fill="x", pady=20)
        opts_frame = ttk.Frame(options_labelframe)
        opts_frame.pack(fill="x")
        self.fps_var = tk.IntVar(value=24)
        self.quitar_fondo_var = tk.BooleanVar(value=True)
        ttk.Label(opts_frame, text="FPS:").pack(side=tk.LEFT)
        ttk.Spinbox(opts_frame, values=[10, 15, 24, 25, 30, 60], width=5, textvariable=self.fps_var).pack(side=tk.LEFT, padx=(5,20))
        ttk.Checkbutton(opts_frame, text="Quitar fondo", variable=self.quitar_fondo_var).pack(side=tk.LEFT)
        
        self.resize_var = tk.BooleanVar()
        self.width_var = tk.StringVar(value="512")
        self.height_var = tk.StringVar(value="512")
        self.anchor_bottom_center_video_var = tk.BooleanVar()
        
        check_resize = ttk.Checkbutton(options_labelframe, text="Definir tamaño del lienzo:", variable=self.resize_var, command=self._toggle_resize_entries_video)
        check_resize.pack(anchor="w", pady=(15,0))
        
        size_frame = ttk.Frame(options_labelframe)
        size_frame.pack(fill="x", padx=18)
        self.entry_ancho = ttk.Entry(size_frame, width=7, textvariable=self.width_var, state=tk.DISABLED)
        self.entry_ancho.pack(side=tk.LEFT)
        self.entry_alto = ttk.Entry(size_frame, width=7, textvariable=self.height_var, state=tk.DISABLED)
        self.entry_alto.pack(side=tk.LEFT, padx=5)

        check_anchor_video = ttk.Checkbutton(options_labelframe, text="Anclar al centro inferior", variable=self.anchor_bottom_center_video_var, command=self._toggle_resize_entries_video)
        check_anchor_video.pack(anchor="w", pady=(5,0))
        
        # ####################################################################
        # CORRECCIÓN DE LAYOUT AQUÍ TAMBIÉN (para consistencia)
        # ####################################################################
        execute_frame_vid = ttk.Frame(self.frame_videos)
        execute_frame_vid.pack(fill="x", expand=True, side="bottom", pady=(10, 0))
        
        self.btn_ejecutar_video = ttk.Button(execute_frame_vid, text="¡Ejecutar Proceso de VIDEO!", style="Accent.TButton", command=self.iniciar_proceso_video)
        self.btn_ejecutar_video.pack(fill="x", ipady=10)

    def _get_current_config(self):
        return {
            "theme": "dark" if self.theme_switch_var.get() else "light",
            "input_img_path": self.entry_input_img.get(),
            "output_img_path": self.entry_output_img.get(),
            "resize_img_enabled": self.resize_img_var.get(),
            "out_img_width": self.width_img_var.get(),
            "out_img_height": self.height_img_var.get(),
            "anchor_bottom_center": self.anchor_bottom_center_var.get(),
            "input_video_path": self.entry_video_input.get(),
            "output_video_frames_path": self.entry_video_output_frames.get(),
            "fps_value": self.fps_var.get(),
            "quitar_fondo": self.quitar_fondo_var.get(),
            "resize_enabled": self.resize_var.get(),
            "out_width": self.width_var.get(),
            "out_height": self.height_var.get(),
            "anchor_bottom_center_video": self.anchor_bottom_center_video_var.get()
        }

    def _guardar_configuracion_actual(self):
        utils.guardar_configuracion(self._get_current_config())

    def _cargar_configuracion_inicial(self):
        config = utils.cargar_configuracion()
        theme = config.get("theme", "dark") 
        self.theme_switch_var.set(theme == "dark")
        sv_ttk.set_theme(theme)
        
        self.entry_input_img.insert(0, config.get("input_img_path", ""))
        self.entry_output_img.insert(0, config.get("output_img_path", ""))
        self.resize_img_var.set(config.get("resize_img_enabled", False))
        self.width_img_var.set(config.get("out_img_width", "512"))
        self.height_img_var.set(config.get("out_img_height", "512"))
        self.anchor_bottom_center_var.set(config.get("anchor_bottom_center", False))
        self._toggle_resize_entries_img()
        
        self.entry_video_input.insert(0, config.get("input_video_path", ""))
        self.entry_video_output_frames.insert(0, config.get("output_video_frames_path", ""))
        self.fps_var.set(config.get("fps_value", 24))
        self.quitar_fondo_var.set(config.get("quitar_fondo", True))
        self.resize_var.set(config.get("resize_enabled", False))
        self.width_var.set(config.get("out_width", "512"))
        self.height_var.set(config.get("out_height", "512"))
        self.anchor_bottom_center_video_var.set(config.get("anchor_bottom_center_video", False))
        self._toggle_resize_entries_video()

    def _check_progress_queue(self):
        try:
            message = self.progress_queue.get_nowait()
            if isinstance(message, tuple):
                current, total, text = message
                self.progressbar['maximum'] = total
                self.progressbar['value'] = current
                self.label_progreso.config(text=text)
            elif isinstance(message, int):
                self.progressbar['value'] += message
                total = self.progressbar['maximum']
                current = self.progressbar['value']
                self.label_progreso.config(text=f"Procesando {current} de {total} imágenes...")
            
            if self.proceso_hilo and self.proceso_hilo.is_alive():
                 self.root.after(100, self._check_progress_queue)
            else:
                self.root.after(100, lambda: utils.cerrar_ventana_progreso(self.ventana_progreso))

        except queue.Empty:
            if self.proceso_hilo and self.proceso_hilo.is_alive():
                self.root.after(100, self._check_progress_queue)
            else:
                self.root.after(100, lambda: utils.cerrar_ventana_progreso(self.ventana_progreso))

    def lanzar_worker(self, target, args):
        self.ventana_progreso, self.label_progreso, self.progressbar = utils.mostrar_ventana_progreso(self.root)
        self.progress_queue = Manager().Queue()
        args_with_queue = args + (self.progress_queue,)
        self.proceso_hilo = threading.Thread(target=target, args=args_with_queue, daemon=True)
        self.proceso_hilo.start()
        self.root.after(100, self._check_progress_queue)

    def iniciar_proceso_imagenes(self):
        self._guardar_configuracion_actual()
        config = self._get_current_config()
        if not config["input_img_path"] or not config["output_img_path"]:
            messagebox.showwarning("Atención", "Selecciona las carpetas de entrada y salida.")
            return
        if config["resize_img_enabled"] or config["anchor_bottom_center"]:
            try:
                if not (int(config["out_img_width"]) > 0 and int(config["out_img_height"]) > 0): raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Error de Resolución", "El ancho y el alto deben ser números enteros positivos.")
                return
        self.lanzar_worker(
            target=processing_logic.procesar_imagenes,
            args=(
                config["input_img_path"], config["output_img_path"], config["resize_img_enabled"],
                config["out_img_width"], config["out_img_height"], config["anchor_bottom_center"]
            )
        )

    def iniciar_proceso_video(self):
        self._guardar_configuracion_actual()
        config = self._get_current_config()
        if not config["input_video_path"] or not config["output_video_frames_path"]:
            messagebox.showwarning("Atención", "Selecciona video y carpeta de salida.")
            return
        if config["resize_enabled"] or config["anchor_bottom_center_video"]:
            try:
                if not (int(config["out_width"]) > 0 and int(config["out_height"]) > 0): raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Error de Resolución", "El ancho y el alto deben ser números enteros positivos.")
                return
        self.lanzar_worker(
            target=processing_logic.procesar_video,
            args=(
                config["input_video_path"], config["output_video_frames_path"], config["fps_value"],
                config["quitar_fondo"], config["resize_enabled"], config["out_width"],
                config["out_height"], config["anchor_bottom_center_video"]
            )
        )
    
    def _seleccionar_carpeta(self, entry_widget):
        ruta = filedialog.askdirectory()
        if ruta:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, ruta)
    
    def _seleccionar_video(self):
        ruta = filedialog.askopenfilename()
        if ruta:
            self.entry_video_input.delete(0, tk.END)
            self.entry_video_input.insert(0, ruta)

    def _toggle_resize_entries_img(self):
        state = tk.NORMAL if self.resize_img_var.get() or self.anchor_bottom_center_var.get() else tk.DISABLED
        self.entry_ancho_img.config(state=state)
        self.entry_alto_img.config(state=state)

    def _toggle_resize_entries_video(self):
        state = tk.NORMAL if self.resize_var.get() or self.anchor_bottom_center_video_var.get() else tk.DISABLED
        self.entry_ancho.config(state=state)
        self.entry_alto.config(state=state)