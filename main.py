import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import plotly.graph_objects as go

st.set_page_config(layout="wide")


# Título do Dashboard
st.markdown(
    """
    <div style="text-align: center; padding: 20px;">
        <h1 style="color: #2E86C1; font-weight: bold; font-size: 40px; margin: 0;">
            DASHBOARD | VENDAS
        </h1>
        <p style="font-size: 22px; color: #2E86C1;">Análise detalhada de vendas e performance</p>
    </div>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def load_transform_data():
    # Leitura dos arquivos CSV
    df_vendas = pd.read_csv("Vendas.csv", sep=';')
    df_produtos = pd.read_csv("CadastroProdutos.csv", sep=';')
    df_lojas = pd.read_csv("Lojas.csv", sep=';')
    df_promocoes = pd.read_csv("Promocoes.csv", sep=';')

    # Realizando os merges de forma clara
    df_vendas = df_vendas.merge(df_produtos, on='ID Produto', how='left') \
                        .merge(df_lojas, on='ID Loja', how='left') \
                        .merge(df_promocoes, on='ID Promocao', how='left')

    # Limpeza de colunas e transformação de dados
    df_vendas = df_vendas.drop(columns=['ID Produto'])
    df_vendas["Preco Unitario"] = df_vendas["Preco Unitario"].str.replace(",", ".").astype(float)
    df_vendas["Custo Unitario"] = df_vendas["Custo Unitario"].str.replace(",", ".").astype(float)

    # Cálculo do Total e Lucro das Vendas
    df_vendas["Total da Venda"] = (df_vendas["Preco Unitario"] * df_vendas["Quantidade Vendida"].astype(int)) - \
                                  (df_vendas["Preco Unitario"] * df_vendas["Quantidade Devolvida"].astype(int))

    df_vendas["Lucro da Venda"] = (df_vendas["Custo Unitario"] * df_vendas["Quantidade Vendida"].astype(int)) - \
                                  (df_vendas["Custo Unitario"] * df_vendas["Quantidade Devolvida"].astype(int))

    # Salvando o DataFrame resultante
    df_vendas.to_csv("dfvendas.csv", sep=';', index=False)

    return df_vendas

def formatar_moeda(valor):
    return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")


def data_transform_show(df_filtered):
    # Calculando os totais
    total_vendas_periodo = formatar_moeda(round(df_filtered["Total da Venda"].sum(), 2))
    total_lucro_periodo = formatar_moeda(round(df_filtered["Lucro da Venda"].sum(), 2))
    ticket_medio = formatar_moeda(round(df_filtered["Total da Venda"].mean(), 2))

    # Template para os Cards
    card_template = """
    <div
    style="
        background-color: #1E1E1E; 
        border-radius: 10px; 
        border: 1px solid white; 
        padding: 20px; 
        text-align: center; 
        width: 100%; 
        max-width: 470px; 
        margin: 20px; 
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h1 style="color: {color}; font-size: 2.8em; margin: 0; padding-bottom: 10px;">R$ {value}</h1>
        <p style="font-size: 1.5em; margin: 0; color: #E0E0E0;">{label}</p>
    </div>
    """

    # Layout dos Cards com maior responsividade
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(card_template.format(color="#FFFFFF", value=total_vendas_periodo, label="Total de Vendas"), unsafe_allow_html=True)
    with col2:
        st.markdown(card_template.format(color="#FFFFFF", value=total_lucro_periodo, label="Total de Lucro"), unsafe_allow_html=True)
    with col3:
        st.markdown(card_template.format(color="#FFFFFF", value=ticket_medio, label="Ticket Médio"), unsafe_allow_html=True)


def charts_revenue(df_filtered):
    # Título do gráfico
    st.subheader("1. Faturamento Mensal")

    # Convertendo "Data da Venda" para datetime e criando coluna 'mes'
    df_filtered["Data da Venda"] = pd.to_datetime(df_filtered["Data da Venda"])
    df_filtered["mes"] = df_filtered["Data da Venda"].dt.to_period("M").astype(str)

    # Agrupando por mês e somando o total de vendas e lucro
    resumo_mensal = df_filtered.groupby("mes")[["Total da Venda", "Lucro da Venda"]].sum().reset_index()

    # Criando o gráfico com colunas para o total de vendas e linha para o lucro
    fig = go.Figure()

    # Adicionando o gráfico de barras (Total de Vendas)
    fig.add_trace(go.Bar(
        x=resumo_mensal["mes"],
        y=resumo_mensal["Total da Venda"],
        name="Total de Vendas",
        marker_color="DodgerBlue",  # Cor mais agradável
        text=resumo_mensal["Total da Venda"].apply(lambda x: f"R$ {x:,.2f}"),  # Formato de texto mais amigável
        texttemplate='%{text}', 
        textposition="outside"
    ))

    # Adicionando o gráfico de linha (Lucro da Venda)
    fig.add_trace(go.Scatter(
        x=resumo_mensal["mes"],
        y=resumo_mensal["Lucro da Venda"],
        name="Lucro Total",
        mode="lines+markers",
        line=dict(color="green", width=2),
        marker=dict(size=8, color='green')
    ))

    # Ajustando o layout do gráfico para visualização mais clara
    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title="Valor (R$)",
        barmode="group",
        template="plotly_white",
        legend_title="Indicadores",
        xaxis=dict(tickangle=-45),
        margin=dict(l=40, r=40, t=60, b=40),
        height=400
    )

    # Exibindo o gráfico de forma responsiva no Streamlit
    st.plotly_chart(fig, use_container_width=True)

def charts_type_sales(df_filtered):
    # Dividindo a tela em duas colunas para os gráficos
    col3, col4 = st.columns(2)
    
    # Gráfico de Faturamento por Tipo de Produto (donut)
    with col3:
        st.subheader("3. Faturamento Por Categoria de Produto")

        # Agrupando por 'Tipo' e somando o 'Total da Venda'
        total_venda_por_tipo = df_filtered.groupby('Tipo')['Total da Venda'].sum().reset_index()

        # Criando o gráfico de rosca (donut) com Altair
        chart = alt.Chart(total_venda_por_tipo).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Total da Venda", type="quantitative"),
            color=alt.Color(field="Tipo", type="nominal"),
            tooltip=["Tipo", "Total da Venda"]
        )
        st.altair_chart(chart, use_container_width=True)

    # Gráfico de Faturamento por Produto
    with col4:
        st.subheader("2. Faturamento Por Produto")
        
        # Agrupando por 'Categoria' e somando o 'Total da Venda'
        produtos_mais_vendidos = df_filtered.groupby('Categoria').agg({'Total da Venda': 'sum'}).reset_index()
        produtos_mais_vendidos = produtos_mais_vendidos.sort_values(by="Total da Venda", ascending=False).head(10)

        # Criando o gráfico de barras
        st.bar_chart(produtos_mais_vendidos.set_index("Categoria")["Total da Venda"], 
                    use_container_width=True)

def promotion_infos(df_filtered):
    # Garantir que 'Total da Venda' é numérico
    try:
        df_filtered["Total da Venda"] = (
            df_filtered["Total da Venda"]
            .astype(str)  # Converter para string, caso tenha valores não numéricos
            .str.replace(',', '')  # Remover vírgulas
            .astype(float)  # Converter para float
        )
    except Exception as e:
        st.error(f"Erro na conversão dos valores de vendas: {e}")
        return

    # Agrupar por "Nome Promocao" e somar o "Total da Venda"
    df_total_promocoes = df_filtered.groupby("Nome Promocao")["Total da Venda"].sum().reset_index()

    # Renomear as colunas para clareza
    df_total_promocoes.columns = ["Promoção", "Total de Vendas"]

    # Gerar o gráfico de barras
    fig = px.bar(
        df_total_promocoes, 
        x="Promoção", 
        y="Total de Vendas",
        text="Total de Vendas",  # Mostrar os valores diretamente nas barras
        labels={"Promoção": "Promoção", "Total de Vendas": "Total de Vendas (R$)"},  # Renomear eixos
        color="Promoção",  # Colorir barras por promoção (opcional)
    )

    # Customizar o layout do gráfico
    fig.update_traces(
        texttemplate='%{text:.2f}',  # Formato do texto: 2 casas decimais
        textposition='outside'      # Posição do texto: fora das barras
    )
    fig.update_layout(
        xaxis=dict(title="Promoção"),  # Nome do eixo x
        yaxis=dict(title="Total de Vendas (R$)"),  # Nome do eixo y
        showlegend=False  # Remover a legenda, pois as cores são autoexplicativas
    )

    # Configuração do aplicativo Streamlit
    st.markdown("### 4. Faturamento por Promoção")

    # Exportar o DataFrame para CSV e gerar link para download
    csv_file = df_total_promocoes.to_csv(index=False, sep=';')
    st.download_button(
        label="Baixar Dados de Promoções",
        data=csv_file,
        file_name="promocoes.csv",
        mime="text/csv"
    )


    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)


def full_data(df_filtered):
    if st.checkbox('Mostrar Dados Brutos'):
        st.subheader('Dados Brutos')
        st.write(df_filtered)


def filter_sidebar(df_vendas):
    # Configuração e imagem do cabeçalho
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding: 10px;">
            <img src="https://cdn-icons-png.flaticon.com/512/5785/5785374.png" style="width: 60%; border-radius: 10px;">
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Título e introdução aos filtros
    st.sidebar.markdown(
        """
        <hr style="border: 1px solid #ccc;">
        <h1 style="text-align: center; color: #2E86C1;">Filtros</h1>
        <p style="text-align: center; font-size: 14px; color: #2E86C1;">
            Ajuste os filtros abaixo para refinar os dados exibidos.
        </p>
        """,
        unsafe_allow_html=True
    )

    # Conversão de datas para DateTime e obtenção de intervalo
    df_vendas["Data da Venda"] = pd.to_datetime(df_vendas["Data da Venda"], format="%d/%m/%Y")
    data_min, data_max = df_vendas["Data da Venda"].min(), df_vendas["Data da Venda"].max()

    # Widgets de filtro de data
    st.sidebar.subheader("Período de Vendas")
    data_inicial = st.sidebar.date_input("Data Inicial", value=data_min, min_value=data_min, max_value=data_max, key="data_inicial")
    data_final = st.sidebar.date_input("Data Final", value=data_max, min_value=data_min, max_value=data_max, key="data_final")

    # Filtros de Loja, Promoção e Produtos
    st.sidebar.subheader("Loja")
    options_loja = st.sidebar.multiselect(
        "Selecione uma ou mais lojas:",
        options=sorted(df_vendas['Nome da Loja'].unique()),
        placeholder="Escolha as lojas"
    )

    st.sidebar.subheader("Promoção")
    options_promocao = st.sidebar.multiselect(
        "Selecione uma ou mais promoções:",
        options=sorted(df_vendas['Nome Promocao'].unique()),
        placeholder="Escolha as promoções"
    )

    st.sidebar.subheader("Produtos")
    options_produtos = st.sidebar.multiselect(
        "Selecione uma ou mais categorias de produtos:",
        options=sorted(df_vendas['Categoria'].unique()),
        placeholder="Escolha os produtos"
    )

    # Aplicação dos filtros no DataFrame
    df_filtered = df_vendas[
        (df_vendas["Data da Venda"] >= pd.to_datetime(data_inicial)) &
        (df_vendas["Data da Venda"] <= pd.to_datetime(data_final))
    ]

    if options_loja:
        df_filtered = df_filtered[df_filtered["Nome da Loja"].isin(options_loja)]

    if options_promocao:
        df_filtered = df_filtered[df_filtered["Nome Promocao"].isin(options_promocao)]

    if options_produtos:
        df_filtered = df_filtered[df_filtered["Categoria"].isin(options_produtos)]

    # Retorno do DataFrame filtrado
    return df_filtered


if __name__ == "__main__":
    df_vendas = load_transform_data()
    df_filtered = filter_sidebar(df_vendas)
    data_transform_show(df_filtered)
    full_data(df_filtered)
    charts_revenue(df_filtered)
    charts_type_sales(df_filtered)
    promotion_infos(df_filtered)
