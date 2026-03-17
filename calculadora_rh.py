import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Calculadora de Comissão RH", layout="wide")

st.title("📊 Calculadora de Comissão Dinâmica")
st.write("Faça o upload da planilha e ajuste os gatilhos de comissão.")
st.divider()

# ==========================================
# 1. LEITURA DA PLANILHA 
# ==========================================

arquivo_upload = st.file_uploader("Faça o upload da 'Planilha de Vendas' (Excel)", type=["xlsx"])

if arquivo_upload is not None:
    try:
        df_scan = pd.read_excel(arquivo_upload, header=None)
        linha_cabecalho = None
        
        for i, linha in df_scan.head(20).iterrows():
            valores = [str(v).strip().lower() for v in linha.values]
            if 'colaborador' in valores and 'contratos assinados' in valores:
                linha_cabecalho = i
                break
        
        if linha_cabecalho is None:
            st.error("❌ Não encontrei as colunas necessárias.")
        else:
            df_vendas = pd.read_excel(arquivo_upload, skiprows=linha_cabecalho)
            df_vendas.columns = df_vendas.columns.astype(str).str.strip().str.lower()
            
            colunas_necessarias = ['colaborador', 'contratos assinados', 'contratos a assinar']
            
            if not all(col in df_vendas.columns for col in colunas_necessarias):
                st.error("⚠️ As colunas encontradas não batem exatamente com o esperado.")
            else:
                st.success("✅ Planilha carregada com sucesso!")
                st.divider()

                # Remove linhas vazias
                df_vendas = df_vendas.dropna(subset=['colaborador'])
                
                # ---> A CORREÇÃO ESTÁ AQUI <---
                # Padroniza os nomes (tira espaços invisíveis e deixa como 'Nome')
                df_vendas['colaborador'] = df_vendas['colaborador'].astype(str).str.strip().str.title()
                
                df_vendas['contratos assinados'] = pd.to_numeric(df_vendas['contratos assinados'], errors='coerce').fillna(0)
                df_vendas['contratos a assinar'] = pd.to_numeric(df_vendas['contratos a assinar'], errors='coerce').fillna(0)

                # Agora o agrupamento vai fundir perfeitamente as Anas
                df_agrupado = df_vendas.groupby('colaborador').agg(
                    valor_assinados=('contratos assinados', 'sum'),
                    vendas_assinados=('contratos assinados', lambda x: (x > 0).sum()),
                    valor_a_assinar=('contratos a assinar', 'sum'),
                    vendas_a_assinar=('contratos a assinar', lambda x: (x > 0).sum())
                ).reset_index()

                # ==========================================
                # 2. LÓGICA DE NEGÓCIO E INTERFACE
                # ==========================================
                
                dados_relatorio = []

                for index, linha in df_agrupado.iterrows():
                    vendedor = linha['colaborador'] # Já está limpo e formatado
                    
                    valor_assinados = float(linha['valor_assinados'])
                    qtd_assinados = int(linha['vendas_assinados'])
                    
                    valor_a_assinar = float(linha['valor_a_assinar'])
                    qtd_a_assinar = int(linha['vendas_a_assinar'])
                    
                    total_vendido = valor_assinados + valor_a_assinar
                    
                    with st.expander(f"👤 Colaborador: {vendedor} | Valor Base Total: R$ {total_vendido:,.2f}", expanded=True):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.markdown("### Configurações")
                            bateu_meta_checkbox = st.checkbox(f"Bateu a Meta?", value=False, key=f"meta_{vendedor}")
                            
                            if bateu_meta_checkbox:
                                st.success("✅ Upgrade de Meta ativado!")
                                padrao_a_assinar, padrao_assinado = 3.0, 4.0
                            else:
                                st.warning("⏳ Usando taxas base.")
                                padrao_a_assinar, padrao_assinado = 1.0, 2.0
                            
                            st.markdown("**Ajuste Fino das Porcentagens (%):**")
                            taxa_a_assinar = st.slider("Taxa - Contratos a Assinar", min_value=0.0, max_value=10.0, value=padrao_a_assinar, step=0.1, key=f"t_nao_{vendedor}")
                            taxa_assinados = st.slider("Taxa - Contratos Assinados", min_value=0.0, max_value=10.0, value=padrao_assinado, step=0.1, key=f"t_sim_{vendedor}")

                        with col2:
                            st.markdown("### Detalhamento das Comissões")
                            
                            comissao_a_assinar = valor_a_assinar * (taxa_a_assinar / 100)
                            comissao_assinados = valor_assinados * (taxa_assinados / 100)
                            comissao_total = comissao_a_assinar + comissao_assinados
                            
                            detalhes = [
                                {
                                    "Status": "Apenas Pago (A Assinar)", 
                                    "Vendas": qtd_a_assinar, 
                                    "Valor Base (R$)": valor_a_assinar, 
                                    "Taxa (%)": taxa_a_assinar, 
                                    "Comissão (R$)": comissao_a_assinar
                                },
                                {
                                    "Status": "Pago e Assinado", 
                                    "Vendas": qtd_assinados, 
                                    "Valor Base (R$)": valor_assinados, 
                                    "Taxa (%)": taxa_assinados, 
                                    "Comissão (R$)": comissao_assinados
                                }
                            ]
                            
                            st.dataframe(pd.DataFrame(detalhes), use_container_width=True)
                            st.markdown(f"<h3 style='color: green;'>Comissão Total a Pagar: R$ {comissao_total:,.2f}</h3>", unsafe_allow_html=True)
                            
                            dados_relatorio.append({
                                "Colaborador": vendedor,
                                "Bateu Meta": "Sim" if bateu_meta_checkbox else "Não",
                                "Qtd A Assinar": qtd_a_assinar,
                                "Base A Assinar (R$)": valor_a_assinar,
                                "Comissão A Assinar (R$)": comissao_a_assinar,
                                "Qtd Assinados": qtd_assinados,
                                "Base Assinados (R$)": valor_assinados,
                                "Comissão Assinados (R$)": comissao_assinados,
                                "Comissão Total (R$)": comissao_total
                            })

                # ==========================================
                # 3. EXPORTAÇÃO
                # ==========================================
                if dados_relatorio:
                    st.divider()
                    st.subheader("📑 Relatório Final")
                    df_rel = pd.DataFrame(dados_relatorio)
                    st.dataframe(df_rel, use_container_width=True)
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_rel.to_excel(writer, index=False)
                    
                    st.download_button("📥 Baixar Relatório Final", output.getvalue(), "comissoes_calculadas.xlsx")

    except Exception as e:
        st.error(f"Ocorreu um erro no processamento: {e}")