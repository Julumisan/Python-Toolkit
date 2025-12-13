# **AliExpress Financial Analyzer**

Script en Python para analizar las exportaciones de datos GDPR de AliExpress (.xlsx).



## El Problema

Los archivos exportados de AliExpress suelen tener problemas que dificultan saber el gasto real:

- Precios en céntimos (multiplicados por 100).

- Filas duplicadas (una fila por artículo en pedidos múltiples, repitiendo el precio total).

- Pedidos cancelados o no pagados incluidos en la suma.



## La Solución

Este script limpia los datos, deduplica las transacciones basándose en el ID del pedido y genera un reporte visual con gráficos e información relevante.



## Requisitos

- Python 3.x

- Librerías: pip install -r requirements.txt



## Uso

1. Solicita tus datos en AliExpress [https://privacy.aliexpress.com] (Privacy -> Download Data). 

Coloca el archivo .xlsx en la misma carpeta que el script.

Ejecuta: python aliexpress_analytics.py



## Autor

Julumisan (JLMS)