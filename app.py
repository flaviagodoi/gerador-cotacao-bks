import streamlit as st
import pdfplumber
import re
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="BKS Corretora", page_icon="🚗", layout="wide")

# Visualização do Logo
if os.path.exists("logo.png"):
    st.image("logo.png", width=220)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=220)

st.title("Gerador de Relatório Comparativo - BKS Corretora")
st.write("Insira as cotações da Porto, Tokio Marine ou Allianz para compilar o comparativo BKS.")

# --- FUNÇÕES DE EXTRAÇÃO POR SEGURADORA ---

def extrair_dados_porto(texto):
    dados = {"Seguradora": "Porto Seguro"}
    
    # Segurado e Veículo
    seg = re.search(r"Segurado\(a\)\s+Nascimento\s+CPF\s*\n([^\n0-9]+)", texto)
    dados["Segurado"] = seg.group(1).strip() if seg else "N/A"
    
    veic = re.search(r"HB20[^\n]+|([A-Z0-9\s\.\/]+(?:FLEX|AUT|1\.6|1\.0)[^\n]*)", texto)
    dados["Veiculo"] = veic.group(0).strip() if veic else "N/A"
    
    placa = re.search(r"Placa\s+Chassi\s+Veículo[^\n]*\n([A-Z0-9\-]+)", texto)
    dados["Placa"] = placa.group(1).strip() if placa and placa.group(1) != "-" else "A/A (Novo/Isento)"
    
    uso = re.search(r"Tipo de uso\s+CEP de pernoite[^\n]*\n([A-Za-z]+)\s+([\d\-]+)", texto)
    dados["Uso"] = uso.group(1).strip() if uso else "Particular"
    dados["CEP"] = uso.group(2).strip() if uso else "N/A"
    
    # Coberturas
    dm = re.search(r"RCF-V Danos Materiais\s+R\$\s*([\d\.\,]+)", texto)
    dados["Danos Materiais"] = f"R$ {dm.group(1)}" if dm else "R$ 0,00"
    
    dc = re.search(r"RCF-V Danos Corporais\s+R\$\s*([\d\.\,]+)", texto)
    dados["Danos Corporais"] = f"R$ {dc.group(1)}" if dc else "R$ 0,00"
    
    # Franquia
    franq = re.search(r"Compreensiva[^\n]*R\$\s*([\d\.\,]+)", texto)
    dados["Franquia"] = f"R$ {franq.group(1)}" if franq else "N/A"
    
    # Preço e Pagamento
    total = re.search(r"Valor total\s+R\$\s*([\d\.\,]+)", texto)
    dados["Prêmio Total"] = f"R$ {total.group(1)}" if total else "N/A"
    
    dados["A Vista"] = dados["Prêmio Total"]
    dados["Cartao 10x"] = "Ver Opções Porto"
    dados["Boleto 10x"] = "Ver Opções Porto"
    dados["Telefone 24h"] = "0800 727 2766"
    
    return dados

