# Project: PDF to Images Converter
# Description: Utilidad CLI para convertir páginas de PDF a imágenes (PNG, JPG, TIFF).
#              Soporta selección de rangos, ajuste de DPI, escala de grises y transparencia.
# Author: JLMS

import argparse
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: Falta la librería PyMuPDF. Instálala con: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


def parse_page_ranges(rng: str, max_pages: int):
    """
    Convierte una cadena de rangos (ej: '1-3,5,10-12') en una lista de índices.
    Maneja errores de formato y límites de página.
    """
    indices = set()
    for part in rng.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                a_str, b_str = part.split("-", 1)
                a = int(a_str)
                b = int(b_str)
            except ValueError:
                continue
            
            a = max(1, a)
            b = min(max_pages, b)
            for i in range(a, b + 1):
                indices.add(i - 1) # Convertir a 0-based index
        else:
            try:
                i = int(part)
                if 1 <= i <= max_pages:
                    indices.add(i - 1)
            except ValueError:
                pass
    return sorted(indices)


def main():
    parser = argparse.ArgumentParser(
        description="Convierte páginas de un PDF a archivos de imagen individuales."
    )
    parser.add_argument("pdf", help="Ruta al archivo PDF de entrada")
    parser.add_argument("-o", "--out", default=None,
                        help="Carpeta de salida (por defecto: <nombre_pdf>_pages)")
    parser.add_argument("--dpi", type=int, default=200,
                        help="Resolución de salida en DPI (por defecto 200)")
    parser.add_argument("--fmt", default="png", choices=["png", "jpg", "jpeg", "tiff", "ppm"],
                        help="Formato de imagen de salida (por defecto png)")
    parser.add_argument("--prefix", default="page",
                        help="Prefijo para los nombres de archivo (por defecto 'page')")
    parser.add_argument("--password", default=None,
                        help="Contraseña si el PDF está encriptado")
    parser.add_argument("--pages", default=None,
                        help="Rango de páginas a exportar (ej: '1-3,5,8-10').")
    
    # Nuevas opciones añadidas
    parser.add_argument("--grayscale", action="store_true",
                        help="Convertir a escala de grises (reduce tamaño de archivo)")
    parser.add_argument("--transparent", action="store_true",
                        help="Mantener fondo transparente (solo para PNG/TIFF)")

    args = parser.parse_args()

    pdf_path = args.pdf
    if not os.path.isfile(pdf_path):
        print(f"[Error] No se encontró el archivo: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Definir carpeta de salida
    out_dir = args.out or (os.path.splitext(os.path.basename(pdf_path))[0] + "_pages")
    os.makedirs(out_dir, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[Error] Fallo al abrir el PDF: {e}", file=sys.stderr)
        sys.exit(1)

    # Autenticación
    if doc.needs_pass:
        if not args.password:
            print("[Error] El PDF está protegido. Usa el argumento --password.", file=sys.stderr)
            sys.exit(1)
        if not doc.authenticate(args.password):
            print("[Error] Contraseña incorrecta.", file=sys.stderr)
            sys.exit(1)

    page_count = doc.page_count
    if page_count == 0:
        print("[Error] El PDF no contiene páginas.", file=sys.stderr)
        sys.exit(1)

    # Selección de páginas
    if args.pages:
        indices = parse_page_ranges(args.pages, page_count)
        if not indices:
            print("[Error] El rango de páginas indicado no es válido o está vacío.", file=sys.stderr)
            sys.exit(1)
    else:
        indices = range(page_count)

    # Configuración de Renderizado
    # DPI base de PDF es 72. Calculamos el factor de zoom.
    zoom = max(1e-6, args.dpi / 72.0)
    matrix = fitz.Matrix(zoom, zoom)
    
    colorspace = fitz.csGRAY if args.grayscale else fitz.csRGB
    alpha_channel = True if args.transparent else False

    ext = "jpg" if args.fmt.lower() in ("jpg", "jpeg") else args.fmt.lower()
    
    # JPG no soporta transparencia, forzamos alpha False para evitar errores
    if ext in ("jpg", "jpeg") and alpha_channel:
        print("[Aviso] JPG no soporta transparencia. Se ignorará --transparent.")
        alpha_channel = False

    print(f"Procesando {len(indices)} páginas desde '{os.path.basename(pdf_path)}'...")
    print(f"Configuración: {args.dpi} DPI | Formato: {ext.upper()} | Grises: {args.grayscale}")

    exported = 0
    for n in indices:
        try:
            page = doc.load_page(n)
            pix = page.get_pixmap(
                matrix=matrix, 
                colorspace=colorspace, 
                alpha=alpha_channel
            )
            
            filename = f"{args.prefix}_{n + 1:03d}.{ext}"
            out_path = os.path.join(out_dir, filename)
            
            pix.save(out_path)
            print(f"  -> Guardado: {filename}")
            exported += 1
        except Exception as e:
            print(f"  [x] Error en página {n + 1}: {e}", file=sys.stderr)

    doc.close()
    if exported > 0:
        print(f"\nProceso finalizado. Imágenes guardadas en:\n{os.path.abspath(out_dir)}")
    else:
        print("\nNo se pudo exportar ninguna página.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()