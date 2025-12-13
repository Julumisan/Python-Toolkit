# Project: Investment Simulator Pro
# Description: Simulador de inversión con interfaz gráfica (Tkinter).
#              Incluye proyecciones Monte Carlo, simulación histórica (Backtesting),
#              ajuste por inflación y cálculo de fiscalidad IRPF España (2025).
# Author: JLMS

import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ------------------ Parámetros Globales ------------------
SEED = 42  # Semilla para reproducibilidad (None para aleatorio)
rng = np.random.default_rng(SEED)

DEFAULT_YEARS = 30
DEFAULT_SIMS = 1000

# Escenarios predefinidos de rentabilidad/volatilidad
SCENARIOS = {
    "Conservador": {"mu_pct": 4.0, "sigma_pct": 10.0},
    "Base":        {"mu_pct": 7.0, "sigma_pct": 15.0},
    "Agresivo":    {"mu_pct": 10.0, "sigma_pct": 25.0},
}

# Tramos IRPF base del ahorro (residentes España) 2025
# Formato: (Límite Inferior, Límite Superior, Tipo Impositivo)
IRPF_TRAMOS_2025 = [
    (0.0,       6000.0,    0.19),
    (6000.0,    50000.0,   0.21),
    (50000.0,   200000.0,  0.23),
    (200000.0,  300000.0,  0.27),
    (300000.0,  float("inf"), 0.30),
]

# ------------------ Funciones Auxiliares ------------------
def parse_money(s: str) -> float:
    """Convierte cadenas de texto con formato moneda a float."""
    s = (
        s.strip()
        .replace("€", "")
        .replace("EUR", "")
        .replace("eur", "")
        .replace(" ", "")
        .replace("_", "")
    )
    if s == "":
        return 0.0
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    return float(s)

def parse_percent(s: str) -> float:
    """Convierte cadenas de porcentaje a float."""
    s = s.strip().replace("%", "").replace(" ", "").replace(",", ".")
    if s == "":
        return 0.0
    return float(s)

def fmt_eur(x: float) -> str:
    """Formatea un float como moneda Euro."""
    return f"{x:,.2f} €"

def aplicar_tramos_irpf(plusvalia: float) -> float:
    """Calcula el impuesto a pagar según los tramos de la base del ahorro 2025."""
    if plusvalia <= 0.0:
        return 0.0
    impuesto = 0.0
    base_restante = plusvalia
    for li, ls, tipo in IRPF_TRAMOS_2025:
        if base_restante <= 0:
            break
        # Tramo aplicable en este escalón
        tramo = min(base_restante, ls - li)
        if tramo > 0:
            impuesto += tramo * tipo
            base_restante -= tramo
    return impuesto

def leer_rendimientos_csv(path: str):
    """
    Lee un archivo CSV para extraer una columna de rendimientos históricos.
    Detecta automáticamente columnas comunes ('return', 'pct', etc.).
    Retorna un array numpy de rendimientos mensuales en decimal.
    """
    datos = []
    headers = None
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("El archivo CSV está vacío.")

    # Detección de encabezado
    try:
        [float(x) for x in rows[0]]
        start_idx = 0
        headers = None
    except Exception:
        headers = [h.strip().lower() for h in rows[0]]
        start_idx = 1

    col_idx = None
    if headers:
        candidatos = ["return", "rend", "ret", "pct", "porcentaje", "r"]
        for c in candidatos:
            if c in headers:
                col_idx = headers.index(c)
                break
        
        # Si no encuentra nombre, intenta detectar columna numérica
        if col_idx is None:
            for j in range(len(headers)):
                try:
                    float(rows[start_idx][j].replace("%","").replace(",","."))
                    col_idx = j
                    break
                except Exception:
                    continue
            if col_idx is None:
                raise ValueError("No se encontró ninguna columna numérica válida.")

    # Procesamiento de filas
    for i in range(start_idx, len(rows)):
        if not rows[i]:
            continue
        try:
            val_raw = rows[i][col_idx if col_idx is not None else 0]
            x = val_raw.strip().replace("%","").replace(",", ".")
            if x == "":
                continue
            v = float(x)
            # Si el valor absoluto > 1.5, se asume que es porcentaje (ej: 7.0) y se pasa a decimal (0.07)
            if abs(v) > 1.5:
                v = v / 100.0
            datos.append(v)
        except (ValueError, IndexError):
            continue

    arr = np.array(datos, dtype=float)
    if arr.size == 0:
        raise ValueError("No se pudieron extraer datos numéricos del CSV.")
    return arr

