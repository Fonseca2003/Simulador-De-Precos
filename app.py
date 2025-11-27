import streamlit as st
import pandas as pd

st.set_page_config(page_title="Formação de Preço", layout="centered")

st.title("📊 Simulador de Preços")

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
st.markdown(
    """
    <hr style="margin-top: 0.2rem; margin-bottom: 0.2rem;">
    """,
    unsafe_allow_html=True,
)

# =========================
# PARÂMETROS GERAIS (COMPARTILHADOS ENTRE AS ABAS)
# =========================
st.subheader("⚙️ Parâmetros Gerais")

# Label dinâmico para o campo de ICMS de entrada / ICMS ST
if tipo_produto == "Sem ST":
    label_icms_entrada = "Crédito ICMS %"
    help_icms_entrada = "ICMS de crédito na entrada. Informe em % (ex.: 18 = 18%)."
else:
    label_icms_entrada = "ICMS ST %"
    help_icms_entrada = "ICMS ST (base para cálculo e recuperação). Informe em %."

col_g1, col_g2 = st.columns(2)
with col_g1:
    st.session_state.icms_entrada_pct = st.number_input(
        label_icms_entrada,
        min_value=0.0,
        step=0.05,
        value=st.session_state.get("icms_entrada_pct", 18.00),
        format="%.2f",
        help=help_icms_entrada,
        key="icms_entrada_pct_global",
    )
    st.session_state.pis_cofins_entrada_pct = st.number_input(
        "Crédito PIS/COFINS %",
        min_value=0.0,
        step=0.05,
        value=st.session_state.get("pis_cofins_entrada_pct", 9.25),
        format="%.2f",
        help="Informe em % (ex.: 9,25 = 9,25%).",
        key="pis_cofins_entrada_pct_global",
    )
    st.session_state.despesas_pct = st.number_input(
        "Despesas %",
        min_value=0.0,
        step=0.05,
        value=st.session_state.get("despesas_pct", 2.00),
        format="%.2f",
        help="Despesas adicionais em %. ",
        key="despesas_pct_global",
    )

with col_g2:
    # Débito ICMS só aparece para produtos sem ST
    if tipo_produto == "Sem ST":
        st.session_state.icms_saida_pct = st.number_input(
            "Débito ICMS %",
            min_value=0.0,
            step=0.05,
            value=st.session_state.get("icms_saida_pct", 18.00),
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
        help="Informe em %. ",
        key="pis_cofins_saida_pct_global",
    )

# Valores compartilhados usados nas abas
icms_entrada_pct = st.session_state.icms_entrada_pct
pis_cofins_entrada_pct = st.session_state.pis_cofins_entrada_pct
despesas_pct = st.session_state.despesas_pct
icms_saida_pct = st.session_state.icms_saida_pct if tipo_produto == "Sem ST" else 0.0
pis_cofins_saida_pct = st.session_state.pis_cofins_saida_pct

st.markdown(
    """
    <hr style="margin-top: 0.2rem; margin-bottom: 0.2rem;">
    """,
    unsafe_allow_html=True,
)

# =========================
# FUNÇÃO AUXILIAR: CALCULAR C11 (TOTAL SAÍDA) CONFORME ST
# =========================
def calcular_total_saida(icms_saida_f: float, pis_cofins_saida_f: float, modo_st: str) -> float:
    """
    Retorna C11 em fração (0-1).
    - Sem ST: C11 = C9 + (C10 - (C10*C9))
    - Com ST: C11 = C10  (apenas PIS/COFINS; ICMS saída não entra como débito)
    """
    if modo_st == "Sem ST":
        return icms_saida_f + (pis_cofins_saida_f - (pis_cofins_saida_f * icms_saida_f))
    else:  # "Com ST"
        return pis_cofins_saida_f

# =========================
# TABS
# =========================
aba1, aba2 = st.tabs(["Valor NF", "Sell In"])

