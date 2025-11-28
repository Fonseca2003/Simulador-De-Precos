import streamlit as st
import pandas as pd

st.set_page_config(page_title="Formação de Preço", layout="centered", page_icon="🧮")
st.title("🧮 Simulador de Preços")

# =========================
# ESTADO INICIAL
# =========================
if "registros" not in st.session_state:
    st.session_state.registros = []

if "registros_verba" not in st.session_state:
    st.session_state.registros_verba = []

# =========================
# TIPO DE PRODUTO (ST x SEM ST)
# =========================
tipo_produto = st.radio(
    "Selecione o tipo de tributação:",
    ["Sem ST", "Com ST"],
    index=0,
    horizontal=True,
    help=(
        "Sem ST: ICMS de saída entra normalmente no cálculo dos impostos.\n"
        "Com ST: ICMS de saída não é considerado em C11 (Total Imposto de Saída), "
        "sendo usado apenas como parâmetro/base (ICMS ST)."
    ),
)

st.markdown("<hr style='margin-top: 0.2rem; margin-bottom: 0.2rem;'>", unsafe_allow_html=True)

# =========================
# PARÂMETROS GERAIS (COMPARTILHADOS)
# =========================
st.subheader("⚙️ Parâmetros Gerais")

if tipo_produto == "Sem ST":
    label_icms_entrada = "Crédito ICMS %"
    help_icms_entrada = "ICMS de crédito na entrada. Informe em % (ex.: 18 = 18%)."
else:
    label_icms_entrada = "ICMS ST %"
    help_icms_entrada = "ICMS ST (base para cálculo e recuperação). Informe em %."

col_g1, col_g2 = st.columns(2)
with col_g1:
    # ICMS Entrada / ICMS ST
    st.session_state.icms_entrada_pct = st.number_input(
        label_icms_entrada,
        min_value=0.0,
        step=0.05,
        value=st.session_state.get("icms_entrada_pct", 18.0),
        format="%.2f",
        help=help_icms_entrada,
        key="icms_entrada_pct_global",
    )
    # PIS/COFINS Entrada
    st.session_state.pis_cofins_entrada_pct = st.number_input(
        "Crédito PIS/COFINS %",
        min_value=0.0,
        step=0.05,
        value=st.session_state.get("pis_cofins_entrada_pct", 9.25),
        format="%.2f",
        help="Informe em % (ex.: 9,25 = 9,25%).",
        key="pis_cofins_entrada_pct_global",
    )
with col_g2:
    if tipo_produto == "Sem ST":
        st.session_state.icms_saida_pct = st.number_input(
            "Débito ICMS %",
            min_value=0.0,
            step=0.05,
            value=st.session_state.get("icms_saida_pct", 18.0),
            format="%.2f",
            help="Informe em % (ex.: 18 = 18%).",
            key="icms_saida_pct_global",
        )
    st.session_state.pis_cofins_saida_pct = st.number_input(
        "Débito PIS/COFINS %",
        min_value=0.0,
        step=0.05,
        value=st.session_state.get("pis_cofins_saida_pct", 9.25),
        format="%.2f",
        help="Informe em % (ex.: 9,25 = 9,25%).",
        key="pis_cofins_saida_pct_global",
    )


st.markdown("""
<style>
/* Ou, se quiser mover tudo dentro do HorizontalBlock */
div[data-testid="stHorizontalBlock"] {
    margin-top: -20px; /* Ajuste conforme necessário */
}            

/* Ajusta os radios para ficarem próximos do input e deslocados para cima */
div[data-testid="stHorizontalBlock"] div[role="radiogroup"] {
    display: flex;
    gap: 0px; /* reduz espaço entre % e R$ */
    position: relative;
    top: -6px; /* desloca para cima */
}

/* Reduz tamanho da fonte das opções */
div[data-testid="stHorizontalBlock"] div[role="radiogroup"] label {
    font-size: 14px !important;
    line-height: 1;
    white-space: nowrap;
}

/* Ajusta largura do INPUT real para Despesas e IPI */
input[id*="despesas_val_global"],
input[id*="ipi_val_global"] {
    width: 250px !important; /* ajuste conforme necessário */
}
</style>
""", unsafe_allow_html=True)


