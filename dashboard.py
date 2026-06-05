import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from shiny import App, render, ui, reactive

# --- Configuração do Visual ---
sns.set_style("whitegrid")
plt.rcParams.update({'font.family': 'sans-serif'})

custom_css = """
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap" rel="stylesheet">
<style>
body { background-color: #f4f7f6; color: #333; font-family: 'Nunito', sans-serif; }

.header { 
    background: #ffffff; padding: 25px; border-bottom: 4px solid #4fa3c4; 
    margin-bottom: 25px; text-align: center; color: #2c3e50;
}

/* Cards com efeito de hover */
.card { 
    background-color: #ffffff; border: none; border-radius: 16px; 
    padding: 25px; margin-bottom: 25px; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }

.card-title { font-size: 18px; font-weight: 800; color: #2c3e50; margin-bottom: 20px; }

.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 20px; }
.metric-card { 
    background-color: #f8f9fa; border-left: 4px solid #4fa3c4; 
    border-radius: 8px; padding: 15px; text-align: center;
}
.metric-title { font-size: 11px; color: #7f8c8d; text-transform: uppercase; font-weight: 700; }
.metric-value { font-size: 24px; color: #2c3e50; font-weight: 800; margin-top: 5px; }
</style>
"""

app_ui = ui.page_fluid(
    ui.HTML(custom_css),
    ui.div(ui.h2(" Video Games Analytics"), class_="header"),
    
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4(" Filtros", style="font-weight: 800;"),
            ui.input_select("platform_select", "Plataforma:", choices={"all": "Todos"}),
            ui.input_select("genre_select", "Gênero:", choices={"all": "Todos"}),
            ui.input_select("publisher_select", "Publicadora:", choices={"all": "Todos"}),
            ui.hr(),
            ui.input_select("stat_factor", "Fator p/ Gráfico:", choices={"mean": "Média", "median": "Mediana", "std": "Desvio-Padrão", "count": "Amostra", "min": "Mínimo", "max": "Máximo"}),
            ui.input_select("sales_metric", "Cartões de Detalhe:", choices={"Global_Sales": "Vendas Globais", "NA_Sales": "NA", "EU_Sales": "EU", "JP_Sales": "JP", "Other_Sales": "Outros"}),
        ),
        
        ui.navset_tab(
            ui.nav_panel(
                " Analise Geral", 
                ui.div(
                    ui.div(" Métricas Estatísticas", class_="card-title"),
                    ui.output_ui("metrics_cards"),
                    class_="card"
                ),
                ui.div(
                    ui.div("Visualização Comparativa", class_="card-title"),
                    ui.output_plot("dynamic_stat_bar"),
                    class_="card"
                ),
                ui.div(
                    ui.div(" Distribuição (Boxplot)", class_="card-title"),
                    ui.output_plot("unified_sales_box"),
                    class_="card"
                )
            )
        )
    )
)

def server(input, output, session):
    @reactive.Calc
    def load_data():
        try: 
            df = pd.read_csv(Path("/home/kaori/Breaking-data/data/vgsales.csv"))
            for col in ['Platform', 'Genre', 'Publisher']: df[col] = df[col].astype('category')
            return df
        except Exception: return None

    @reactive.Effect
    def _update_filters():
        data = load_data()
        if data is not None:
            ui.update_select("platform_select", choices={"all": "Todos"} | {p: p for p in sorted(data['Platform'].dropna().unique())})
            ui.update_select("genre_select", choices={"all": "Todos"} | {g: g for g in sorted(data['Genre'].dropna().unique())})
            ui.update_select("publisher_select", choices={"all": "Todos"} | {p: p for p in sorted(data['Publisher'].dropna().unique())})

    @reactive.Calc
    def get_filtered_data():
        data = load_data()
        if data is None: return None
        p, g, pub = input.platform_select(), input.genre_select(), input.publisher_select()
        if p != "all": data = data[data['Platform'] == p]
        if g != "all": data = data[data['Genre'] == g]
        if pub != "all": data = data[data['Publisher'] == pub]
        return data

    @output
    @render.ui
    def metrics_cards():
        df = get_filtered_data()
        if df is None or df.empty: return None
        dados = df[input.sales_metric()].dropna()
        metrics = {"Amostra": len(dados), "Média": f"{dados.mean():.2f}", "Mediana": f"{dados.median():.2f}", "Desvio-P": f"{dados.std():.2f}", "Mín": dados.min(), "Máx": dados.max()}
        cards = [ui.div(ui.div(k, class_="metric-title"), ui.div(v, class_="metric-value"), class_="metric-card") for k, v in metrics.items()]
        return ui.div(*cards, class_="metric-grid")

    @output
    @render.plot
    def dynamic_stat_bar():
        df = get_filtered_data()
        if df is None or df.empty: return None
        fator = input.stat_factor()
        label_map = {"mean": "Média", "median": "Mediana", "std": "Desvio-Padrão", "count": "Amostra", "min": "Mínimo", "max": "Máximo"}
        agg_map = {"mean": "mean", "median": "median", "std": "std", "count": "count", "min": "min", "max": "max"}
        
        data_stats = df[['NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales']].agg(agg_map[fator])
        
        fig, ax = plt.subplots(figsize=(8, 3), facecolor='none')
        data_stats.plot(kind='bar', ax=ax, color='#4fa3c4', edgecolor='none', width=0.6) 
        
        # Limpeza visual do gráfico
        ax.set_facecolor('none')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ecf0f1')
        ax.spines['bottom'].set_color('#ecf0f1')
        ax.tick_params(axis='x', rotation=0, colors='#7f8c8d')
        ax.tick_params(axis='y', colors='#7f8c8d')
        return fig

    @output
    @render.plot
    def unified_sales_box():
        df = get_filtered_data()
        if df is None or df.empty: return None
        df_melt = df.melt(value_vars=['NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales'], var_name='Região', value_name='Vendas')
        fig, ax = plt.subplots(figsize=(8, 3), facecolor='none')
        sns.boxplot(data=df_melt, x='Região', y='Vendas', ax=ax, color='#a2d2ff', flierprops=dict(markerfacecolor='#4fa3c4', markeredgecolor='none'))
        
        # Limpeza visual
        ax.set_facecolor('none')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ecf0f1')
        ax.spines['bottom'].set_color('#ecf0f1')
        return fig

app = App(app_ui, server)