# ------------------ Interfaz Gráfica (App) ------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Inversión — Pro (Monte Carlo + Empírico)")
        self.geometry("1180x720")
        self.minsize(1024, 640)

        self._sync_guard = False
        self.empirical_returns = None 
        self._build_ui()
        self._simulate_and_render()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        self.tab_g = ttk.Frame(nb)
        self.tab_t = ttk.Frame(nb)
        nb.add(self.tab_g, text="Simulación (Gráfica)")
        nb.add(self.tab_t, text="Datos (Tabla)")
        nb.pack(fill="both", expand=True)

        left = ttk.Frame(self.tab_g, padding=12)
        right = ttk.Frame(self.tab_g, padding=12)
        left.pack(side="left", fill="y")
        right.pack(side="right", fill="both", expand=True)

        # ------------ Variables de Control ------------
        self.v_cap_ini    = tk.StringVar(value="10.000")
        self.v_aport_m    = tk.StringVar(value="300")
        self.v_aport_crec = tk.StringVar(value="2.0%")
        self.v_years      = tk.IntVar(value=DEFAULT_YEARS)
        self.v_sims       = tk.IntVar(value=DEFAULT_SIMS)

        self.v_mu_txt    = tk.StringVar(value="7.00%")
        self.v_mu_sld    = tk.DoubleVar(value=7.0)
        self.v_sigma_txt = tk.StringVar(value="15.00%")

        self.v_infl      = tk.StringVar(value="2.00%")
        self.v_fee       = tk.StringVar(value="0.10%")
        self.v_objetivo  = tk.StringVar(value="300000")

        self.v_real      = tk.BooleanVar(value=False)
        self.v_use_tax   = tk.BooleanVar(value=True)
        self.v_mode_emp  = tk.BooleanVar(value=False)
        self.v_scenario  = tk.StringVar(value="Base")

        # ------------ Panel Izquierdo (Inputs) ------------
        ttk.Label(left, text="Capital inicial").pack(anchor="w")
        ttk.Entry(left, textvariable=self.v_cap_ini, width=28).pack(anchor="w", pady=(0, 8))

        ttk.Label(left, text="Aportación mensual (DCA)").pack(anchor="w")
        ttk.Entry(left, textvariable=self.v_aport_m, width=28).pack(anchor="w", pady=(0, 4))

        ttk.Label(left, text="Crecimiento anual aportación (%)").pack(anchor="w")
        ttk.Entry(left, textvariable=self.v_aport_crec, width=28).pack(anchor="w", pady=(0, 10))

        # Selector de Escenarios
        frame_scen = ttk.Frame(left)
        frame_scen.pack(anchor="w", pady=(0, 6))
        ttk.Label(frame_scen, text="Escenario:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(frame_scen, width=14, state="readonly",
                     values=list(SCENARIOS.keys()), textvariable=self.v_scenario)\
            .grid(row=0, column=1, padx=(6,0))

        # Rentabilidad Esperada (Mu)
        ttk.Label(left, text="Rendimiento anual esperado μ (%)").pack(anchor="w")
        ttk.Scale(left, from_=-5.0, to=30.0, orient="horizontal",
                  variable=self.v_mu_sld, command=self._on_mu_scale, length=260).pack(anchor="w", pady=(2, 4))
        ttk.Entry(left, textvariable=self.v_mu_txt, width=28).pack(anchor="w", pady=(0, 8))

        # Volatilidad (Sigma)
        ttk.Label(left, text="Desviación típica anual σ (%)").pack(anchor="w")
        ttk.Entry(left, textvariable=self.v_sigma_txt, width=28).pack(anchor="w", pady=(0, 10))

        # Opción Modo Empírico
        ttk.Checkbutton(left, text="Usar CSV histórico (modo empírico)", variable=self.v_mode_emp)\
            .pack(anchor="w", pady=(0, 4))
        ttk.Button(left, text="Cargar CSV…", command=self._load_csv).pack(anchor="w", pady=(0, 10))

        # Inflación y Costes
        ttk.Label(left, text="Inflación anual (%)").pack(anchor="w")
        ttk.Entry(left, textvariable=self.v_infl, width=28).pack(anchor="w", pady=(0, 6))

        ttk.Label(left, text="Comisión anual (TER, %)").pack(anchor="w")
        ttk.Entry(left, textvariable=self.v_fee, width=28).pack(anchor="w", pady=(0, 10))

        # Opciones de Visualización
        ttk.Checkbutton(left, text="Mostrar en euros reales (ajustado inflación)", variable=self.v_real)\
            .pack(anchor="w", pady=(0, 8))
        ttk.Checkbutton(left, text="Aplicar IRPF España 2025 (Plusvalía)", variable=self.v_use_tax)\
            .pack(anchor="w", pady=(0, 12))

        # Configuración Simulación
        misc = ttk.Frame(left)
        misc.pack(anchor="w", pady=(0, 8))
        ttk.Label(misc, text="Años:").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(misc, from_=1, to=60, textvariable=self.v_years, width=6).grid(row=0, column=1, padx=(4, 10))
        ttk.Label(misc, text="Simulaciones:").grid(row=0, column=2, sticky="w")
        ttk.Spinbox(misc, from_=100, to=100000, increment=100, textvariable=self.v_sims, width=10)\
            .grid(row=0, column=3, padx=(4, 0))

        ttk.Label(left, text="Objetivo de capital (probabilidad)").pack(anchor="w")
        ttk.Entry(left, textvariable=self.v_objetivo, width=28).pack(anchor="w", pady=(0, 12))

        # Botonera
        bar = ttk.Frame(left)
        bar.pack(anchor="w", pady=(2, 12))
        ttk.Button(bar, text="Aplicar escenario", command=self._apply_scenario).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(bar, text="Actualizar", command=self._simulate_and_render).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(bar, text="Exportar CSV", command=self._export_csv).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(bar, text="Guardar PNG", command=self._save_png).grid(row=0, column=3)

        # Etiqueta de Resumen
        self.lbl_resumen = ttk.Label(left, text="", justify="left")
        self.lbl_resumen.pack(anchor="w", pady=(0, 4))

        # Sincronización Slider/Texto
        self.v_mu_txt.trace_add("write", self._on_mu_text_changed)

        # ------------ Panel Derecho (Gráfico) ------------
        fig = Figure(figsize=(7.6, 4.6), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Tiempo (años)")
        self.ax.set_ylabel("Capital")
        self.ax.grid(True, linestyle="--", linewidth=0.6)
        self.canvas = FigureCanvasTkAgg(fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ------------ Pestaña Datos (Tabla) ------------
        container = ttk.Frame(self.tab_t, padding=12)
        container.pack(fill="both", expand=True)
        cols = ("anio", "aportado", "mediana", "p10", "p90", "p_obj")
        self.tree = ttk.Treeview(container, columns=cols, show="headings", height=20)
        
        heads = [("anio","Año",70), ("aportado","Aportado acum.",160),
                 ("mediana","Mediana",160), ("p10","P10",140), ("p90","P90",140),
                 ("p_obj","Prob. ≥ objetivo",150)]
        
        for c, t, w in heads:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="e" if c!="anio" else "center")
        
        self.tree.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")

    # ------------- Lógica de Eventos -------------
    def _on_mu_scale(self, _=None):
        if self._sync_guard: return
        try:
            self._sync_guard = True
            self.v_mu_txt.set(f"{self.v_mu_sld.get():.2f}%")
        finally:
            self._sync_guard = False

    def _on_mu_text_changed(self, *_):
        if self._sync_guard: return
        try:
            mu = parse_percent(self.v_mu_txt.get())
        except Exception:
            return
        mu = max(min(mu, 50.0), -20.0)
        try:
            self._sync_guard = True
            self.v_mu_sld.set(mu)
        finally:
            self._sync_guard = False

    def _apply_scenario(self):
        sc = SCENARIOS.get(self.v_scenario.get(), None)
        if not sc: return
        self.v_mu_txt.set(f"{sc['mu_pct']:.2f}%")
        self.v_sigma_txt.set(f"{sc['sigma_pct']:.2f}%")

    def _load_csv(self):
        path = filedialog.askopenfilename(
            title="Selecciona CSV de rendimientos",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")]
        )
        if not path: return
        try:
            self.empirical_returns = leer_rendimientos_csv(path)
            self.v_mode_emp.set(True)
            messagebox.showinfo("Carga exitosa", f"Se han importado {self.empirical_returns.size} registros.")
        except Exception as e:
            messagebox.showerror("Error de lectura", str(e))

    # ------------- Motor de Simulación -------------
    def _simulate_and_render(self):
        try:
            cap0     = parse_money(self.v_cap_ini.get())
            aport_m  = parse_money(self.v_aport_m.get())
            crec_pct = parse_percent(self.v_aport_crec.get())
            years    = int(self.v_years.get())
            n_sims   = int(self.v_sims.get())

            infl     = parse_percent(self.v_infl.get())/100.0
            fee      = parse_percent(self.v_fee.get())/100.0
            mu       = parse_percent(self.v_mu_txt.get())/100.0
            sigma    = max(0.0, parse_percent(self.v_sigma_txt.get())/100.0)
            objetivo = parse_money(self.v_objetivo.get())

            use_real = bool(self.v_real.get())
            use_tax  = bool(self.v_use_tax.get())
            use_emp  = bool(self.v_mode_emp.get() and self.empirical_returns is not None)
        except Exception as e:
            messagebox.showerror("Datos inválidos", f"Revise los campos de entrada.\n{e}")
            return

        months = years * 12
        dt = 1.0/12.0
        mu_net = mu - fee
        
        # Generación del vector de aportaciones
        aport_meses = np.full(months, aport_m, dtype=float)
        if crec_pct != 0.0:
            crec = crec_pct/100.0
            for a in range(1, years):
                aport_meses[a*12:(a+1)*12] = aport_m * ((1.0 + crec) ** a)

        # Inicialización de matriz de caminos (Simulaciones x Meses)
        paths = np.empty((n_sims, months+1), dtype=float)
        paths[:,0] = cap0

        if use_emp:
            # Simulación Empírica (Bootstrap/Muestreo)
            rend_hist = self.empirical_returns.copy()
            if rend_hist.size < 24:
                rend_hist = np.repeat(rend_hist/12.0, 12) # Ajuste simple si datos son anuales
            
            for m in range(1, months+1):
                r = rng.choice(rend_hist, size=n_sims, replace=True)
                paths[:, m] = paths[:, m-1] * (1.0 + r) + aport_meses[m-1]
        else:
            # Simulación Monte Carlo (Movimiento Browniano Geométrico)
            shocks = rng.normal(loc=0.0, scale=np.sqrt(dt), size=(n_sims, months))
            for m in range(1, months+1):
                prev = paths[:, m-1]
                # Fórmula GBM discreta
                ret  = np.exp((mu_net - 0.5*sigma*sigma)*dt + sigma*shocks[:, m-1])
                paths[:, m] = prev*ret + aport_meses[m-1]

        # Reducción a datos anuales para visualización
        annual_idx = np.arange(0, months+1, 12)
        annual_paths = paths[:, annual_idx]

        # Cálculo de lo aportado acumulado
        aport_acum = cap0 + np.concatenate(([0], np.cumsum(np.add.reduceat(aport_meses, np.arange(0, months, 12)))))
        
        # Ajuste por inflación (Rendimiento Real)
        if use_real:
            defl = (1.0 + infl) ** np.arange(0, years+1)
            annual_paths = annual_paths / defl
            aport_acum = aport_acum / defl

        # Cálculo Fiscal (IRPF)
        if use_tax:
            finales = annual_paths[:, -1]
            aport_final = aport_acum[-1]
            plus = finales - aport_final
            impuestos = np.array([aplicar_tramos_irpf(float(p)) for p in plus])
            annual_paths[:, -1] = finales - impuestos

        # Cálculo de Estadísticos
        med = np.median(annual_paths, axis=0)
        p10 = np.percentile(annual_paths, 10, axis=0)
        p90 = np.percentile(annual_paths, 90, axis=0)

        # Probabilidad de éxito
        objetivo_arr = objetivo * np.ones_like(med)
        probs = np.mean(annual_paths >= objetivo_arr, axis=0)

        # Renderizado de Gráfica
        self.ax.clear()
        self.ax.grid(True, linestyle="--", linewidth=0.6)
        self.ax.set_xlabel("Tiempo (años)")
        self.ax.set_ylabel(f"Capital ({'euros reales' if use_real else 'euros nominales'})")
        
        xs = np.arange(0, years+1)
        self.ax.plot(xs, med, label="Mediana", marker="o", color="#2c3e50")
        self.ax.fill_between(xs, p10, p90, alpha=0.25, label="Rango P10–P90", color="#3498db")
        self.ax.plot(xs, aport_acum, linestyle="--", label="Capital Invertido", color="#e74c3c")
        
        self.ax.legend(loc="upper left")
        self.canvas.draw_idle()

        # Actualización Resumen Texto
        final_med = med[-1]
        prob_final = probs[-1] * 100.0
        self.lbl_resumen.config(
            text=(
                f"μ: {parse_percent(self.v_mu_txt.get()):.2f}%  |  σ: {parse_percent(self.v_sigma_txt.get()):.2f}%  "
                f"| Inflación: {infl*100:.2f}%  | TER: {fee*100:.2f}%\n"
                f"Aportación inicial: {parse_money(self.v_aport_m.get()):,.2f} €  "
                f"(Indexación: {crec_pct:.2f}%)  | Años: {years}  | Sims: {n_sims}\n"
                f"Mediana final: {fmt_eur(final_med)}  |  Probabilidad Objetivo: {prob_final:.1f}%"
            )
        )

        # Actualización Tabla
        for r in self.tree.get_children():
            self.tree.delete(r)
        for a in range(0, years+1):
            self.tree.insert(
                "", "end",
                values=(
                    a,
                    fmt_eur(aport_acum[a]),
                    fmt_eur(med[a]),
                    fmt_eur(p10[a]),
                    fmt_eur(p90[a]),
                    f"{probs[a]*100:,.1f}%",
                )
            )

        # Almacenamiento de datos para exportación
        self._last_results = {
            "years": years,
            "xs": xs,
            "aport_acum": aport_acum,
            "med": med, "p10": p10, "p90": p90, "probs": probs,
            "use_real": use_real
        }

    # ------------- Exportación -------------
    def _export_csv(self):
        if not hasattr(self, "_last_results"): return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Exportar datos"
        )
        if not path: return
        r = self._last_results
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["anio","capital_invertido","mediana","p10","p90","probabilidad_objetivo"])
                for i in range(r["years"]+1):
                    w.writerow([int(r["xs"][i]), f"{r['aport_acum'][i]:.2f}",
                                f"{r['med'][i]:.2f}", f"{r['p10'][i]:.2f}",
                                f"{r['p90'][i]:.2f}", f"{r['probs'][i]*100:.2f}"])
            messagebox.showinfo("Exportación completada", f"Datos guardados en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_png(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            title="Guardar gráfico"
        )
        if not path: return
        try:
            self.canvas.figure.savefig(path, dpi=150, bbox_inches="tight")
            messagebox.showinfo("Guardado", f"Imagen guardada en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    App().mainloop()