# Layout
col_g3, col_g4, col_g5, col_g6 = st.columns([4, 1, 4, 1])

with col_g3:
    st.session_state.despesas_val = st.number_input(
        "Despesas",
        min_value=0.0,
        step=0.05,
        value=st.session_state.get("despesas_val", 2.0),
        format="%.2f",
        key="despesas_val_global",
    )

with col_g4:
    tipo_despesas = st.radio(
        "",
        ["%", "R\u00A0$"],  # espaço não separável
        index=0,
        horizontal=True,
        key="tipo_despesas",
    )

with col_g5:
    st.session_state.ipi_val = st.number_input(
        "IPI",
        min_value=0.0,
        step=0.05,
        value=st.session_state.get("ipi_val", 0.0),
        format="%.2f",
        key="ipi_val_global",
    )

with col_g6:
    tipo_ipi = st.radio(
        "",
        ["%", "R\u00A0$"],
        index=0,
        horizontal=True,
        key="tipo_ipi",
    )

# =========================
# FUNÇÃO AUXILIAR
# =========================
def calcular_total_saida(icms_saida_f: float, pis_cofins_saida_f: float, modo_st: str) -> float:
    if modo_st == "Sem ST":
        return icms_saida_f + (pis_cofins_saida_f - (pis_cofins_saida_f * icms_saida_f))
    else:
        return pis_cofins_saida_f

# =========================
# TABS
# =========================
aba1, aba2 = st.tabs(["Valor NF", "Sell In"])

# =========================
# ABA 1 – SIMULADOR NF
# =========================
with aba1:
    ultimo_resultado = None
    with st.form("form_preco"):
        st.subheader("Dados de entrada – Valor NF")
        col3, col4 = st.columns(2)
        with col3:
            preco = st.number_input("Preço De Venda R$", min_value=0.0, step=0.05, format="%.2f", key="preco_aba1")
        with col4:
            margem_pct = st.number_input("Margem %", min_value=0.0, step=0.05, value=0.0, format="%.2f", key="margem_pct_aba1")
        submitted = st.form_submit_button("Calcular e adicionar à lista")

    if submitted:
        icms_entrada_f = st.session_state.icms_entrada_pct / 100.0
        pis_cofins_entrada_f = st.session_state.pis_cofins_entrada_pct / 100.0
        icms_saida_f = st.session_state.icms_saida_pct / 100.0 if tipo_produto == "Sem ST" else 0.0
        pis_cofins_saida_f = st.session_state.pis_cofins_saida_pct / 100.0
        margem_f = margem_pct / 100.0

        # Despesas
        if tipo_despesas == "%":
            despesas_f = st.session_state.despesas_val / 100.0
        else:
            despesas_f = st.session_state.despesas_val / preco if preco > 0 else 0.0

        # IPI
        if tipo_ipi == "%":
            ipi_f = st.session_state.ipi_val / 100.0
        else:
            ipi_f = st.session_state.ipi_val / preco if preco > 0 else 0.0

        # Total saída
        total_saida_f = calcular_total_saida(icms_saida_f, pis_cofins_saida_f, tipo_produto)

        # Custo líquido
        custo_liquido = preco * (1 - (margem_f + total_saida_f)) - ipi_f * preco

        # Valor NF
        if tipo_produto == "Sem ST":
            try:
                custo_nf = custo_liquido / (1 - icms_entrada_f - pis_cofins_entrada_f*(1 - icms_entrada_f) + despesas_f)
            except ZeroDivisionError:
                custo_nf = float("nan")
        else:
            try:
                denom = 1 - (1 - icms_entrada_f)*pis_cofins_entrada_f + despesas_f + icms_entrada_f
                custo_nf = custo_liquido / denom
            except ZeroDivisionError:
                custo_nf = float("nan")

        # PMZ
        try:
            pmz = custo_liquido / (1 - total_saida_f)
        except ZeroDivisionError:
            pmz = float("nan")

        # Armazena registro
        linha = {
            "Tipo": tipo_produto,
            "Valor NF R$": custo_nf,
            "Custo Líquido R$": custo_liquido,
            "PMZ R$": pmz,
            "Total Imposto %": total_saida_f*100,
            "Margem %": margem_pct,
            "Despesas": st.session_state.despesas_val,
            "IPI": st.session_state.ipi_val,
        }
        st.session_state.registros.append(linha)
        ultimo_resultado = linha
        st.success("Cálculos realizados e linha adicionada à lista!")

    if ultimo_resultado:
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Custo NF", f"R$ {ultimo_resultado['Valor NF R$']:.2f}")
            st.metric("Custo Líquido", f"R$ {ultimo_resultado['Custo Líquido R$']:.2f}")
        with col_b:
            st.metric("PMZ", f"R$ {ultimo_resultado['PMZ R$']:.2f}")
            st.metric("Total Imposto de Saída", f"{ultimo_resultado['Total Imposto %']:.2f}%")

    st.subheader("📋 Lista de simulações – Valor NF")
    if st.session_state.registros:
        df = pd.DataFrame(st.session_state.registros)
        df = df.fillna(0.0)
        st.dataframe(df.style.format({
            "Valor NF R$": "{:,.2f}",
            "Custo Líquido R$": "{:,.2f}",
            "PMZ R$": "{:,.2f}",
            "Total Imposto %": "{:,.2f}%",
            "Margem %": "{:,.2f}%",
            "Despesas": "{:,.2f}",
            "IPI": "{:,.2f}",
        }))
    else:
        st.info("Nenhuma simulação cadastrada ainda.")

