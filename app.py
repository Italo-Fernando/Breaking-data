import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from shiny import App, render, ui, reactive

# Configuração visual
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

app_ui = ui.page_fluid(
    ui.h2("Dashboard Exploratório de Dados"),
    
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("1. Configurações"),
            ui.input_selectize("file_select", "Selecione o arquivo CSV:", choices=[], width="100%"),
            ui.input_selectize("variable_select", "Selecione a variável numérica:", choices=[], width="100%"),
            ui.hr(),
            ui.h4("2. Estatísticas"),
            ui.output_text_verbatim("stats_output"),
            width=350
        ),
        
        # PRIMEIRA ALTERAÇÃO: Tudo agrupado em uma única aba inicial
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
            # Futuramente, adicione novas análises aqui: ui.nav_panel("Nova Análise", ...)
        )
    )
)

def server(input, output, session):
    @reactive.Effect
    def update_files():
        data_dir = Path("/home/kaori/Breaking-data/data")
        csv_files = list(data_dir.glob("*.csv"))
        file_choices = {file.name: str(file) for file in csv_files}
        ui.update_selectize("file_select", choices=file_choices)
    
    @reactive.Calc
    def load_data():
        file_path = input.file_select()
        if not file_path: return None
        try: return pd.read_csv(file_path)
        except Exception: return None
    
    @reactive.Effect
    def update_variables():
        data = load_data()
        if data is not None:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            ui.update_selectize("variable_select", choices=numeric_cols)
    
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
        out = ""
        for k, v in stats.items():
            out += f"{k}: {int(v)}\n" if k == 'N' else f"{k}: {v:.4f}\n"
        return out
    
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