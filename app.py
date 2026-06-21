import sys
import subprocess
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from shiny import App, render, ui, reactive

# Configuração visual
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

# --- Lançamento do dashboard.py como app separado ---
DASHBOARD_PORT = 8001
DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"
_dashboard_proc = None

def ensure_dashboard_running():
    """Sobe o dashboard.py num processo próprio (uma vez só)."""
    global _dashboard_proc
    if _dashboard_proc is None or _dashboard_proc.poll() is not None:
        _dashboard_proc = subprocess.Popen(
            [sys.executable, "-m", "shiny", "run", "dashboard.py", "--port", str(DASHBOARD_PORT)],
            cwd=str(Path(__file__).resolve().parent),
        )

app_ui = ui.page_fluid(
    ui.h2("Dashboard Exploratório de Dados"),

    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("1. Configurações"),
            ui.input_file("file_select", "Selecione o arquivo CSV:", accept=[".csv"], multiple=False, width="100%"),
            ui.input_selectize("variable_select", "Selecione a variável numérica:", choices=[], width="100%"),
            ui.hr(),
            ui.h4("2. Estatísticas"),
            ui.output_text_verbatim("stats_output"),
            # Botão para a "Análise Geral" — só aparece após escolher o arquivo.
            ui.output_ui("general_button"),
            width=350
        ),

        ui.navset_tab(
            ui.nav_panel(
                "Análise descritiva de uma variável",
                ui.div(
                    ui.br(),
                    ui.row(
                        ui.column(6, ui.card(ui.h4("Histograma"), ui.output_plot("histogram"))),
                        ui.column(6, ui.card(ui.h4("Boxplot"), ui.output_plot("boxplot")))
                    ),
                    ui.br(),
                    ui.row(
                        ui.column(12, ui.card(ui.h4("Amostra do Dataset"), ui.output_table("data_table")))
                    ),
                    style="padding: 10px;"
                )
            )
        )
    )
)

def server(input, output, session):
    @reactive.Calc
    def load_data():
        file_info = input.file_select()
        if not file_info: return None
        try: return pd.read_csv(file_info[0]["datapath"])
        except Exception: return None

    # Colunas numéricas que são identificadores, não variáveis de análise.
    ID_COLS = {"Rank", "id", "ID", "index"}

    @reactive.Effect
    def update_variables():
        data = load_data()
        if data is not None:
            numeric_cols = [c for c in data.select_dtypes(include=[np.number]).columns
                            if c not in ID_COLS]
            ui.update_selectize("variable_select", choices=numeric_cols)

    # ---------- Botão da "Análise Geral" (gating + lançamento) ----------
    @output
    @render.ui
    def general_button():
        if load_data() is None:
            return None
        return ui.div(
            ui.hr(),
            ui.input_action_button("open_dashboard", "Abrir Análise Geral", class_="btn-primary", width="100%"),
            ui.output_ui("dashboard_link"),
        )

    @reactive.Effect
    @reactive.event(input.open_dashboard)
    def _launch_dashboard():
        ensure_dashboard_running()

    @output
    @render.ui
    def dashboard_link():
        if not input.open_dashboard():
            return None
        # Abre numa nova aba e deixa o link como fallback (popup pode ser bloqueado).
        return ui.div(
            ui.tags.script(f"window.open('{DASHBOARD_URL}', '_blank');"),
            ui.p("Aguarde alguns segundos e, se a aba não abrir, clique abaixo:", style="margin-top:10px;"),
            ui.a("Abrir Análise Geral em nova aba", href=DASHBOARD_URL, target="_blank"),
        )

    # ---------- Aba descritiva ----------
    @reactive.Calc
    def calculate_stats():
        data = load_data()
        var = input.variable_select()
        if data is None or not var: return None

        col = data[var].dropna()
        if len(col) == 0: return None
        return {
            'N': len(col), 'Média': col.mean(), 'Mediana': col.median(),
            'Desvio-padrão': col.std(), 'Mínimo': col.min(), 'Máximo': col.max()
        }

    @output
    @render.text
    def stats_output():
        stats = calculate_stats()
        if stats is None: return "Aguardando seleção..."

        def fmt(v):
            # Inteiro quando o valor não tem parte fracionária (ex.: Year),
            # decimal nos demais casos (ex.: vendas).
            return str(int(v)) if float(v).is_integer() else f"{v:.4f}"

        return "".join(f"{k}: {fmt(v)}\n" for k, v in stats.items())

    @output
    @render.plot
    def histogram():
        data = load_data()
        var = input.variable_select()
        if data is None or not var: return None
        fig, ax = plt.subplots()
        ax.hist(data[var].dropna(), bins=30, color='#4fa3c4', edgecolor='black')
        ax.set_title(f'Histograma de {var}')
        return fig

    @output
    @render.plot
    def boxplot():
        data = load_data()
        var = input.variable_select()
        if data is None or not var: return None
        fig, ax = plt.subplots()
        ax.boxplot(data[var].dropna(), vert=True, patch_artist=True, boxprops=dict(facecolor='#4fa3c4'))
        ax.set_title(f'Boxplot de {var}')
        return fig

    @output
    @render.table
    def data_table():
        data = load_data()
        if data is None: return pd.DataFrame()
        return data.head(15)

app = App(app_ui, server)
