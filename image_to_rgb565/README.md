# Image to RGB565 Converter

Herramienta de automatización para convertir imágenes estándar (JPG, PNG, BMP) a formato **RGB565 (16-bit)**. Diseñada específicamente para desarrolladores de sistemas embebidos (ESP32, Arduino, STM32) que trabajan con pantallas TFT (ILI9341, ST7789, etc.).

## El Problema
Las pantallas TFT gestionadas por microcontroladores suelen requerir datos de imagen en formato "crudo" (raw) RGB565 (5 bits rojo, 6 verde, 5 azul). Convertir imágenes manualmente o usar herramientas online es lento y a menudo no permite corregir problemas de hardware comunes como la inversión de colores o el intercambio de canales rojo/azul.

## Características Clave
* **Smart Crop (Recorte Inteligente):** Redimensiona la imagen manteniendo la relación de aspecto y recorta el centro sobrante, evitando deformaciones.
* **Formatos de Salida:**
    * `.raw`: Archivo binario puro, ideal para guardar en sistemas de archivos (SPIFFS, LittleFS, SD Card).
    * `.h`: Archivo de cabecera C con array `PROGMEM`, listo para compilar dentro del firmware.
* **Corrección de Hardware:** Flags para solucionar problemas comunes de controladores de pantalla (Inversión de color, Swap R/B).
* **Procesamiento por Lotes:** Puede convertir una carpeta entera de una sola vez.

## Requisitos
* Python 3.x
* Librería Pillow: `pip install Pillow`

## Uso

### 1. Conversión Básica (Carpeta actual)
Busca todas las imágenes en la carpeta donde está el script y las convierte a 240x320 (por defecto):
```bash
python image_to_rgb565.py
```

### 2. Conversión Específica (Archivo único)
Convierte una imagen específica definiendo dimensiones personalizadas:
```bash
python image_to_rgb565.py imagen.jpg -W 128 -H 128
```

### 3. Generación de Código C (Para Firmware)
Si prefieres incrustar la imagen en el código en lugar de leerla de una SD:
```bash
python image_to_rgb565.py logo.png --c-header --no-raw
```
Esto generará un archivo `logo.h` con un array `const uint16_t`.

### 4. Corrección de Colores (Troubleshooting)
Si en tu pantalla los colores salen "extraños" (ej: caras azules o fondo negro que se ve blanco):
```bash
# Corrige canales intercambiados (Rojo <-> Azul)
python image_to_rgb565.py imagen.jpg --swap

# Corrige colores negativos/invertidos
python image_to_rgb565.py imagen.jpg --invert
```

## Argumentos Disponibles

| Flag | Descripción |
| :--- | :--- |
| `source` | Archivo o carpeta a procesar (por defecto: carpeta actual). |
| `-W`, `--width` | Ancho objetivo de la pantalla (Default: 240). |
| `-H`, `--height` | Alto objetivo de la pantalla (Default: 320). |
| `--c-header` | Genera archivo .h (array C PROGMEM). |
| `--no-raw` | No genera el archivo binario .raw. |
| `--swap` | Intercambia canales Rojo y Azul (Fix para pantallas BGR). |
| `--invert` | Invierte los bits de color (Fix para efecto negativo). |
| `--delete` | Borra la imagen original tras la conversión exitosa. |

## Autor
JLMS