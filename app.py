import streamlit as st
import os

st.set_page_config(page_title="BKS Corretora", page_icon="🚗", layout="wide")

# Tenta carregar o logo se a imagem existir no repositório
if os.path.exists("logo.png"):
    st.image("logo.png", width=250)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=250)
else:
    st.info("💡 Para exibir seu logo aqui, faça o upload da imagem como 'logo.png' no GitHub.")

st.title("BKS Corretora - Gerador de Cotações")
st.write("Sistema em construção para padronização de PDFs.")
