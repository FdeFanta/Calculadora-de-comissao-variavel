import streamlit as st
import pandas as pd

st.set_page_config(page_title="Calculadora de Comissão RH", layout="wide")

st.title("📊 Calculadora de Comissão Dinâmica")
st.write("Protótipo de comissionamento com gatilhos de Meta, Pagamento e Assinatura.")

# ==========================================
# 1. SIMULANDO AS PLANILHAS (Dados de Teste)
# ==========================================

# Planilha 1: Regras dos Colaboradores (As taxas estão em porcentagem %)
dados_regras = pd.DataFrame({
    'Vendedor': ['João', 'Maria'],
    'Meta': [200000, 100000], # Meta em R$
    'Taxa_Base_Pago': [1.0, 1.5],       # Se NÃO bater a meta (só pago)
    'Taxa_Base_Assinado': [2.0, 2.5],   # Se NÃO bater a meta (pago e assinado)
    'Taxa_Meta_Pago': [3.0, 3.5],       # Se BATER a meta (só pago)
    'Taxa_Meta_Assinado': [4.0, 4.5]    # Se BATER a meta (pago e assinado)
})

# Planilha 2: Vendas do Mês
dados_vendas = pd.DataFrame({
    'Contrato': ['C001', 'C002', 'C003', 'C004', 'C005'],
    'Vendedor': ['João', 'João', 'João', 'Maria', 'Maria'],
    'Valor': [100000, 120000, 50000, 80000, 30000],
    'Pago': ['S', 'S', 'N', 'S', 'S'],       # 'N' será ignorado na conta
    'Assinado': ['S', 'N', 'N', 'S', 'S']
})

# ==========================================
# 2. LÓGICA DE NEGÓCIO E INTERFACE
# ==========================================

# Filtra: Só entra na conta o que estiver PAGO ('S')
vendas_validas = dados_vendas[dados_vendas['Pago'] == 'S'].copy()

st.divider()

# Loop para criar uma área separada para cada vendedor
for index, regra in dados_regras.iterrows():
    vendedor = regra['Vendedor']
    meta = regra['Meta']
    
    # Pega só as vendas válidas (pagas) desse vendedor
    vendas_vendedor = vendas_validas[vendas_validas['Vendedor'] == vendedor]
    total_vendido = vendas_vendedor['Valor'].sum()
    
    # Verifica automaticamente se bateu a meta
    bateu_meta_auto = total_vendido >= meta

    # Cria uma "caixa" visual para cada vendedor
    with st.expander(f"👤 Colaborador: {vendedor} | Total Vendido (Pago): R$ {total_vendido:,.2f} | Meta: R$ {meta:,.2f}", expanded=True):
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### Configurações")
            # Aqui está o CHECKBOX que você pediu. Ele já vem marcado se bater a meta, mas o RH pode mudar.
            bateu_meta_checkbox = st.checkbox(f"Bateu a Meta? (Upgrade de Taxas)", value=bateu_meta_auto, key=f"meta_{vendedor}")
            
            # Define quais taxas usar baseado no checkbox
            if bateu_meta_checkbox:
                padrao_pago = regra['Taxa_Meta_Pago']
                padrao_assinado = regra['Taxa_Meta_Assinado']
                st.success("✅ Upgrade de Meta ativado!")
            else:
                padrao_pago = regra['Taxa_Base_Pago']
                padrao_assinado = regra['Taxa_Base_Assinado']
                st.warning("⏳ Usando taxas base (sem meta).")
            
            # Aqui estão os SCROLLS (Sliders) para o ajuste fino do RH
            st.markdown("**Ajuste Fino das Porcentagens (%):**")
            taxa_pago_real = st.slider("Taxa para Contratos apenas Pagos", min_value=0.0, max_value=10.0, value=float(padrao_pago), step=0.1, key=f"pago_{vendedor}")
            taxa_assinado_real = st.slider("Taxa para Contratos Pagos e Assinados", min_value=0.0, max_value=10.0, value=float(padrao_assinado), step=0.1, key=f"assin_{vendedor}")

        with col2:
            st.markdown("### Cálculo das Comissões")
            comissao_total = 0
            
            # Tabela de detalhamento de cada contrato
            detalhes = []
            for _, venda in vendas_vendedor.iterrows():
                if venda['Assinado'] == 'S':
                    taxa_aplicada = taxa_assinado_real
                    status = "Pago & Assinado"
                else:
                    taxa_aplicada = taxa_pago_real
                    status = "Apenas Pago"
                
                valor_comissao = venda['Valor'] * (taxa_aplicada / 100)
                comissao_total += valor_comissao
                
                detalhes.append({
                    "Contrato": venda['Contrato'],
                    "Valor Base": venda['Valor'],
                    "Status": status,
                    "Taxa (%)": taxa_aplicada,
                    "Comissão (R$)": valor_comissao
                })
            
            # Mostra a tabela detalhada e o total
            if detalhes:
                st.dataframe(pd.DataFrame(detalhes), use_container_width=True)
                st.markdown(f"<h3 style='color: green;'>Comissão Total a Pagar: R$ {comissao_total:,.2f}</h3>", unsafe_allow_html=True)
            else:
                st.info("Nenhuma venda paga encontrada para este vendedor.")