# =========================
# 🧮 ABA 1 – SIMULADOR NF
# =========================
with aba1:
    ultimo_resultado = None

    with st.form("form_preco"):
        st.subheader("Dados de entrada – Valor NF")

        col3, col4 = st.columns(2)
        with col3:
            preco = st.number_input(
                "Preço De Venda R$",
                min_value=0.0,
                step=0.05,
                format="%.2f",
                key="preco_aba1",
            )
        with col4:
            margem_pct = st.number_input(
                "Margem %",
                min_value=0.0,
                step=0.05,
                value=0.00,
                format="%.2f",
                help="Margem de lucro em % (ex.: 20 = 20%).",
                key="margem_pct_aba1",
            )

        submitted = st.form_submit_button("Calcular e adicionar à lista")

    if submitted:
        # Converte tudo para fração
        icms_entrada_f = icms_entrada_pct / 100.0
        pis_cofins_entrada_f = pis_cofins_entrada_pct / 100.0
        despesas_f = despesas_pct / 100.0
        icms_saida_f = icms_saida_pct / 100.0
        pis_cofins_saida_f = pis_cofins_saida_pct / 100.0
        margem_f = margem_pct / 100.0

        # TOTAL SAÍDA conforme tipo de produto
        total_saida_f = calcular_total_saida(icms_saida_f, pis_cofins_saida_f, tipo_produto)

        # 👉 CUSTO LÍQUIDO (igual para Sem ST e Com ST):
        # C7 = PREÇO * (1 - (MARGEM + C11))
        custo_liquido = preco * (1 - (margem_f + total_saida_f))

        # 👉 CUSTO NF
        if tipo_produto == "Sem ST":
            # Fórmula original (sem ST):
            # C3 = C7 / (1 - C4 - C5*(1 - C4) + C6)
            try:
                custo_nf = custo_liquido / (
                    1 - icms_entrada_f - pis_cofins_entrada_f * (1 - icms_entrada_f) + despesas_f
                )
            except ZeroDivisionError:
                custo_nf = float("nan")
        else:
            # COM ST – usando sua fórmula de custo líquido:
            # C7 = NF - ((NF - NF*ICMS_ST)*PIS_COFINS) + (NF*DESPESAS) + (NF*ICMS_ST)
            # Fazendo a álgebra, isso equivale a:
            # C7 = NF * [ 1 - (1-ICMS_ST)*PIS_COFINS + DESPESAS + ICMS_ST ]
            # Logo:
            # NF = C7 / [ 1 - (1-ICMS_ST)*PIS_COFINS + DESPESAS + ICMS_ST ]
            try:
                denom = 1 - (1 - icms_entrada_f) * pis_cofins_entrada_f + despesas_f + icms_entrada_f
                custo_nf = custo_liquido / denom
            except ZeroDivisionError:
                custo_nf = float("nan")

        # PMZ
        try:
            pmz = custo_liquido / (1 - total_saida_f)
        except ZeroDivisionError:
            pmz = float("nan")

        # Guarda registro
        linha = {
            "Tipo": tipo_produto,
            "Valor NF R$": custo_nf,
            "Crédito ICMS/ICMS ST %": icms_entrada_pct,
            "Crédito PIS/COFINS %": pis_cofins_entrada_pct,
            "Despesas %": despesas_pct,
            "Custo Líquido R$": custo_liquido,
            "Débito ICMS %": icms_saida_pct if tipo_produto == "Sem ST" else 0.0,
            "Débito PIS/COFINS %": pis_cofins_saida_pct,
            "Imposto Total %": total_saida_f * 100,
            "PMZ R$": pmz,
            "Preço de Venda R$": preco,
            "Margem %": margem_pct,
        }

        st.session_state.registros.append(linha)
        ultimo_resultado = linha

        st.success("Cálculos realizados e linha adicionada à lista!")

    # Mostra o Resultado em destaque
    if ultimo_resultado:
        st.subheader("🧮 Resultado")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Custo NF", f"R$ {ultimo_resultado['Valor NF R$']:.2f}")
            st.metric("Custo Líquido", f"R$ {ultimo_resultado['Custo Líquido R$']:.2f}")
        with col_b:
            st.metric("PMZ", f"R$ {ultimo_resultado['PMZ R$']:.2f}")
            st.metric("Total Imposto de Saída", f"{ultimo_resultado['Imposto Total %']:.2f}%")

    # Tabela
    st.subheader("📋 Lista de simulações – Valor NF")
    if st.session_state.registros:
        df = pd.DataFrame(st.session_state.registros)

        # 👇 evita erro de None em formatação
        df = df.fillna(0.0)

        format_dict = {
            "Valor NF R$": "{:,.2f}",
            "Custo Líquido R$": "{:,.2f}",
            "PMZ R$": "{:,.2f}",
            "Preço de Venda R$": "{:,.2f}",
            "Crédito ICMS/ICMS ST %": "{:,.2f}%",
            "Crédito PIS/COFINS %": "{:,.2f}%",
            "Despesas %": "{:,.2f}%",
            "Débito ICMS %": "{:,.2f}%",
            "Débito PIS/COFINS %": "{:,.2f}%",
            "Imposto Total %": "{:,.2f}%",
            "Margem %": "{:,.2f}%",
        }
        st.dataframe(df.style.format(format_dict))
    else:
        st.info("Nenhuma simulação cadastrada ainda. Preencha o formulário acima para começar.")

