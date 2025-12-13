# Trade Republic PDF Parser (Beta)

Herramienta experimental para la extracción y estructuración de datos financieros desde los extractos PDF de Trade Republic.

> **AVISO IMPORTANTE (WIP):**
> Esta herramienta se encuentra en fase **Beta/Experimental**. El formato de los PDFs de Trade Republic no es constante y cambia frecuentemente. El script utiliza heurísticas y expresiones regulares complejas para intentar estructurar la información, pero **es posible que requiera ajustes manuales** o falle con ciertos tipos de extractos. Se recomienda revisar siempre el archivo de log generado.

## El Problema
Trade Republic provee extractos en PDF difíciles de procesar automáticamente, complicando el seguimiento de carteras grandes, el cálculo de impuestos o el análisis de P&L (Pérdidas y Ganancias).

## La Solución
Este script parsea el texto del PDF, identifica bloques de transacciones mediante patrones Regex avanzados y exporta los resultados a un Excel estructurado.

## Funcionalidades
* **Detección de Movimientos:** Compras, ventas, planes de ahorro, intereses y gastos con tarjeta.
* **Limpieza de Datos:** Algoritmos para limpiar nombres de empresas, ISINs y corregir formatos numéricos ambiguos (ej: diferenciar 1.000 de 1,000).
* **Cálculo de P&L:** Genera una pestaña resumen con el Cash Flow por activo y posición neta.
* **Modo Auditoría:** Genera un archivo `.log` detallado para verificar cómo se ha interpretado cada línea del PDF.

## Uso

1.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```
2.  Ejecutar el script:
    ```bash
    python trade_republic_parser.py
    ```
3.  Se abrirá una ventana para seleccionar tu archivo `.pdf`.
4.  El resultado se guardará como `.xlsx` en la misma carpeta que el original.

## Autor

JLMS