# =========================
# ABA 2 – SELL IN
# =========================
with aba2:
    st.subheader("Dados de entrada – Sell In")
    with st.form("form_verba"):
        col3, col4 = st.columns(2)
        with col3:
            custo_nf_input = st.number_input("Valor NF (R$)", min_value=0.0, step=0.05, format="%.2f", key="custo_nf_input_aba2")
            preco_v = st.number_input("Preço De Venda R$", min_value=0.0, step=0.05, format="%.2f", key="preco_v_aba2")
        with col4:
            margem_pct_v = st.number_input("Margem %", min_value=0.0, step=0.05, value=0.0, format="%.2f", key="margem_pct_v_aba2")
        submitted_verba = st.form_submit_button("Calcular verba necessária")

    if submitted_verba and preco_v > 0:
        icms_entrada_f_v = st.session_state.icms_entrada_pct / 100.0
        pis_cofins_entrada_f_v = st.session_state.pis_cofins_entrada_pct / 100.0
        icms_saida_f_v = st.session_state.icms_saida_pct / 100.0 if tipo_produto == "Sem ST" else 0.0
        pis_cofins_saida_f_v = st.session_state.pis_cofins_saida_pct / 100.0
        margem_f_v = margem_pct_v / 100.0

        # Despesas
        if tipo_despesas == "%":
            despesas_f_v = st.session_state.despesas_val / 100.0
        else:
            despesas_f_v = st.session_state.despesas_val / preco_v if preco_v > 0 else 0.0

        # IPI
        if tipo_ipi == "%":
            ipi_f_v = st.session_state.ipi_val / 100.0
        else:
            ipi_f_v = st.session_state.ipi_val / preco_v if preco_v > 0 else 0.0

        # Custo líquido atual
        if tipo_produto == "Sem ST":
            D_v = 1 - icms_entrada_f_v - pis_cofins_entrada_f_v*(1 - icms_entrada_f_v) + despesas_f_v
        else:
            D_v = 1 - (1 - icms_entrada_f_v)*pis_cofins_entrada_f_v + despesas_f_v + icms_entrada_f_v

        custo_liquido_atual = custo_nf_input * D_v - ipi_f_v * custo_nf_input

        # Total saída
        total_saida_f_v = calcular_total_saida(icms_saida_f_v, pis_cofins_saida_f_v, tipo_produto)

        # Custo líquido objetivo
        custo_liquido_obj = preco_v * (1 - (margem_f_v + total_saida_f_v)) - ipi_f_v * preco_v

        # Verba necessária
        verba_reais = custo_liquido_atual - custo_liquido_obj
        verba_pct_sobre_nf = (verba_reais / custo_nf_input * 100.0) if custo_nf_input > 0 else float("nan")
        verba_pct_sobre_preco = (verba_reais / preco_v * 100.0) if preco_v > 0 else float("nan")

        linha_verba = {
            "Tipo": tipo_produto,
            "Valor NF R$": custo_nf_input,
            "Preço de Venda R$": preco_v,
            "Margem %": margem_pct_v,
            "Crédito ICMS/ICMS ST %": st.session_state.icms_entrada_pct,
            "Crédito PIS/COFINS %": st.session_state.pis_cofins_entrada_pct,
            "Despesas": st.session_state.despesas_val,
            "IPI": st.session_state.ipi_val,
            "Débito ICMS %": st.session_state.icms_saida_pct if tipo_produto == "Sem ST" else 0.0,
            "Débito PIS/COFINS %": st.session_state.pis_cofins_saida_pct,
            "Custo Líquido Atual R$": custo_liquido_atual,
            "Custo Líquido Objetivo R$": custo_liquido_obj,
            "Total Imposto %": total_saida_f_v*100,
            "Verba R$": verba_reais,
            "Verba % NF": verba_pct_sobre_nf,
            "Verba % Preço de Venda": verba_pct_sobre_preco,
        }

        st.session_state.registros_verba.append(linha_verba)

        colv1, colv2 = st.columns(2)
        with colv1:
            st.metric("Verba necessária (R$)", f"R$ {verba_reais:,.2f}")
            st.metric("Verba sobre NF (%)", f"{verba_pct_sobre_nf:,.2f}%")
            st.metric("Verba sobre preço de venda (%)", f"{verba_pct_sobre_preco:,.2f}%")
        with colv2:
            st.metric("Custo Líquido atual (C7)", f"R$ {custo_liquido_atual:,.2f}")
            st.metric("Custo Líquido objetivo (C7 alvo)", f"R$ {custo_liquido_obj:,.2f}")
            st.metric("Total Imposto de Saída (C11)", f"{total_saida_f_v*100:,.2f}%")

    # --- Tabela Sell In ---
    st.subheader("📋 Lista de simulações de verba - Sell In")
    if st.session_state.registros_verba:
        df_verba = pd.DataFrame(st.session_state.registros_verba)
        df_verba = df_verba.fillna(0.0)
        st.dataframe(df_verba.style.format({
            "Valor NF R$": "{:,.2f}",
            "Preço de Venda R$": "{:,.2f}",
            "Margem %": "{:,.2f}%",
            "Crédito ICMS/ICMS ST %": "{:,.2f}%",
            "Crédito PIS/COFINS %": "{:,.2f}%",
            "Despesas": "{:,.2f}",
            "IPI": "{:,.2f}",
            "Débito ICMS %": "{:,.2f}%",
            "Débito PIS/COFINS %": "{:,.2f}%",
            "Custo Líquido Atual R$": "{:,.2f}",
            "Custo Líquido Objetivo R$": "{:,.2f}",
            "Total Imposto %": "{:,.2f}%",
            "Verba R$": "{:,.2f}",
            "Verba % NF": "{:,.2f}%",
            "Verba % Preço de Venda": "{:,.2f}%",
        }))
    else:
        st.info("Nenhuma simulação de verba cadastrada ainda.")