# =========================
# 💰 ABA 2 – SELL IN
# =========================
with aba2:
    st.subheader("Dados de entrada – Sell In")

    with st.form("form_verba"):
        col3, col4 = st.columns(2)
        with col3:
            custo_nf_input = st.number_input(
                "CUSTO NF (R$)",
                min_value=0.0,
                step=0.05,
                format="%.2f",
                key="custo_nf_input_aba2",
            )
            preco_v = st.number_input(
                "Preço De Venda R$",
                min_value=0.0,
                step=0.05,
                format="%.2f",
                key="preco_v_aba2",
            )
        with col4:
            margem_pct_v = st.number_input(
                "Margem %",
                min_value=0.0,
                step=0.05,
                value=0.00,
                format="%.2f",
                help="Margem de lucro desejada em %.",
                key="margem_pct_v_aba2",
            )

        submitted_verba = st.form_submit_button("Calcular verba necessária")

    if submitted_verba:
        if preco_v <= 0:
            st.error("O PREÇO de venda deve ser maior que zero.")
        else:
            # Converte para fração
            icms_entrada_f_v = icms_entrada_pct / 100.0
            pis_cofins_entrada_f_v = pis_cofins_entrada_pct / 100.0
            despesas_f_v = despesas_pct / 100.0
            icms_saida_f_v = icms_saida_pct / 100.0
            pis_cofins_saida_f_v = pis_cofins_saida_pct / 100.0
            margem_f_v = margem_pct_v / 100.0

            # 1) CUSTO LÍQUIDO ATUAL (a partir do CUSTO NF informado)
            if tipo_produto == "Sem ST":
                # D = 1 - C4 - C5*(1 - C4) + C6
                D_v = 1 - icms_entrada_f_v - pis_cofins_entrada_f_v * (1 - icms_entrada_f_v) + despesas_f_v
            else:
                # Com ST: usando mesma lógica invertida do CL:
                # C7 = NF * [ 1 - (1-ICMS_ST)*PIS_COFINS + DESPESAS + ICMS_ST ]
                D_v = 1 - (1 - icms_entrada_f_v) * pis_cofins_entrada_f_v + despesas_f_v + icms_entrada_f_v

            custo_liquido_atual = custo_nf_input * D_v

            # 2) TOTAL SAÍDA (fração) conforme tipo de produto
            total_saida_f_v = calcular_total_saida(icms_saida_f_v, pis_cofins_saida_f_v, tipo_produto)

            # 3) CUSTO LÍQUIDO OBJETIVO
            custo_liquido_obj = preco_v * (1 - (margem_f_v + total_saida_f_v))

            # 4) VERBA NECESSÁRIA
            verba_reais = custo_liquido_atual - custo_liquido_obj

            verba_pct_sobre_nf = (verba_reais / custo_nf_input * 100.0) if custo_nf_input > 0 else float("nan")
            verba_pct_sobre_preco = (verba_reais / preco_v * 100.0) if preco_v > 0 else float("nan")

            linha_verba = {
                "Tipo": tipo_produto,
                "Valor NF R$": custo_nf_input,
                "Preço de Venda R$": preco_v,
                "Margem %": margem_pct_v,
                "Crédito ICMS/ICMS ST %": icms_entrada_pct,
                "PIS/COFINS ENT (C5) [%]": pis_cofins_entrada_pct,
                "Despesas %": despesas_pct,
                "Débito ICMS %": icms_saida_pct if tipo_produto == "Sem ST" else 0.0,
                "Débito PIS/COFINS %": pis_cofins_saida_pct,
                "CUSTO LÍQUIDO ATUAL (C7) [R$]": custo_liquido_atual,
                "CUSTO LÍQUIDO OBJ (C7) [R$]": custo_liquido_obj,
                "Imposto Total %": total_saida_f_v * 100,
                "VERBA (R$)": verba_reais,
                "VERBA / NF [%]": verba_pct_sobre_nf,
                "VERBA / PREÇO [%]": verba_pct_sobre_preco,
            }

            st.session_state.registros_verba.append(linha_verba)

            colv1, colv2 = st.columns(2)
            with colv1:
                st.metric("Custo Líquido atual (C7)", f"R$ {custo_liquido_atual:,.2f}")
                st.metric("Custo Líquido objetivo (C7 alvo)", f"R$ {custo_liquido_obj:,.2f}")
                st.metric("Total Imposto de Saída (C11)", f"{total_saida_f_v * 100:,.2f}%")
            with colv2:
                st.metric("Verba necessária (R$)", f"R$ {verba_reais:,.2f}")
                st.metric("Verba sobre NF (%)", f"{verba_pct_sobre_nf:,.2f}%")
                st.metric("Verba sobre preço (%)", f"{verba_pct_sobre_preco:,.2f}%")

    # --- Tabela de resultados da ABA 2 ---
    st.subheader("📋 Lista de simulações de verba – Aba 2")

    if st.session_state.registros_verba:
        df_verba = pd.DataFrame(st.session_state.registros_verba)

        # 👇 evita erro de None nas colunas de % quando estiverem zeradas
        df_verba = df_verba.fillna(0.0)

        format_dict_verba = {
            "Valor NF R$": "{:,.2f}",
            "Preço de Venda R$": "{:,.2f}",
            "Margem %": "{:,.2f}%",
            "Crédito ICMS/ICMS ST %": "{:,.2f}%",
            "PIS/COFINS ENT (C5) [%]": "{:,.2f}%",
            "Despesas %": "{:,.2f}%",
            "Débito ICMS %": "{:,.2f}%",
            "Débito PIS/COFINS %": "{:,.2f}%",
            "CUSTO LÍQUIDO ATUAL (C7) [R$]": "{:,.2f}",
            "CUSTO LÍQUIDO OBJ (C7) [R$]": "{:,.2f}",
            "Imposto Total %": "{:,.2f}%",
            "VERBA (R$)": "{:,.2f}",
            "VERBA / NF [%]": "{:,.2f}%",
            "VERBA / PREÇO [%]": "{:,.2f}%",
        }

        st.dataframe(df_verba.style.format(format_dict_verba))
    else:
        st.info("Nenhuma simulação de verba cadastrada ainda. Preencha o formulário acima para começar.")
