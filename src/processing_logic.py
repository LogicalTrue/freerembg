# processing_logic.py

import os
import shutil
import time
import sys
import uuid
import subprocess
from PIL import Image
from rembg import remove  # <--- IMPORTANTE: Usamos la librería interna
from tkinter import messagebox

# Extensiones que aceptamos. Todo lo demás se ignora.
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

def procesar_imagenes(ruta_input, ruta_output, redimensionar, ancho, alto, anchor_bottom_center, progress_queue):
    """
    Procesa imágenes usando recursividad para clonar la estructura de subcarpetas.
    """
    try:
        # 1. Validaciones iniciales
        if not os.path.exists(ruta_input):
            progress_queue.put((0, 0, "Error: La carpeta no existe"))
            return
        if not os.path.exists(ruta_output): 
            os.makedirs(ruta_output)

        # 2. Filtrado RECURSIVO (El cambio clave)
        archivos_validos = []
        for root_dir, _, files in os.walk(ruta_input):
            for f in files:
                if f.lower().endswith(VALID_EXTENSIONS):
                    archivos_validos.append(os.path.join(root_dir, f))

        total_files = len(archivos_validos)

        if total_files == 0:
            progress_queue.put((1, 1, "Sin imágenes"))
            return

        progress_queue.put((0, total_files, "Iniciando motor de IA..."))
        print(f"--> Procesando {total_files} imágenes recursivamente...")

 # 3. Bucle de procesamiento clonador
        for i, ruta_completa_in in enumerate(archivos_validos):
            # Averiguamos la ruta relativa para mantener las carpetas ordenadas
            ruta_relativa = os.path.relpath(ruta_completa_in, ruta_input)
            directorio_relativo = os.path.dirname(ruta_relativa)
            
            # MAGIA UUID: Genera un string único de 32 caracteres (ej: 'c9a646d39c61405386f123456789abcd')
            # Usamos .hex para quitarle los guiones y que quede un string alfanumérico limpio
            nombre_unico = uuid.uuid4().hex
            
            # Armamos la ruta de salida con el nuevo nombre único
            ruta_completa_out = os.path.join(ruta_output, directorio_relativo, f"{nombre_unico}.png")

            # Creamos las subcarpetas en el destino si no existen
            os.makedirs(os.path.dirname(ruta_completa_out), exist_ok=True)

            try:
                # --- A. REMOVER FONDO ---
                with open(ruta_completa_in, 'rb') as file_in:
                    input_data = file_in.read()
                    
                subject = remove(input_data)

                # --- B. POST-PROCESAMIENTO ---
                if redimensionar or anchor_bottom_center:
                    from io import BytesIO
                    img = Image.open(BytesIO(subject))
                    img_final = _aplicar_transformacion_pil(img, redimensionar, int(ancho), int(alto), anchor_bottom_center)
                    img_final.save(ruta_completa_out)
                else:
                    with open(ruta_completa_out, 'wb') as file_out:
                        file_out.write(subject)

            except Exception as e:
                print(f"❌ Error en archivo {ruta_relativa}: {e}")
                continue

        progress_queue.put((total_files, total_files, "¡Proceso Completado!"))
        time.sleep(0.5)
        print("Proceso finalizado con éxito manteniendo las carpetas.")

    except Exception as e:
        print(f"Error fatal: {e}")
        progress_queue.put((0, 0, f"Error: {str(e)}"))

