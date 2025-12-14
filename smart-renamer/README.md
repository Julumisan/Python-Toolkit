# Smart Media Renamer

Utilidad de organización de archivos que normaliza los nombres caóticos de imágenes y videos (especialmente de WhatsApp y capturas de pantalla de Android) a un formato de fecha estandarizado y legible.

## El Problema
Las aplicaciones móviles guardan archivos con nombres inconsistentes:
* `IMG-20231201-WA0001.jpg`
* `Screenshot_2023-12-01-10-00-00... .jpg`
* `WhatsApp Image 2023-12-01... .jpeg`

Esto dificulta ordenarlos cronológicamente en el PC.

## La Solución
Este script escanea una carpeta, detecta patrones conocidos mediante Expresiones Regulares (Regex) y los renombra a un formato uniforme: `YYYY_MM_DD_HH-MM-SS`.

## Características
* **Seguridad por Defecto:** Se ejecuta en modo "Simulación" (Dry-Run) a menos que se especifique lo contrario.
* **Anti-Colisiones:** Si el nuevo nombre ya existe, añade un contador automático (`_1`, `_2`) en lugar de sobrescribir el archivo.
* **Patrones Soportados:** WhatsApp (Img/Vid), Android Stock Cam, Screenshots, etc.

## Uso

### 1. Simulación (Recomendado)
Ver qué cambios se harían sin tocar nada:
```bash
python smart_renamer.py "C:\Mis Fotos\WhatsApp"
```
### 2. Ejecutar cambios
Aplicar los cambios de nombre reales:

```bash
python smart_renamer.py "C:\Mis Fotos\WhatsApp" --run
```
### 3. Carpeta actual
Si ejecutas el script dentro de la carpeta que quieres ordenar:

```bash
python smart_renamer.py --run
```

## Autor
JLMS