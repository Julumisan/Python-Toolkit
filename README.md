# Python-Toolkit
Suite de utilidades y herramientas prácticas desarrolladas en Python. Soluciones ligeras para problemas cotidianos de ingeniería de datos y automatización.

A diferencia de un proyecto monolítico, este repositorio sigue una arquitectura modular: cada carpeta contiene una herramienta independiente con su propia lógica y dependencias aisladas. El objetivo es proveer soluciones de "copiar y ejecutar" para tareas de análisis de datos (ETL), manipulación de archivos y automatización de procesos.

## Contenido

| Herramienta | Descripción | Dependencias Clave |
| :--- | :--- | :--- |
| **[AliExpress Analytics](./aliexpress-analytics)** | Auditoría financiera de exportaciones GDPR. Detecta gasto real y filtra cancelaciones. | `pandas`, `seaborn`,`matplotlib`, `openpyxl`|
| **[Image to RGB565](./image-to-rgb565)** | Conversor de imágenes para pantallas TFT embebidas (ESP32/Arduino). Genera binarios RAW y arrays C con corrección de color. | `Pillow` |
| **[Investment Simulator](./investment-simulator)** | Proyecciones de inversión mediante Monte Carlo y Backtesting histórico. Incluye cálculo fiscal (IRPF 2025) y ajuste por inflación. | `numpy`, `matplotlib` |
| **[PDF to Images](./pdf-to-images)** | Conversor CLI de PDF a imágenes (PNG/JPG). Soporta DPI personalizado, rangos de páginas y escala de grises. | `pymupdf` |
| **[Trade Republic Parser (WIP)](./trade-republic-parser)** | Extractor experimental de datos financieros desde PDFs de Trade Republic a Excel. Incluye cálculo de P&L. | `pdfplumber`, `pandas`, `openpyxl` |


## Uso General

Cada carpeta contiene su propio `requirements.txt`. Para usar una herramienta (ejemplo con aliexpress-analytics):

1. Entra en el directorio:
   ```bash
   cd aliexpress-analytics
   ```

2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta el script:
   ```bash
   python aliexpress_analytics.py
   ```

## Autor

Julumisan (JLMS)
