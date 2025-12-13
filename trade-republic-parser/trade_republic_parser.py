# Project: Trade Republic PDF Parser (WIP)
# Description: Herramienta de extracción de datos financieros desde extractos PDF de Trade Republic.
#              Convierte el formato no estructurado del banco en un Excel (XLSX) legible con cálculo de P&L.
#              Nota: Herramienta en fase beta debido a la variabilidad del formato PDF de origen.
# Date: 2025-12-13
# Author: JLMS

import pdfplumber
import pandas as pd
import re
import os
import tkinter as tk
import logging
from tkinter import filedialog, messagebox

# --- CONFIGURACIÓN DE LOGGING (MODO AUDITORÍA) ---
# Se determina la ruta absoluta del script para guardar el log en la misma carpeta
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_LOG = os.path.join(DIRECTORIO_BASE, 'debug_trade_republic.log')

# Se configura el logging para asegurar la creación inmediata del archivo
logging.basicConfig(
    filename=RUTA_LOG,
    level=logging.INFO, 
    format='%(asctime)s - %(message)s', # Se añade timestamp para mejor trazabilidad
    datefmt='%H:%M:%S',
    filemode='w',
    encoding='utf-8',
    force=True # Se fuerza la re-configuración si ya existiera una instancia
)

# Se escribe una entrada inicial para forzar la creación física del archivo en disco
logging.info("--- INICIO DE EJECUCIÓN DEL PROGRAMA ---")


# --- PATRONES REGEX ---
REGEX_INICIO_TRANSACCION = r"^(\d{1,2})\s+([a-z]{3,4})" 
REGEX_ANIO = r"\b(20\d{2})\b"
REGEX_ISIN = r"\b([A-Z]{2}[A-Z0-9]{9}[0-9])\b" 

# Regex estricta para importes monetarios (evita falsos positivos con cantidades)
# Se exigen grupos de 3 dígitos tras punto (1.319,00) o número sin puntos.
REGEX_PRECIO_TOTAL = r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})\s*€"

def limpiar_euros(str_num):
    """Se limpian las cadenas de texto monetarias para convertirlas al formato float estándar."""
    if not str_num: return 0.0
    clean = str_num.replace("€", "").strip()
    clean = clean.replace(".", "") # Se quitan puntos de mil
    clean = clean.replace(",", ".") # Se cambia coma a punto decimal
    try:
        return float(clean)
    except ValueError:
        return 0.0

def limpiar_cantidad(str_num):
    """
    Se interpretan las cantidades numéricas resolviendo la ambigüedad del formato europeo.
    Se diferencia entre 1.000 (mil) y 1.45 (uno coma cuarenta y cinco).
    """
    if not str_num: return 0.0
    clean = str_num.strip()
    
    # Caso 1: Punto y Coma -> Estándar (1.200,50)
    if "." in clean and "," in clean:
        clean = clean.replace(".", "").replace(",", ".")
        return float(clean)
    
    # Caso 2: Solo coma -> Decimal europeo (10,5)
    if "," in clean:
        clean = clean.replace(",", ".")
        return float(clean)
        
    # Caso 3: Solo punto -> Ambiguo (1.000 vs 1.5)
    if "." in clean:
        partes = clean.split(".")
        parte_decimal = partes[-1]
        # Heurística: Si tiene 3 decimales exactos, se asume mil (1.000)
        if len(parte_decimal) == 3:
            clean = clean.replace(".", "")
        else:
            pass # Se considera decimal
            
    try:
        return float(clean)
    except ValueError:
        return 0.0

