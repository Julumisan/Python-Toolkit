# Simulador de Inversión Pro

Herramienta de escritorio (GUI) para proyectar escenarios de inversión a largo plazo. Combina modelos estadísticos (Monte Carlo) con fiscalidad real y opciones de simulación histórica.

## Características

* **Modelo Híbrido:**
    * **Monte Carlo:** Proyección basada en Movimiento Browniano Geométrico (GBM) con parámetros configurables (μ, σ).
    * **Modo Empírico:** Capacidad de cargar un CSV con rendimientos históricos reales para realizar *backtesting* o proyecciones basadas en datos pasados.
* **Fiscalidad Real:** Cálculo automático del IRPF español (Base del Ahorro 2025) sobre la plusvalía generada al final del periodo.
* **Ajuste por Inflación:** Opción para visualizar todos los resultados en "Euros Reales" (descontando el efecto de la inflación anual).
* **DCA Dinámico:** Configuración de aportaciones mensuales con crecimiento anual porcentual (para simular subidas de sueldo o ajustes al IPC).
* **Probabilidad de Éxito:** Cálculo de la probabilidad porcentual de alcanzar un objetivo financiero específico año a año.

## Instalación

Requiere Python 3.x y las librerías listadas en `requirements.txt`.

1.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```
2.  Ejecutar el simulador:
    ```bash
    python investment_simulator.py
    ```

*Nota: En sistemas Linux, es posible que necesites instalar el soporte para Tkinter por separado (ej: `sudo apt-get install python3-tk`).* No lo he probado en Linux, pero debería funcionar con el soporte.

## Uso

1.  **Parámetros de Entrada:** Configura tu capital inicial, aportación mensual y perfil de riesgo en el panel izquierdo.
2.  **Escenarios:** Utiliza los preajustes (Conservador, Base, Agresivo) o define tu propia rentabilidad y volatilidad esperada.
3.  **Simulación:** Pulsa "Actualizar" para ejecutar 1,000+ simulaciones simultáneas.
4.  **Análisis:**
    * **Gráfico:** Visualiza la mediana y las bandas de probabilidad (percentiles 10 y 90).
    * **Tabla:** Consulta los datos numéricos exactos año a año en la pestaña "Datos".
5.  **Exportación:** Guarda los resultados en CSV para Excel o descarga la gráfica en PNG.

## Autor

JLMS