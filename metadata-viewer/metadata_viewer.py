# Project: Metadata & EXIF Viewer
# Description: Extractor de metadatos de archivos e imágenes. 
#              Incluye decodificación de coordenadas GPS a formato decimal (Google Maps)
#              y alertas de privacidad.
# Author: JLMS

import os
import sys
import datetime
import argparse
from PIL import Image, ExifTags

def limpiar_ruta(ruta_sucia):
    """Limpia las rutas arrastradas desde la terminal (elimina comillas simples y dobles)."""
    if not ruta_sucia: return ""
    ruta = ruta_sucia.strip()
    
    # Eliminamos ambas comillas por seguridad en cualquier OS
    ruta = ruta.replace('"', '').replace("'", "")
    
    # Limpieza específica de caracteres de escape si es necesario
    if sys.platform != "win32":
        ruta = ruta.replace("\\ ", " ")
    else:
        ruta = ruta.replace("& ", "")
        
    return ruta

def obtener_info_general(ruta):
    """Obtiene metadatos del sistema de archivos (OS level)."""
    try:
        info = os.stat(ruta)
        creado = datetime.datetime.fromtimestamp(info.st_ctime)
        modif = datetime.datetime.fromtimestamp(info.st_mtime)
        size_mb = info.st_size / (1024 * 1024)
        
        print(f"\n[SISTEMA DE ARCHIVOS]")
        print(f"   Archivo:   {os.path.basename(ruta)}")
        print(f"   Ruta:      {os.path.dirname(ruta)}")
        print(f"   Tamaño:    {size_mb:.2f} MB")
        print(f"   Creado:    {creado}")
        print(f"   Modific.:  {modif}")
        return True
    except Exception as e:
        print(f"[Error] No se puede acceder al archivo: {e}")
        return False

# --- INICIO DEL BLOQUE GPS CORREGIDO ---

def _safe_float(val):
    """Convierte de forma segura tipos IFDRational o tuplas a float, evitando dividir por cero."""
    try:
        # Caso 1: Es un objeto IFDRational (propio de Pillow)
        if hasattr(val, 'numerator') and hasattr(val, 'denominator'):
            if val.denominator == 0: return 0.0
            return float(val)
        
        # Caso 2: Es una tupla/lista antigua (numerador, denominador)
        if isinstance(val, (tuple, list)) and len(val) == 2:
            if val[1] == 0: return 0.0
            return val[0] / val[1]
            
        # Caso 3: Ya es un int o float
        return float(val)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0

def _convertir_a_grados(value):
    """
    Convierte las tuplas GPS a decimal usando conversión segura.
    """
    try:
        d = _safe_float(value[0])
        m = _safe_float(value[1])
        s = _safe_float(value[2])
        
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return 0.0

def obtener_gps_info(exif_data):
    """Busca y decodifica la información GPS si existe y es válida."""
    if not exif_data: return
    
    gps_info = None
    for tag, value in exif_data.items():
        decoded = ExifTags.TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            gps_info = value
            break
            
    if not gps_info:
        return

    # Indices estándar (1=LatRef, 2=Lat, 3=LonRef, 4=Lon)
    try:
        lat_ref = gps_info.get(1)
        lat_raw = gps_info.get(2)
        lon_ref = gps_info.get(3)
        lon_raw = gps_info.get(4)
        
        if lat_raw and lon_raw:
            # Ahora _convertir_a_grados ya no fallará, devolverá 0.0 si hay error
            lat = _convertir_a_grados(lat_raw)
            lon = _convertir_a_grados(lon_raw)
            
            # Si el resultado es 0.0 y 0.0, ignoramos
            if lat == 0.0 and lon == 0.0:
                print(f"   [Info] Coordenadas inválidas (0,0) detectadas.")
                return 

            # Ajuste de hemisferios
            if lat_ref == "S": lat = -lat
            if lon_ref == "W": lon = -lon
            
            print(f"\n[DATOS DE GEOLOCALIZACIÓN]")
            print(f"   Coordenadas: {lat:.6f}, {lon:.6f}")
            # Usamos el link estándar de Google Maps que funciona mejor
            print(f"   Google Maps: https://www.google.com/maps?q={lat},{lon}")
            print(f"   ALERTA!!!: Esta imagen revela la ubicación exacta.")
            
    except Exception as e:
        print(f"   [Error GPS]: {e}")

# --- FIN DEL BLOQUE GPS ---
        
        
def analizar_imagen(ruta):
    """Extrae EXIF estándar y busca GPS."""
    try:
        img = Image.open(ruta)
        exif_raw = img._getexif()
        
        if not exif_raw:
            print("\n[INFO] La imagen no contiene metadatos EXIF (posiblemente eliminados o formato Web).")
            return

        print(f"\n[DATOS DE CÁMARA / EXIF]")
        
        # Tags de interés prioritario
        tags_interes = ["Make", "Model", "DateTimeOriginal", "Software", "LensModel", "ISOSpeedRatings", "ExposureTime", "FNumber"]
        
        for tag_id, value in exif_raw.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            
            # Filtramos datos binarios largos (MakerNote, UserComment)
            if isinstance(value, bytes) or len(str(value)) > 100:
                continue
                
            if tag_name in tags_interes:
                print(f"   {tag_name:<20}: {value}")
        
        # Intentar extraer GPS
        obtener_gps_info(exif_raw)

    except IOError:
        print("\n[INFO] El archivo no es una imagen o formato no soportado por Pillow.")
    except Exception as e:
        print(f"[Error] Analizando imagen: {e}")

def procesar_archivo(ruta):
    if not os.path.isfile(ruta):
        print(f"[Error] La ruta no existe: {ruta}") # Muestra qué ruta está intentando leer para depurar
        return
    
    print("="*60)
    if obtener_info_general(ruta):
        # Intentamos analizar como imagen sin importar la extensión
        analizar_imagen(ruta)
    print("="*60)

def modo_interactivo():
    print("==================================================")
    print("   METADATA INSPECTOR (Arrastra y suelta)")
    print("   Escribe 'salir' para cerrar.")
    print("==================================================")
    while True:
        try:
            entrada = input("\n>> Archivo: ")
            if entrada.lower() in ["salir", "exit"]: break
            ruta = limpiar_ruta(entrada)
            if ruta: procesar_archivo(ruta)
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break

def main():
    parser = argparse.ArgumentParser(description="Inspector de Metadatos y EXIF/GPS")
    parser.add_argument("archivo", nargs="?", help="Ruta al archivo a analizar")
    args = parser.parse_args()
    
    if args.archivo:
        procesar_archivo(limpiar_ruta(args.archivo)) # Aplicamos limpieza también aquí
    else:
        modo_interactivo()

if __name__ == "__main__":
    main()