def limpiar_nombre_empresa(nombre_sucio, isin):
    """Se elimina ruido y palabras técnicas del nombre de la empresa/activo."""
    if not nombre_sucio: return "Desconocido"
    
    nombre = nombre_sucio.replace(isin, "")
    
    basura = [
        "Comercio", "Buy trade", "Sell trade", "Savings plan execution", "quantity:", 
        "Transferencia", "Tarjeta", "Ingreso aceptado", "Best Turbo auf", "Unlimited Turbo auf", "Turbo auf",
        "Mini Future auf", "Warrant auf", "Open End Turbo auf", "Mini Future"
    ]
    
    for b in basura:
        nombre = re.sub(b, "", nombre, flags=re.IGNORECASE)
        
    # Limpieza de residuos técnicos (prefijos de mercado, fechas residuales, divisa)
    nombre = re.sub(r"(DL-|EO\s*)-?[\s,]*[\d\.,]+", "", nombre, flags=re.IGNORECASE)
    nombre = re.sub(r",\s*\d+\s*\d*", "", nombre) 
    nombre = re.sub(r"\b20\d{2}\b", "", nombre) 
    nombre = re.sub(r"[€$]", "", nombre) 
    
    nombre = re.sub(r"\s+", " ", nombre)
    nombre = re.sub(r"[,\.-]+$", "", nombre.strip())
    
    return nombre.strip() if nombre.strip() else "Desconocido"

def detectar_tipo_activo(bloque_texto):
    """Se clasifica el activo entre Stock (Acción/ETF) o Derivado."""
    desc_upper = bloque_texto.upper()
    palabras_clave_derivados = ["TURBO", "MINI FUTURE", "WARRANT", "BEST", "OPEN END", "KO", "FACTOR"]
    for palabra in palabras_clave_derivados:
        if palabra in desc_upper: return "Derivado"
    return "Stock"