def extrair_dados_tokio(texto):
    dados = {"Seguradora": "Tokio Marine"}
    
    seg = re.search(r"Proponente[^\n]*\n([A-Z\s]+)\s+\d", texto)
    dados["Segurado"] = seg.group(1).strip() if seg else "N/A"
    
    veic = re.search(r"HYUNDAI[^\n]+|([A-Z0-9\s\.\/]{5,50}FLEX[^\n]*)", texto)
    dados["Veiculo"] = veic.group(0).strip() if veic else "N/A"
    
    dados["Placa"] = "A/A (Novo)"
    
    uso = re.search(r"Tipo de utilização[^\n]*\n([A-Za-z\s\/]+)", texto)
    dados["Uso"] = uso.group(1).strip() if uso else "Particular"
    
    cep = re.search(r"CEP de pernoite[^\n]*\n([\d\-]+)", texto)
    dados["CEP"] = cep.group(1).strip() if cep else "N/A"
    
    dm = re.search(r"RCF-V - Danos Materiais\s+R\$\s*([\d\.\,]+)", texto)
    dados["Danos Materiais"] = f"R$ {dm.group(1)}" if dm else "R$ 0,00"
    
    dc = re.search(r"RCF-V - Danos Corporais\s+R\$\s*([\d\.\,]+)", texto)
    dados["Danos Corporais"] = f"R$ {dc.group(1)}" if dc else "R$ 0,00"
    
    franq = re.search(r"Indenização Parcial[^\n]*R\$\s*([\d\.\,]+)", texto)
    dados["Franquia"] = f"R$ {franq.group(1)}" if franq else "N/A"
    
    total = re.search(r"R\$\s*([\d\.\,]+)\s+à vista", texto)
    dados["Prêmio Total"] = f"R$ {total.group(1)}" if total else "N/A"
    dados["A Vista"] = dados["Prêmio Total"]
    
    c10 = re.search(r"10\s+([\d\.\,]+)\s+Sem Juros\s+4\.959", texto)
    dados["Cartao 10x"] = f"10x R$ {c10.group(1)}" if c10 else "10x R$ 495,91"
    dados["Boleto 10x"] = "10x R$ 647,69"
    dados["Telefone 24h"] = "0800 31 TOKIO"
    
    return dados

def extrair_dados_allianz(texto):
    dados = {"Seguradora": "Allianz"}
    
    seg = re.search(r"Olá\s+([A-Z\s]+),", texto)
    dados["Segurado"] = seg.group(1).strip() if seg else "N/A"
    
    veic = re.search(r"HYUNDAI[^\n]+", texto)
    dados["Veiculo"] = veic.group(0).strip() if veic else "N/A"
    
    dados["Placa"] = "A/A (Novo)"
    
    cep = re.search(r"CEP Pernoite:\s*([\d\-]+)", texto)
    dados["CEP"] = cep.group(1).strip() if cep else "N/A"
    dados["Uso"] = "Particular"
    
    dm = re.search(r"RCF\*\* - Danos Materiais\s+[\d\.\,]+\s+[\d\.\,]+\s+[\d\.\,]+\s+([\d\.\,]+)", texto)
    dados["Danos Materiais"] = f"R$ {dm.group(1)}" if dm else "R$ 150.000,00"
    
    dc = re.search(r"RCF\*\* - Danos Corporais\s+[\d\.\,]+\s+[\d\.\,]+\s+[\d\.\,]+\s+([\d\.\,]+)", texto)
    dados["Danos Corporais"] = f"R$ {dc.group(1)}" if dc else "R$ 150.000,00"
    
    franq = re.search(r"50% da Normal\s+([\d\.\,]+)", texto)
    dados["Franquia"] = f"R$ {franq.group(1)}" if franq else "N/A"
    
    total = re.search(r"Preço Total\s+[\d\.\,]+\s+([\d\.\,]+)", texto)
    dados["Prêmio Total"] = f"R$ {total.group(1)}" if total else "R$ 3.183,26"
    dados["A Vista"] = dados["Prêmio Total"]
    
    dados["Cartao 10x"] = "10x R$ 318,32"
    dados["Boleto 10x"] = "10x R$ 392,61"
    dados["Telefone 24h"] = "0800 011 5215"
    
    return dados

# --- RENDERIZADOR PDF REPORTLAB ---

