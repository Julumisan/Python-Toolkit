# Metadata & EXIF Viewer

Herramienta forense para la inspección profunda de metadatos ocultos en archivos de imagen. Diseñada para auditorías de privacidad, verificando si una imagen expone datos sensibles como la geolocalización o detalles técnicos del dispositivo.

## Características

* **Decodificación GPS Robusta:** Extrae y convierte coordenadas GPS desde el formato EXIF (racionales o tuplas) a decimales, generando un enlace directo a **Google Maps**.
* **Protección contra Errores:** Maneja de forma segura tipos de datos complejos de EXIF (IFDRational) para evitar fallos matemáticos (división por cero) comunes en metadatos corruptos.
* **Análisis Híbrido:**
    * **Nivel Sistema:** Muestra fechas reales de creación/modificación y tamaño.
    * **Nivel EXIF:** Filtra los datos más relevantes (Cámara, Lente, ISO, Software) eliminando ruido binario.
* **Interfaz Flexible:** Soporta "Arrastrar y Soltar" en consola o ejecución directa por argumentos (CLI), con limpieza automática de rutas (comillas, espacios escapados).

## Requisitos

* Python 3.x
* Librería Pillow: `pip install Pillow`

## Uso

### Modo Interactivo (Recomendado)
Ejecuta el script sin argumentos y arrastra archivos directamente a la terminal:
```bash
python metadata_viewer.py
```

### Modo CLI (Automatización)
Pasa la ruta del archivo como argumento:
```bash
python metadata_viewer.py "C:\Fotos\img_1234.jpg"
```

### Ejemplo de Salida (Con GPS detectado)
```text
[SISTEMA DE ARCHIVOS]
   Archivo:   IMG_2025.jpg
   Tamaño:    4.20 MB
   Creado:    2025-06-15 10:30:00

[DATOS DE CÁMARA / EXIF]
   Make                : Apple
   Model               : iPhone 13 Pro
   DateTimeOriginal    : 2025-06-15 10:30:00
   Software            : 15.0

[DATOS DE GEOLOCALIZACIÓN]
   Coordenadas: 40.416775, -3.703790
   Google Maps: [http://maps.google.com/?q=40.416775,-3.703790](http://maps.google.com/?q=40.416775,-3.703790)
   ALERTA!!!: Esta imagen revela la ubicación exacta.
```

## Autor
JLMS