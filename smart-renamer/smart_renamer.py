# Project: Smart Media Renamer
# Description: Utilidad para normalizar nombres de archivos multimedia (WhatsApp, Android, etc.)
#              usando patrones Regex. Incluye detección de colisiones y modo 'dry-run'.
# Author: JLMS

import os
import re
import argparse
import sys

def get_unique_filename(directory, filename):
    """
    Si el archivo existe, añade un contador (_1, _2) para evitar sobrescribir.
    Ejemplo: foto.jpg -> foto_1.jpg
    """
    name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
        
    return new_filename

def run_renamer(target_folder, dry_run=False):
    """Ejecuta el proceso de renombrado basado en patrones predefinidos."""
    
    # Lista de patrones (Tuplas: Regex Búsqueda, Formato Reemplazo)
    patrones = [
        # WhatsApp Images: IMG-YYYYMMDD-WAXXXX.jpg -> YYYY_MM_DD_XXXX.jpg
        (r"IMG-(\d{4})(\d{2})(\d{2})-WA(\d{4})\.jpg", r"\1_\2_\3_\4.jpg"),
        (r"IMG-(\d{4})(\d{2})(\d{2})-WA(\d{4})\.jpeg", r"\1_\2_\3_\4.jpeg"),
        
        # WhatsApp Video: VID-YYYYMMDD-WAXXXX.mp4 -> YYYY_MM_DD_XXXX.mp4
        (r"VID-(\d{4})(\d{2})(\d{2})-WA(\d{4})\.mp4", r"\1_\2_\3_\4.mp4"),
        
        # Android Standard IMG: IMGYYYYMMDDHHMMSS.jpg -> YYYY_MM_DD_HH-MM-SS.jpg
        (r"IMG(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.jpg", r"\1_\2_\3_\4-\5-\6.jpg"),
        (r"IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.jpg", r"\1_\2_\3_\4-\5-\6.jpg"),
        
        # Android Standard VID
        (r"VID(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.mp4", r"\1_\2_\3_\4-\5-\6.mp4"),
        (r"VID_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.mp4", r"\1_\2_\3_\4-\5-\6.mp4"),
        (r"VID_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.mp4", r"\1_\2_\3_\4-\5-\6.mp4"),

        # WhatsApp Export format (Español/Inglés)
        (r"WhatsApp\ Image\ (\d{4})-(\d{2})-(\d{2})\ at\ (\d{2})\.(\d{2})\.(\d{2})\.jpeg", r"\1_\2_\3_\4-\5-\6.jpeg"),
        (r"WhatsApp\ Video\ (\d{4})-(\d{2})-(\d{2})\ at\ (\d{2})\.(\d{2})\.(\d{2})\.mp4", r"\1_\2_\3_\4-\5-\6.mp4"),

        # Screenshots (WhatsApp y Generales)
        (r"Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{3})_.*\.jpg", r"\1_\2_\3_\4_\5_\6_\7.jpeg"),
        
        # Casos especiales WA con sufijos (~1)
        (r"IMG-(\d{4})(\d{2})(\d{2})-WA(\d{4})\~(\d{1})\.jpg", r"\1_\2_\3_\4_\5.jpg"),

        # Sufijo _VIDEO para mp4 genéricos (cuidado con este patrón, es agresivo)
        # Se asegura de no aplicarlo si ya tiene _VIDEO
        (r"^(?!.*_VIDEO)(.+)\.mp4$", r"\1_VIDEO.mp4"),
        
        # Corrección de doble sufijo si ocurriera
        (r"(.+)_VIDEO_VIDEO\.mp4$", r"\1_VIDEO.mp4")
    ]

    count = 0
    if not os.path.isdir(target_folder):
        print(f"[Error] La ruta no existe: {target_folder}")
        return

    print(f"Analizando: {target_folder}")
    if dry_run:
        print("[MODO SIMULACIÓN] No se realizarán cambios reales.\n")

    for archivo in os.listdir(target_folder):
        ruta_completa = os.path.join(target_folder, archivo)
        
        # Ignorar carpetas, solo archivos
        if not os.path.isfile(ruta_completa):
            continue

        renombrado = False
        
        for patron, reemplazo in patrones:
            if re.match(patron, archivo):
                nuevo_nombre_base = re.sub(patron, reemplazo, archivo)
                
                # Evitar renombrar si el nombre no cambia
                if nuevo_nombre_base == archivo:
                    break

                # Gestión de colisiones (si el archivo ya existe)
                nuevo_nombre_final = get_unique_filename(target_folder, nuevo_nombre_base)
                
                ruta_nueva = os.path.join(target_folder, nuevo_nombre_final)

                if dry_run:
                    print(f"[Simul] {archivo}  -->  {nuevo_nombre_final}")
                else:
                    try:
                        os.rename(ruta_completa, ruta_nueva)
                        print(f"[OK] {archivo}  -->  {nuevo_nombre_final}")
                    except OSError as e:
                        print(f"[Error] No se pudo renombrar {archivo}: {e}")
                
                renombrado = True
                count += 1
                break 

    print("-" * 40)
    print(f"Proceso finalizado. Archivos procesados: {count}")

def main():
    parser = argparse.ArgumentParser(description="Renombrador masivo de archivos multimedia basado en patrones Regex.")
    parser.add_argument("folder", nargs="?", default=".", help="Carpeta a procesar (por defecto: carpeta actual)")
    parser.add_argument("--run", action="store_true", help="Ejecutar cambios reales (Por defecto es MODO SIMULACIÓN)")
    
    args = parser.parse_args()
    
    target_folder = os.path.abspath(args.folder)
    
    # Por seguridad, dry_run es True a menos que se use --run
    is_dry_run = not args.run
    
    run_renamer(target_folder, dry_run=is_dry_run)

if __name__ == "__main__":
    main()