def procesar_pdf(ruta_pdf):
    """Núcleo de ejecución: lectura de PDF, parsing de bloques y exportación."""
    print(f"Procesando: {ruta_pdf}...")
    
    texto_completo = ""
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    texto_completo += text + "\n"
    except Exception as e:
        msg = f"No se pudo leer el PDF: {e}"
        messagebox.showerror("Error", msg)
        return

    # Limpieza inicial de caracteres
    texto_limpio = texto_completo.replace('"', '').replace('“', '').replace('”', '')
    lineas = texto_limpio.split('\n')
    
    # --- FASE 1: AGRUPACIÓN POR BLOQUES ---
    bloques_transaccion = []
    bloque_actual_texto = []
    
    for i, linea in enumerate(lineas):
        linea = linea.strip()
        if not linea: continue

        match_inicio = re.match(REGEX_INICIO_TRANSACCION, linea, re.IGNORECASE)

        if match_inicio:
            if bloque_actual_texto:
                bloques_transaccion.append(" ".join(bloque_actual_texto))
            bloque_actual_texto = [linea]
        else:
            if bloque_actual_texto:
                bloque_actual_texto.append(linea)

    if bloque_actual_texto:
        bloques_transaccion.append(" ".join(bloque_actual_texto))

    print(f"Se encontraron {len(bloques_transaccion)} bloques potenciales.")

    # --- FASE 2: PARSING Y EXTRACCIÓN ---
    data = []
    
    logging.info("INFORME DE AUDITORÍA DE EXTRACCIÓN")
    logging.info("==========================================================================================")

    for idx, bloque in enumerate(bloques_transaccion):
        if "RESUMEN DE ESTADO" in bloque or "BALANCE INICIAL" in bloque: continue
        # Filtro para evitar rangos de fechas que parecen transacciones
        if re.search(r"\d{1,2}\s+[a-z]{3,4}.*?-.*?\d{1,2}\s+[a-z]{3,4}", bloque, re.IGNORECASE):
            continue

        match_inicio = re.match(REGEX_INICIO_TRANSACCION, bloque, re.IGNORECASE)
        if not match_inicio: continue
        
        dia, mes = match_inicio.groups()
        match_anio = re.search(REGEX_ANIO, bloque)
        anio = match_anio.group(1) if match_anio else "2025"
        fecha = f"{dia} {mes} {anio}"

        # Clasificación del movimiento
        tipo_movimiento = "Desconocido"
        if "Comercio" in bloque: tipo_movimiento = "Comercio"
        elif "Transferencia" in bloque: tipo_movimiento = "Transferencia"
        elif "intereses" in bloque.lower() or "interest payment" in bloque.lower(): tipo_movimiento = "Intereses"
        elif "Tarjeta" in bloque or "Transacción con tarjeta" in bloque: tipo_movimiento = "Tarjeta"
        elif "Recompensa" in bloque: tipo_movimiento = "Recompensa"
        
        direccion = ""
        if "Buy trade" in bloque: direccion = "Compra"
        elif "Sell trade" in bloque: direccion = "Venta"
        elif "Savings plan execution" in bloque: direccion = "Compra (Plan)"
        
        isin_match = re.search(REGEX_ISIN, bloque)
        isin = isin_match.group(1) if isin_match else ""

        # Extracción de Cantidad (Acciones/Títulos)
        cantidad = 0.0
        match_qty_label = re.search(r"(?:quantity|Anzahl):", bloque, re.IGNORECASE)
        
        if match_qty_label:
            texto_post_qty = bloque[match_qty_label.end():]
            
            # Limpieza específica para aislar la cantidad de otros números cercanos
            texto_limpio_qty = re.sub(REGEX_PRECIO_TOTAL, "", texto_post_qty)
            texto_limpio_qty = re.sub(r"\b202\d\b", "", texto_limpio_qty)
            texto_limpio_qty = re.sub(r"[a-zA-Z]+", "", texto_limpio_qty)
            
            numeros_candidatos = re.findall(r"[\d\.,]+", texto_limpio_qty)
            numeros_candidatos = [n for n in numeros_candidatos if any(c.isdigit() for c in n)]
            
            if numeros_candidatos:
                # El último candidato suele ser la cantidad correcta en líneas rotas
                candidato_final = numeros_candidatos[-1]
                cantidad = limpiar_cantidad(candidato_final)
                logging.info(f"[DEBUG QTY] Texto crudo: {texto_post_qty[:30]}... -> Cantidad detectada: {cantidad}")

        # Extracción de Importes Monetarios
        importes_encontrados_raw = re.findall(REGEX_PRECIO_TOTAL, bloque)
        importes_encontrados_float = [limpiar_euros(x) for x in importes_encontrados_raw]
        
        euros_totales = 0.0
        flujo = ""
        str_entrada = "-"
        str_salida = "-"
        str_balance = "-"

        if importes_encontrados_float:
            monto_operacion = importes_encontrados_float[0]
            monto_raw = importes_encontrados_raw[0]
            
            if len(importes_encontrados_raw) > 1:
                str_balance = importes_encontrados_raw[-1]
            
            if direccion in ["Compra", "Compra (Plan)"] or tipo_movimiento == "Tarjeta":
                euros_totales = monto_operacion
                flujo = "Salida"
                str_salida = monto_raw
            elif direccion == "Venta" or tipo_movimiento in ["Intereses", "Transferencia", "Recompensa"]:
                if "Ingreso aceptado" in bloque or "Incoming transfer" in bloque or "Recompensa" in bloque:
                    euros_totales = monto_operacion
                    flujo = "Entrada"
                    str_entrada = monto_raw
                else:
                    if tipo_movimiento == "Transferencia" and "Outgoing" in bloque:
                            euros_totales = monto_operacion
                            flujo = "Salida"
                            str_salida = monto_raw
                    elif direccion == "Venta": 
                        euros_totales = monto_operacion
                        flujo = "Entrada"
                        str_entrada = monto_raw
                    else:
                        euros_totales = monto_operacion
                        flujo = "Entrada"
                        str_entrada = monto_raw

        empresa = "N/A"
        tipo_activo = "N/A"
        
        if isin:
            match_nombre = re.search(r"(Buy trade|Sell trade|Savings plan execution)(.*?)(quantity:|$)", bloque, re.IGNORECASE)
            if match_nombre:
                raw_name = match_nombre.group(2)
                empresa = limpiar_nombre_empresa(raw_name, isin)
            tipo_activo = detectar_tipo_activo(bloque)
        elif tipo_movimiento == "Tarjeta" or tipo_movimiento == "Transferencia":
            desc_temp = bloque
            desc_temp = re.sub(REGEX_PRECIO_TOTAL, "", desc_temp)
            desc_temp = re.sub(REGEX_INICIO_TRANSACCION, "", desc_temp)
            desc_temp = re.sub(REGEX_ANIO, "", desc_temp)
            desc_temp = desc_temp.replace("Transferencia", "").replace("Tarjeta", "").replace("Transacción con tarjeta", "")
            desc_temp = desc_temp.replace("Ingreso aceptado:", "").replace("Incoming transfer from", "")
            empresa = desc_temp.strip()[:50]

        precio_unidad = 0.0
        if cantidad > 0 and euros_totales > 0:
            precio_unidad = euros_totales / cantidad

        # --- LOGGING PARA AUDITORÍA ---
        tipo_final_log = direccion if direccion else tipo_movimiento
        
        alerta = ""
        if euros_totales > 10000:
            alerta = " [!!! ALERTA CRÍTICA: VALOR > 10k - REVISAR !!!]"

        logging.info(f"Línea Original:\n{bloque.strip()}")
        logging.info("")
        logging.info(f"Fecha: {fecha} | TIPO: {tipo_final_log} | DESC: {empresa} | CANT: {cantidad} | IN: {str_entrada} | OUT: {str_salida} | BAL: {str_balance}{alerta}")
        logging.info("-" * 100)

        if tipo_movimiento == "Comercio" or isin:
            data.append({
                "Fecha": fecha,
                "Tipo Movimiento": direccion if direccion else tipo_movimiento,
                "Cantidad": cantidad,
                "Euros Totales": euros_totales * (-1 if flujo == "Salida" else 1),
                "Precio/Unidad": precio_unidad,
                "Empresa": empresa,
                "ISIN": isin,
                "Activo": tipo_activo
            })

    if not data:
        messagebox.showwarning("Aviso", "No se encontraron datos procesables en el PDF.")
        return

    # --- FASE 3: GENERACIÓN DE EXCEL Y P&L ---
    df = pd.DataFrame(data)
    
    # Cálculos P&L (Profit & Loss)
    def get_signed_quantity(row):
        if "Compra" in row['Tipo Movimiento']:
            return row['Cantidad']
        elif "Venta" in row['Tipo Movimiento']:
            return -row['Cantidad']
        return 0

    df['Cantidad_Signed'] = df.apply(get_signed_quantity, axis=1)

    df_pl = df.groupby(["ISIN"]).agg({
        "Empresa": "first",
        "Activo": "first",
        "Euros Totales": "sum",
        "Cantidad_Signed": "sum"
    }).reset_index()
    
    df_pl.rename(columns={"Euros Totales": "Beneficio/Pérdida (Cash Flow)", "Cantidad_Signed": "Posición Neta"}, inplace=True)
    df_pl = df_pl[["Empresa", "Activo", "Beneficio/Pérdida (Cash Flow)", "Posición Neta", "ISIN"]]
    
    total_pl = df_pl["Beneficio/Pérdida (Cash Flow)"].sum()
    row_total = pd.DataFrame([{"Empresa": "TOTAL GLOBAL", "Activo": "-", "Beneficio/Pérdida (Cash Flow)": total_pl, "Posición Neta": 0, "ISIN": "-"}])
    df_pl = pd.concat([df_pl, row_total], ignore_index=True)

    output_file = ruta_pdf.replace(".pdf", "_procesado.xlsx")
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df[["Tipo Movimiento", "Cantidad", "Euros Totales", "Precio/Unidad", "Empresa", "Activo", "Fecha", "ISIN"]].to_excel(writer, sheet_name="Movimientos", index=False)
            df_pl.to_excel(writer, sheet_name="Beneficio-Perdida", index=False)
        messagebox.showinfo("Éxito", f"Archivo generado:\n{output_file}\n\nRevisa 'debug_trade_republic.log' para detalles de auditoría.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar Excel: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() # Se oculta la ventana principal, no se destruye aún
    root.attributes('-topmost', True)
    
    try:
        print("Esperando selección de archivo PDF...")
        root.update()
        file_path = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        root.attributes('-topmost', False)
        
        if file_path:
            procesar_pdf(file_path)
        else:
            print("Operación cancelada por el usuario.")
            
    finally:
        # Se asegura el cierre correcto de recursos
        logging.shutdown()
        root.destroy()