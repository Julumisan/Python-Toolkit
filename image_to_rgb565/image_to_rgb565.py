# Project: Image to RGB565 Converter
# Description: Convierte imágenes a formato binario raw (RGB565) para pantallas TFT (ESP32/Arduino).
#              Incluye redimensionado inteligente (Center Crop) y generación opcional de cabeceras C (.h).
#              Soporta inversión de color y cambio de canales RB.
# Author: JLMS

import os
import argparse
import struct
from PIL import Image, ImageOps

def pack_rgb565(r, g, b, swap_rb=False, invert=False):
    """
    Empaqueta valores R, G, B en un entero de 16 bits (RGB565).
    Realiza intercambio de canales o inversión de bits si se solicita.
    """
    if swap_rb:
        r, b = b, r
    
    # Formula RGB565: RRRRRGGG GGGBBBBB
    val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    
    if invert:
        val = ~val & 0xFFFF
        
    return val

def generate_c_header(data, var_name, out_path):
    """Genera un archivo de cabecera C con el array de datos."""
    with open(out_path, "w") as f:
        f.write(f"// Generado por Image to RGB565 Converter\n")
        f.write(f"// Bytes: {len(data)}\n")
        f.write(f"#include <pgmspace.h>\n\n")
        f.write(f"const uint16_t {var_name}[] PROGMEM = {{\n")
        
        # Se escribe en formato hex, agrupando de 16 en 16 valores
        # Los datos en 'data' son bytes (Big Endian per pixel), se reconstruyen words
        count = 0
        line = "  "
        # Iterar de 2 en 2 bytes
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                # Reconstruye el word
                word = (data[i] << 8) | data[i+1]
                line += f"0x{word:04X}, "
                count += 1
                if count >= 12:
                    f.write(line + "\n")
                    line = "  "
                    count = 0
        
        if line != "  ":
            f.write(line + "\n")
            
        f.write("};\n")

def process_image(img_path, args):
    """Procesa una única imagen según los argumentos proporcionados."""
    try:
        img = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"[Error] No se pudo abrir {img_path}: {e}")
        return

    # Redimensionado inteligente (Center Crop) para mantener aspecto
    # ImageOps.fit recorta el centro en lugar de deformar
    img = ImageOps.fit(img, (args.width, args.height), Image.Resampling.LANCZOS)

    root, _ = os.path.splitext(img_path)
    filename = os.path.basename(root)
    
    # Buffer para datos binarios
    raw_data = bytearray()
    
    pixels = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            val = pack_rgb565(r, g, b, args.swap, args.invert)
            
            # Big Endian (MSB primero) es lo estándar para SPI TFTs
            raw_data.append((val >> 8) & 0xFF)
            raw_data.append(val & 0xFF)

    # 1. Exportar RAW (Binario puro)
    if not args.no_raw:
        out_raw = f"{root}.raw"
        with open(out_raw, "wb") as f:
            f.write(raw_data)
        print(f"[OK] RAW generado: {os.path.basename(out_raw)}")

    # 2. Exportar Header C (Opcional)
    if args.c_header:
        out_h = f"{root}.h"
        # Limpia nombre de variable (solo alfanumérico)
        var_name = "".join(x for x in filename if x.isalnum()) + "_img"
        generate_c_header(raw_data, var_name, out_h)
        print(f"[OK] Header C generado: {os.path.basename(out_h)}")

    # 3. Borrar original (Opcional)
    if args.delete:
        os.remove(img_path)
        print(f"     (Original eliminado: {os.path.basename(img_path)})")

def main():
    parser = argparse.ArgumentParser(description="Convierte imágenes para pantallas TFT (RGB565).")
    parser.add_argument("source", nargs="?", default=".", help="Archivo o carpeta a procesar (default: carpeta actual)")
    parser.add_argument("-W", "--width", type=int, default=240, help="Ancho objetivo (default: 240)")
    parser.add_argument("-H", "--height", type=int, default=320, help="Alto objetivo (default: 320)")
    parser.add_argument("--swap", action="store_true", help="Intercambiar canales Rojo y Azul (Fix BGR)")
    parser.add_argument("--invert", action="store_true", help="Invertir colores (Fix negativo)")
    parser.add_argument("--c-header", action="store_true", help="Generar también archivo .h (array C)")
    parser.add_argument("--no-raw", action="store_true", help="No generar archivo .raw")
    parser.add_argument("--delete", action="store_true", help="Borrar imágenes originales tras conversión")

    args = parser.parse_args()

    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

    targets = []
    if os.path.isfile(args.source):
        targets.append(args.source)
    elif os.path.isdir(args.source):
        for f in os.listdir(args.source):
            if os.path.splitext(f)[1].lower() in extensions:
                targets.append(os.path.join(args.source, f))
    else:
        print(f"[Error] La fuente '{args.source}' no existe.")
        return

    if not targets:
        print("[Info] No se encontraron imágenes para procesar.")
        return

    print(f"Procesando {len(targets)} archivos...")
    print(f"Config: {args.width}x{args.height} | SwapRB: {args.swap} | Invert: {args.invert}")
    print("-" * 40)

    for path in targets:
        process_image(path, args)

if __name__ == "__main__":
    main()