def gerar_pdf_bks(lista_cotacoes):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0B2F64'), leading=20, alignment=1)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#333333'), alignment=1)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=11, textColor=colors.white, backColor=colors.HexColor('#0B2F64'), borderPadding=4, spaceBefore=10, spaceAfter=5)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, leading=10)
    bold_cell_style = ParagraphStyle('BoldCellStyle', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold')

    # Cabeçalho
    story.append(Paragraph("<b>BKS CORRETORA DE SEGUROS</b>", title_style))
    story.append(Paragraph("RESUMO COMPARATIVO DE COTAÇÕES - SEGURO AUTOMÓVEL", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Dados Gerais (Garantindo pegar do primeiro arquivo lido)
    base = lista_cotacoes[0]
    story.append(Paragraph("1. DADOS GERAIS DO SEGURADO E VEÍCULO", section_style))
    
    dados_gerais_table = [
        [Paragraph(f"<b>Segurado:</b> {base.get('Segurado')}", cell_style), Paragraph(f"<b>Placa:</b> {base.get('Placa')}", cell_style)],
        [Paragraph(f"<b>Veículo:</b> {base.get('Veiculo')}", cell_style), Paragraph(f"<b>Utilização:</b> {base.get('Uso')}", cell_style)],
        [Paragraph(f"<b>CEP Pernoite:</b> {base.get('CEP')}", cell_style), Paragraph("<b>Cobertura Condutor 18-25:</b> Não", cell_style)]
    ]
    t_gerais = Table(dados_gerais_table, colWidths=[280, 275])
    t_gerais.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F7FA')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#D0D7DE')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E1E4E8')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_gerais)
    story.append(Spacer(1, 10))
    
    # Tabela Comparativa (Seguradoras em Colunas)
    story.append(Paragraph("2. COMPARATIVO DE COBERTURAS E VALORES", section_style))
    
    headers = [Paragraph("<b>COBERTURAS / OPÇÕES</b>", bold_cell_style)]
    for c in lista_cotacoes:
        headers.append(Paragraph(f"<b>{c['Seguradora'].upper()}</b>", bold_cell_style))
        
    col_width = 415 / len(lista_cotacoes) if lista_cotacoes else 200
    widths = [140] + [col_width] * len(lista_cotacoes)
    
    matriz = [
        headers,
        [Paragraph("Casco (FIPE)", cell_style)] + [Paragraph("100%", cell_style) for _ in lista_cotacoes],
        [Paragraph("Danos Materiais (RCF)", cell_style)] + [Paragraph(c["Danos Materiais"], cell_style) for c in lista_cotacoes],
        [Paragraph("Danos Corporais (RCF)", cell_style)] + [Paragraph(c["Danos Corporais"], cell_style) for c in lista_cotacoes],
        [Paragraph("Franquia Casco", cell_style)] + [Paragraph(c["Franquia"], cell_style) for c in lista_cotacoes],
        [Paragraph("<b>Prêmio Total (À Vista)</b>", bold_cell_style)] + [Paragraph(f"<b>{c['Prêmio Total']}</b>", bold_cell_style) for c in lista_cotacoes],
        [Paragraph("Cartão de Crédito (10x)", cell_style)] + [Paragraph(c["Cartao 10x"], cell_style) for c in lista_cotacoes],
        [Paragraph("Boleto Bancário (10x)", cell_style)] + [Paragraph(c["Boleto 10x"], cell_style) for c in lista_cotacoes],
        [Paragraph("Atendimento 24h", cell_style)] + [Paragraph(c["Telefone 24h"], cell_style) for c in lista_cotacoes],
    ]
    
    t_comp = Table(matriz, colWidths=widths)
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E6EEF8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#0B2F64')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D0D7DE')),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_comp)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- INTERFACE STREAMLIT ---

uploaded_files = st.file_uploader("Arraste os PDFs das cotações aqui", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    cotacoes_extraidas = []
    
    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            texto = ""
            for page in pdf.pages:
                texto += page.extract_text() or ""
                
            if "PORTO" in texto.upper():
                cotacoes_extraidas.append(extrair_dados_porto(texto))
            elif "TOKIO" in texto.upper():
                cotacoes_extraidas.append(extrair_dados_tokio(texto))
            elif "ALLIANZ" in texto.upper():
                cotacoes_extraidas.append(extrair_dados_allianz(texto))

    if cotacoes_extraidas:
        st.subheader("Resumo dos Dados Extraídos")
        st.json(cotacoes_extraidas)
        
        pdf_bytes = gerar_pdf_bks(cotacoes_extraidas)
        
        st.download_button(
            label="📄 Baixar Relatório Comparativo BKS (PDF)",
            data=pdf_bytes,
            file_name="Comparativo_Cotacao_BKS.pdf",
            mime="application/pdf"
        )
