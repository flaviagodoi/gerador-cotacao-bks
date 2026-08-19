import streamlit as st
import pdfplumber
import os

st.set_page_config(page_title="BKS Corretora", page_icon="🚗", layout="wide")

# Exibição do Logo BKS
if os.path.exists("logo.png"):
    st.image("logo.png", width=220)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=220)

st.title("Gerador de Relatório Comparativo - BKS")
st.write("Faça o upload dos PDFs das cotações abaixo para testar a leitura dos dados.")

# Upload de arquivos
st.subheader("1. Upload das Cotações (PDF)")
uploaded_files = st.file_uploader(
    "Arraste ou selecione os PDFs da Porto, Allianz e Tokio",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} arquivo(s) carregado(s) com sucesso!")
    
    st.subheader("2. Leitura dos Dados Extraídos")
    
    # Exibe o conteúdo lido de cada PDF para podermos mapear os campos exatos
    for index, file in enumerate(uploaded_files):
        with st.expander(f"📄 Visualizar texto lido: {file.name}"):
            with pdfplumber.open(file) as pdf:
                texto_completo = ""
                for page in pdf.pages:
                    texto_completo += page.extract_text() or ""
                st.text_area(f"Texto extraído do arquivo {index+1}", texto_completo, height=250)