def _aplicar_transformacion_pil(img_original, redimensionar, target_w, target_h, anchor_bottom):
    """
    Lógica corregida: Escala el frame completo para no destruir 
    la coherencia espacial de la secuencia de video.
    """
    if redimensionar or anchor_bottom:
        canvas_w, canvas_h = target_w, target_h
        # Creamos el lienzo vacío transparente
        final_canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        
        # Escalamos la imagen COMPLETA para no perder la posición relativa original
        scale_ratio = min(canvas_w / img_original.width, canvas_h / img_original.height)
        new_w = int(img_original.width * scale_ratio)
        new_h = int(img_original.height * scale_ratio)
        
        img_resized = img_original.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Centramos horizontalmente por defecto
        x_offset = (canvas_w - new_w) // 2
        
        # Si ancla abajo, lo pegamos al fondo. Si no, al centro vertical.
        if anchor_bottom:
            y_offset = canvas_h - new_h
        else:
            y_offset = (canvas_h - new_h) // 2
            
        # Pegamos el frame escalado en el nuevo lienzo
        final_canvas.paste(img_resized, (x_offset, y_offset), img_resized)
        return final_canvas

    # Si no hay que redimensionar ni anclar, devolvemos como viene
    return img_original


def obtener_ruta_ffmpeg():
    """Encuentra el binario de ffmpeg ya sea en desarrollo o compilado."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Si está corriendo como un .exe compilado por PyInstaller
        return os.path.join(sys._MEIPASS, 'assets', 'ffmpeg.exe')
    else:
        # Si estás corriendo el .py crudo desde tu editor
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ruta_base, 'assets', 'ffmpeg.exe')

def procesar_video(ruta_video, ruta_salida_frames, fps, quitar_fondo, redimensionar, ancho, alto, 
                   anchor_bottom_center, progress_queue):
    """
    Procesa video extrayendo frames con ffmpeg y luego limpiando con rembg (librería).
    """
    import subprocess # FFMPEG sí necesita subprocess, rembg no.
    
    try:
        os.makedirs(ruta_salida_frames, exist_ok=True)
        
        # 1. Extracción de frames
        progress_queue.put((0, 100, "Extrayendo frames con FFmpeg..."))
        
        # Carpeta temporal para frames crudos
        temp_dir = os.path.join(ruta_salida_frames, "temp_raw_frames")
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        # Buscamos nuestro ejecutable empaquetado
        ruta_ffmpeg = obtener_ruta_ffmpeg()

        # Comando FFMPEG usando nuestro binario privado 🎬
        subprocess.run([
            ruta_ffmpeg, '-i', ruta_video, '-vf', f'fps={fps}', 
            os.path.join(temp_dir, 'frame_%06d.png')
        ], check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

        frames = sorted(os.listdir(temp_dir))
        total_frames = len(frames)
        
        if not quitar_fondo:
            # Si no quitamos fondo, solo movemos los archivos
            for f in frames:
                shutil.move(os.path.join(temp_dir, f), os.path.join(ruta_salida_frames, f))
            shutil.rmtree(temp_dir)
            progress_queue.put((100, 100, "Listo"))
            return

        # 2. Procesamiento frame a frame con Rembg (Librería)
        progress_queue.put((20, 100, "Iniciando IA en frames..."))
        
        for i, frame in enumerate(frames):
            ruta_in = os.path.join(temp_dir, frame)
            ruta_out = os.path.join(ruta_salida_frames, frame)
            
            # --- REMBG INTERNO ---
            with open(ruta_in, 'rb') as f_in:
                data = f_in.read()
                out_data = remove(data)
            
            # --- RESIZE/ANCHOR ---
            if redimensionar or anchor_bottom_center:
                from io import BytesIO
                img = Image.open(BytesIO(out_data))
                img_final = _aplicar_transformacion_pil(img, redimensionar, int(ancho), int(alto), anchor_bottom_center)
                img_final.save(ruta_out)
            else:
                with open(ruta_out, 'wb') as f_out:
                    f_out.write(out_data)

            # Actualizar barra cada 5 frames para no saturar
            if i % 5 == 0:
                porcentaje = 20 + int((i / total_frames) * 80)
                progress_queue.put((porcentaje, 100, f"Video: Frame {i}/{total_frames}"))

        # Limpieza
        shutil.rmtree(temp_dir)
        progress_queue.put((100, 100, "¡Video completado!"))

    except Exception as e:
        progress_queue.put((0, 0, f"Error video: {str(e)}"))
        print(f"Error video: {e}")