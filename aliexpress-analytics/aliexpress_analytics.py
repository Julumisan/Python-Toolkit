# Project: AliExpress Financial Analyzer
# Description: Herramienta de auditoría y visualización de gastos reales basada en exportaciones GDPR de AliExpress.
#              Filtra duplicados, corrige escalas de moneda (céntimos) y valida entregas reales.
# Date: 2025-12-13
# Author: JLMS

import pandas as pd
import glob
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from datetime import timedelta

# Configuración de estilo para gráficos
sns.set_theme(style="whitegrid")
warnings.filterwarnings("ignore")

def cargar_y_procesar_datos():
    """
    Busca el primer archivo .xlsx en el directorio, carga la hoja de pedidos
    y aplica la limpieza de datos, deduplicación y conversión monetaria.
    """
    archivos = glob.glob("*.xlsx")
    if not archivos:
        print("[Error] No se ha encontrado ningún archivo .xlsx en el directorio actual.")
        return None

    archivo_objetivo = archivos[0]
    print(f"[Info] Procesando archivo: {archivo_objetivo}")

    try:
        # Se fuerza la lectura de IDs como string para evitar pérdida de precisión
        df = pd.read_excel(archivo_objetivo, sheet_name="Order Information", 
                           dtype={'parent_orderid': str, 'order_id': str})
    except Exception as e:
        print(f"[Error] Fallo al leer el archivo Excel: {e}")
        return None

    # Normalización de cabeceras
    df.columns = df.columns.str.strip().str.lower()
    
    # Definición de columnas clave
    col_pago = 'payable_amt'
    col_fecha = 'gmt_pay_order_time'
    col_exito = 'is_success_pay'
    col_razon = 'end_reason'

    # --- FASE 1: LIMPIEZA INICIAL ---
    # Filtrado por indicador de pago exitoso
    df = df[df[col_exito].astype(str).str.upper().str.contains('Y|1|TRUE', regex=True)].copy()
    
    # Conversión de fechas y eliminación de registros sin fecha de pago
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha])

    # --- FASE 2: VALIDACIÓN DE ESTADO (ENTREGADO VS CANCELADO) ---
    # Se establece una ventana de tiempo para considerar pedidos "en tránsito"
    ultima_fecha = df[col_fecha].max()
    ventana_transito = ultima_fecha - timedelta(days=90) 
    
    def validar_pedido(row):
        """
        Determina si un pedido es válido para el cómputo.
        Criterios:
        1. El comprador ha confirmado la recepción ('buyer_accept_goods').
        2. El pedido es reciente (< 90 días) y se asume en tránsito.
        """
        razon = str(row.get(col_razon, '')).lower()
        fecha = row[col_fecha]
        
        if 'buyer_accept_goods' in razon:
            return True
        if fecha > ventana_transito:
            return True
        return False

    df = df[df.apply(validar_pedido, axis=1)].copy()

    # --- FASE 3: DEDUPLICACIÓN DE TRANSACCIONES ---
    # Se agrupan los items por 'parent_orderid' para evitar sumar el total del pedido N veces
    df['transaction_id'] = df.apply(
        lambda row: str(row['parent_orderid']) if (len(str(row['parent_orderid'])) > 5 and str(row['parent_orderid']).lower() not in ['nan', '0']) 
        else str(row['order_id']), axis=1
    )
    
    # Se conserva el primer registro de cada transacción única
    df_unicos = df.drop_duplicates(subset=['transaction_id'], keep='first').copy()

    # --- FASE 4: CÁLCULOS FINALES ---
    # Conversión de céntimos a unidad monetaria estándar (división por 100)
    df_unicos['importe_real'] = pd.to_numeric(df_unicos[col_pago], errors='coerce').fillna(0) / 100.0
    
    # Generación de columnas temporales
    df_unicos['year'] = df_unicos[col_fecha].dt.year
    df_unicos['month_year'] = df_unicos[col_fecha].dt.to_period('M')

    return df_unicos

def generar_informe_texto(df):
    """Muestra un resumen estadístico en la salida estándar."""
    if df is None or df.empty: return

    col_fecha = 'gmt_pay_order_time'
    total_gasto = df['importe_real'].sum()
    total_pedidos = len(df)
    
    print("\n" + "="*50)
    print(" INFORME DE ANÁLISIS FINANCIERO ALIEXPRESS")
    print("="*50)
    print(f"Total Gasto Histórico:    {total_gasto:,.2f} EUR")
    print(f"Total Transacciones:      {total_pedidos}")
    if total_pedidos > 0:
        print(f"Ticket Medio:             {total_gasto/total_pedidos:,.2f} EUR")
    
    # Análisis de pico de gasto
    gasto_mensual = df.groupby('month_year')['importe_real'].sum()
    if not gasto_mensual.empty:
        max_mes = gasto_mensual.idxmax()
        max_valor = gasto_mensual.max()
        print(f"Mes de mayor gasto:       {max_mes} ({max_valor:,.2f} EUR)")

    print("-" * 50)
    print("TOP 5 PEDIDOS DE MAYOR VALOR:")
    top_5 = df.sort_values(by='importe_real', ascending=False).head(5)
    for i, row in top_5.iterrows():
        nombre = str(row['item_name'])[:45] + "..."
        fecha = row[col_fecha].date()
        print(f"{i+1}. [{fecha}] {row['importe_real']:8.2f} EUR | {nombre}")
    print("="*50)
    
    return gasto_mensual

def generar_visualizaciones(gasto_mensual, df):
    """Genera dashboard gráfico con Matplotlib/Seaborn."""
    if gasto_mensual is None or gasto_mensual.empty: return

    fig = plt.figure(figsize=(14, 9))
    fig.suptitle('Dashboard de Gastos AliExpress', fontsize=16)
    gs = fig.add_gridspec(2, 2)

    # 1. Serie Temporal
    ax1 = fig.add_subplot(gs[0, :])
    gasto_mensual.index = gasto_mensual.index.to_timestamp()
    sns.lineplot(x=gasto_mensual.index, y=gasto_mensual.values, ax=ax1, color='#2c3e50', linewidth=2)
    ax1.set_title('Evolución Temporal del Gasto')
    ax1.set_ylabel('EUR')
    ax1.fill_between(gasto_mensual.index, gasto_mensual.values, color='#2c3e50', alpha=0.1)

    # 2. Barras por Año
    ax2 = fig.add_subplot(gs[1, 0])
    gasto_anual = df.groupby('year')['importe_real'].sum()
    sns.barplot(x=gasto_anual.index, y=gasto_anual.values, ax=ax2, palette="Blues_d")
    ax2.set_title('Gasto Acumulado por Año')
    ax2.bar_label(ax2.containers[0], fmt='%.0f €')

    # 3. Top Items
    ax3 = fig.add_subplot(gs[1, 1])
    top_10 = df.sort_values(by='importe_real', ascending=False).head(10)
    top_10['short_name'] = top_10['item_name'].astype(str).apply(lambda x: x[:30] + '...')
    sns.barplot(x='importe_real', y='short_name', data=top_10, ax=ax3, palette="Reds_d")
    ax3.set_title('Top 10 Artículos Más Costosos')
    ax3.set_xlabel('EUR')
    ax3.set_ylabel('')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    df_procesado = cargar_y_procesar_datos()
    if df_procesado is not None:
        datos_mensuales = generar_informe_texto(df_procesado)
        generar_visualizaciones(datos_mensuales, df_procesado)