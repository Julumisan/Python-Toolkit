# PDF to Images Converter

Utilidad de línea de comandos (CLI) ligera y rápida para convertir páginas de documentos PDF en archivos de imagen de alta calidad.



## Características

* **Alta Fidelidad:** Utiliza el motor de renderizado MuPDF (vía PyMuPDF) para una conversión precisa.
* **Control Total:** Permite definir la resolución (DPI), el formato de salida y el rango de páginas.
* **Privacidad:** Procesa los documentos localmente sin subirlos a la nube.
* **Soporte Avanzado:**
    * Archivos protegidos con contraseña.
    * Conversión a escala de grises.
    * Fondos transparentes (para PNG/TIFF).



## Requisitos

* Python 3.x
* `pip install -r requirements.txt`


## Uso

### Conversión Básica
Convierte todas las páginas a PNG (200 DPI por defecto):
```bash
python pdf_to_images.py documento.pdf
```
### Conversión Avanzada
Convierte solo las páginas 1, 2, 3 y 7 a JPG en alta resolución (300 DPI) y escala de grises:
```bash
python pdf_to_images.py documento.pdf --dpi 300 --fmt jpg --pages "1-3,7" --grayscale
```


## Argumentos Disponibles

| Flag | Descripción |
| :--- | :--- |
| `-o, --out` | Directorio de salida |
| `--dpi` | Resolución (Puntos por pulgada). |
| `--pages` | Rango (ej: "1-5, 10"). |
| `--password` | Para PDFs encriptados. |
| `--transparent` | Mantiene el fondo transparente (útil para logos o esquemas). |




## Autor
JLMS

