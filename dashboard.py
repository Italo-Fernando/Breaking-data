import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import norm, linregress
from shiny import App, render, ui, reactive

# --- Configuração do Visual ---
sns.set_style("whitegrid")
plt.rcParams.update({'font.family': 'sans-serif'})

# --- Teste de hipótese: rótulos das opções (reutilizados na UI e nos textos) ---
TEST_TYPES = {
    "two_sided": "Bilateral",
    "greater": "Unilateral à direita",
    "less": "Unilateral à esquerda",
}

# Variáveis quantitativas testáveis (Year + colunas de vendas).
TEST_VARS = {
    "Year": "Ano de lançamento",
    "Global_Sales": "Vendas Globais",
    "NA_Sales": "Vendas na América do Norte",
    "EU_Sales": "Vendas na Europa",
    "JP_Sales": "Vendas no Japão",
    "Other_Sales": "Vendas em outros Países",
}


def z_test_mean_known_variance(sample, mu0, pop_variance, test_type, alpha):
    """Teste Z para a média populacional com variância conhecida.

    Retorna um dict com a estatística do teste, o valor crítico, o p-valor
    e a decisão. `sample` é uma Series/array já sem NaN.
    """
    n = len(sample)
    if n == 0 or pop_variance <= 0:
        return None

    xbar = float(np.mean(sample))
    sigma = np.sqrt(pop_variance)
    z = (xbar - mu0) / (sigma / np.sqrt(n))

    if test_type == "greater":          # H1: mu > mu0
        critical = norm.ppf(1 - alpha)
        reject = z > critical
        p_value = 1 - norm.cdf(z)
    elif test_type == "less":            # H1: mu < mu0
        critical = norm.ppf(alpha)
        reject = z < critical
        p_value = norm.cdf(z)
    else:                                # bilateral, H1: mu != mu0
        critical = norm.ppf(1 - alpha / 2)
        reject = abs(z) > critical
        p_value = 2 * (1 - norm.cdf(abs(z)))

    return {
        "n": n, "xbar": xbar, "sigma": sigma, "z": z,
        "critical": critical, "p_value": p_value, "reject": reject,
    }

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
    ui.div(ui.h2(" Análise do dataset"), class_="header"),
    
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4(" Filtros", style="font-weight: 800;"),
            ui.input_select("platform_select", "Plataforma:", choices={"all": "Todos"}),
            ui.input_select("genre_select", "Gênero:", choices={"all": "Todos"}),
            ui.input_select("publisher_select", "Publicadora:", choices={"all": "Todos"}),
            ui.hr(),
            ui.input_select("stat_factor", "Fator p/ Gráfico:", choices={"mean": "Média", "median": "Mediana", "std": "Desvio-Padrão", "count": "Amostra", "min": "Mínimo", "max": "Máximo"}),
            ui.input_select("sales_metric", "Cartões de Detalhe:", choices={"Global_Sales": "Vendas Globais", "NA_Sales": "Vendas na América do Norte", "EU_Sales": "Vendas na Europa", "JP_Sales": "Vendas no Japão", "Other_Sales": "Vendas em outros Países"}),
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
            ),
            ui.nav_panel(
                "Regressão Linear",
                ui.div(
                    ui.div("Configuração da Regressão", class_="card-title"),
                    ui.row(
                        ui.column(6, ui.input_select("reg_x", "Variável explicativa (x):", choices=TEST_VARS)),
                        ui.column(6, ui.input_select("reg_y", "Variável resposta (y):", choices={k: v for k, v in TEST_VARS.items() if k != "Year"}, selected="Global_Sales")),
                    ),
                    class_="card"
                ),
                ui.div(
                    ui.div("Resultados", class_="card-title"),
                    ui.output_ui("regression_results"),
                    class_="card"
                ),
                ui.div(
                    ui.div("Gráfico de Dispersão com Linha de Regressão", class_="card-title"),
                    ui.output_plot("regression_plot"),
                    class_="card"
                )
            ),
            ui.nav_panel(
                "Teste de hipótese",
                ui.div(
                    ui.div("Teste para a média (variância conhecida)", class_="card-title"),
                    ui.p("Variável e filtros aplicados; a variância inicia na variância amostral (ajustável).",
                         style="color:#7f8c8d; font-size:13px;"),
                    ui.row(
                        ui.column(6, ui.input_select("test_var", "Variável quantitativa:", choices=TEST_VARS)),
                        ui.column(6, ui.input_radio_buttons("test_type", "Tipo de teste:", choices=TEST_TYPES)),
                    ),
                    ui.input_numeric("var_pop", "Variância populacional (σ²):", value=1, min=0.0001),
                    ui.input_slider("mu0", "Valor de μ₀:", min=0, max=10, value=5),
                    ui.input_slider("alpha", "Nível de significância (α):", min=0.01, max=0.20, value=0.05, step=0.01),
                    class_="card"
                ),
                ui.div(
                    ui.div("Resultado do teste", class_="card-title"),
                    ui.output_ui("hypothesis_result"),
                    class_="card"
                ),
                ui.div(
                    ui.div("Distribuição sob H₀ e estatística do teste", class_="card-title"),
                    ui.output_plot("hypothesis_plot"),
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
            csv_path = Path(__file__).resolve().parent / "data" / "vgsales.csv"
            df = pd.read_csv(csv_path)
            for col in ['Platform', 'Genre', 'Publisher']: df[col] = df[col].astype('category')
            return df
        except Exception:
            return None

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

    @reactive.Calc
    def regression_data():
        # Ajuste de mínimos quadrados entre as duas variáveis selecionadas, sobre os dados filtrados.
        df = get_filtered_data()
        if df is None or df.empty: return None
        x_col, y_col = input.reg_x(), input.reg_y()
        if x_col == y_col: return None
        sub = df[[x_col, y_col]].dropna()
        if len(sub) < 2: return None
        x, y = sub[x_col].values, sub[y_col].values
        slope, intercept, r, _, _ = linregress(x, y)
        return {"x": x, "y": y, "slope": slope, "intercept": intercept, "r": r,
                "x_col": x_col, "y_col": y_col}

    @output
    @render.ui
    def regression_results():
        res = regression_data()
        if res is None:
            return ui.p("Selecione duas variáveis diferentes.", style="color:#7f8c8d;")
        slope, intercept, r = res["slope"], res["intercept"], res["r"]
        r2 = r ** 2
        sinal = "+" if intercept >= 0 else "-"
        equacao = f"ŷ = {slope:.4f}x {sinal} {abs(intercept):.4f}"
        linhas = {
            "Coeficiente de correlação (R)": f"{r:.4f}",
            "Coeficiente de determinação (R²)": f"{r2:.4f}",
            "Equação da reta": equacao,
        }
        itens = [ui.tags.li(ui.tags.b(f"{k}: "), v) for k, v in linhas.items()]
        return ui.tags.ul(*itens, style="list-style:none; padding-left:0; font-size:15px;")

    @output
    @render.plot
    def regression_plot():
        res = regression_data()
        if res is None: return None
        x, y = res["x"], res["y"]
        slope, intercept = res["slope"], res["intercept"]
        x_line = np.array([x.min(), x.max()])
        y_line = slope * x_line + intercept

        fig, ax = plt.subplots(figsize=(8, 4), facecolor='none')
        ax.scatter(x, y, color='#4fa3c4', alpha=0.5, edgecolors='none', s=20)
        ax.plot(x_line, y_line, color='#e74c3c', linewidth=2,
                label=f"ŷ = {slope:.4f}x {'+ ' if intercept >= 0 else '- '}{abs(intercept):.4f}")
        ax.set_xlabel(TEST_VARS[res["x_col"]], color='#7f8c8d')
        ax.set_ylabel(TEST_VARS[res["y_col"]], color='#7f8c8d')
        ax.set_facecolor('none')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ecf0f1')
        ax.spines['bottom'].set_color('#ecf0f1')
        ax.tick_params(colors='#7f8c8d')
        ax.legend(fontsize=9, frameon=False)
        return fig

    @reactive.Calc
    def get_test_sample():
        # Série da variável quantitativa selecionada para o teste, filtrada e sem NaN.
        df = get_filtered_data()
        if df is None or df.empty: return None
        return df[input.test_var()].dropna()

    @reactive.Effect
    def _update_mu0_slider():
        # Ajusta a faixa do slider de μ₀ ao intervalo real da variável.
        sample = get_test_sample()
        if sample is None or len(sample) == 0: return
        lo, hi = float(sample.min()), float(sample.max())
        if lo == hi: hi = lo + 1  # evita slider degenerado
        raw = (hi - lo) / 100 or 0.01
        # Passo inteiro em variáveis de grande amplitude (ex.: vendas), decimal nas pequenas.
        step = max(1, round(raw)) if raw >= 1 else round(raw, 4)
        ui.update_slider("mu0", min=round(lo, 4), max=round(hi, 4),
                         value=round(float(sample.mean()), 4), step=step)

    @reactive.Effect
    def _update_var_pop():
        # Inicia a variância populacional na variância amostral (ordem de grandeza realista).
        sample = get_test_sample()
        if sample is None or len(sample) < 2: return
        ui.update_numeric("var_pop", value=round(float(sample.var()), 4))

    @reactive.Calc
    def test_result():
        # Resultado do teste Z, compartilhado entre o texto e o gráfico.
        sample = get_test_sample()
        if sample is None: return None
        return z_test_mean_known_variance(
            sample, input.mu0(), input.var_pop(), input.test_type(), input.alpha()
        )

    @output
    @render.ui
    def hypothesis_result():
        if get_test_sample() is None: return ui.p("Sem dados para o filtro selecionado.")
        res = test_result()
        if res is None:
            return ui.p("Informe uma variância populacional positiva.", style="color:#c0392b;")

        decisao = "Rejeita-se H₀" if res["reject"] else "Não se rejeita H₀"
        cor = "#c0392b" if res["reject"] else "#27ae60"
        linhas = {
            "Hipótese H₀": f"μ = {input.mu0()}",
            "Tipo de teste": TEST_TYPES[input.test_type()],
            "Tamanho da amostra (n)": res["n"],
            "Média amostral (x̄)": f"{res['xbar']:.4f}",
            "Desvio-padrão (σ)": f"{res['sigma']:.4f}",
            "Estatística do teste (Z)": f"{res['z']:.4f}",
            "Valor crítico": f"{res['critical']:.4f}",
            "p-valor": f"{res['p_value']:.4f}",
        }
        itens = [ui.tags.li(ui.tags.b(f"{k}: "), str(v)) for k, v in linhas.items()]
        return ui.div(
            ui.tags.ul(*itens, style="list-style:none; padding-left:0;"),
            ui.div(decisao, style=f"font-size:20px; font-weight:800; color:{cor}; margin-top:10px;"),
        )

    @output
    @render.plot
    def hypothesis_plot():
        res = test_result()
        if res is None: return None
        z, crit, tipo = res["z"], res["critical"], input.test_type()

        # Eixo amplo o bastante para conter o Z e a região de rejeição.
        lim = max(4.0, abs(z) + 1)
        x = np.linspace(-lim, lim, 500)
        y = norm.pdf(x)

        fig, ax = plt.subplots(figsize=(8, 3.2), facecolor='none')
        ax.plot(x, y, color='#2c3e50')

        # Sombreia a(s) região(ões) de rejeição conforme o tipo de teste.
        if tipo == "greater":
            ax.fill_between(x, y, where=(x >= crit), color='#e74c3c', alpha=0.3)
            ax.axvline(crit, color='#e74c3c', ls='--', label=f'Crítico = {crit:.2f}')
        elif tipo == "less":
            ax.fill_between(x, y, where=(x <= crit), color='#e74c3c', alpha=0.3)
            ax.axvline(crit, color='#e74c3c', ls='--', label=f'Crítico = {crit:.2f}')
        else:
            ax.fill_between(x, y, where=(x >= crit), color='#e74c3c', alpha=0.3)
            ax.fill_between(x, y, where=(x <= -crit), color='#e74c3c', alpha=0.3)
            ax.axvline(crit, color='#e74c3c', ls='--', label=f'Crítico = ±{crit:.2f}')
            ax.axvline(-crit, color='#e74c3c', ls='--')

        # Z calculado e a posição de H0 (Z = 0).
        ax.axvline(0, color='#bdc3c7', ls=':')
        ax.axvline(z, color='#2980b9', lw=2, label=f'Z calc = {z:.2f}')

        ax.set_yticks([])
        ax.set_xlabel('Z')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.legend(loc='upper right', fontsize=9, frameon=False)
        return fig

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