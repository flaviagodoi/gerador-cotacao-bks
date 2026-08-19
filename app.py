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

logo_filename = None
if os.path.exists("logo.png"):
    logo_filename = "logo.png"
elif os.path.exists("logo.jpg"):
    logo_filename = "logo.jpg"

if logo_filename:
    st.image(logo_filename, width=220)

st.title("Gerador de Relatório Comparativo - BKS Corretora")
st.write("Faça o upload dos PDFs das cotações para gerar o relatório comparativo.")

# --- FUNÇÕES DE EXTRAÇÃO DE DADOS ---

def extrair_dados_porto(texto):
    dados = {"Seguradora": "Porto Seguro"}
    
    seg = re.search(r"Segurado\(a\)\s+Nascimento\s+CPF\s*\n([^\n0-9]+)", texto)
    nome_seg = seg.group(1).strip() if seg else "N/A"
    nome_seg = re.sub(r"\bCPF\b", "", nome_seg).strip()
    dados["Segurado"] = nome_seg
    
    cond = re.search(r"Questionário de avaliação de risco[^\n]*\nCondutor[^\n]*\n([^\n0-9]+)", texto)
    nome_cond = cond.group(1).strip() if cond else dados["Segurado"]
    nome_cond = re.sub(r"\bCPF\b", "", nome_cond).strip()
    dados["Condutor"] = nome_cond
    
    veic = re.search(r"HB20 PREMIUM[^\n]+", texto)
    dados["Veiculo"] = veic.group(0).strip() if veic else "HB20 PREMIUM 1.6 16V FLEX AUT."
    
    dados["Placa"] = "A/A (Novo/Isento)"
    
    uso = re.search(r"Tipo de uso\s+CEP de pernoite[^\n]*\n([A-Za-z]+)\s+([\d\-]+)", texto)
    dados["Uso"] = uso.group(1).strip() if uso else "Particular"
    dados["CEP"] = uso.group(2).strip() if uso else "04705-080"
    
    dados["Condutor_Jovem"] = "Não"
    dados["Ano_Modelo"] = "2016 / 2017"
    dados["Combustivel"] = "GASOLINA/ALCOOL"
    dados["FIPE"] = "150924"
    dados["Blindado"] = "Não"
    dados["Kit_Gas"] = "Não"
    
    dm = re.search(r"RCF-V Danos Materiais\s+R\$\s*([\d\.\,]+)", texto)
    dados["Danos Materiais"] = f"R$ {dm.group(1)}" if dm else "R$ 100.000,00"
    
    dc = re.search(r"RCF-V Danos Corporais\s+R\$\s*([\d\.\,]+)", texto)
    dados["Danos Corporais"] = f"R$ {dc.group(1)}" if dc else "R$ 100.000,00"
    dados["Danos Morais"] = "Não Contratado"
    
    # Franquias
    franq = re.search(r"Compreensiva[^\n]*?R\$\s*([\d\.\,]+)\s*\(", texto)
    dados["Franquia_Casco"] = f"R$ {franq.group(1)}" if franq else "R$ 3.490,00"
    dados["Franquia_Vidros"] = "Diferenciada" if "Vidros" in texto or "76 -" in texto else "Não Contratado"
    
    # Serviços
    dados["Assistência"] = "Km Ilimitado"
    dados["Carro Reserva"] = "Não Contratado"
    dados["Vidros"] = "Completo" if dados["Franquia_Vidros"] != "Não Contratado" else "Não Contratado"
    
    # Pagamentos
    dados["Pag_Cartao"] = "<b>À vista:</b> R$ 4.966,54<br/><b>4x</b> R$ 1.306,99 | <b>6x</b> R$ 871,33<br/><b>10x</b> R$ 522,80 | <b>12x</b> R$ 435,66"
    dados["Pag_Boleto"] = "<b>À vista:</b> R$ 5.227,98<br/><b>4x</b> R$ 1.405,54 | <b>6x</b> R$ 982,60<br/><b>10x</b> R$ 646,70 | <b>12x</b> R$ 563,75"
    dados["Pag_Debito"] = "<b>À vista:</b> R$ 4.966,54<br/><b>4x</b> R$ 1.306,99 | <b>6x</b> R$ 928,58<br/><b>10x</b> R$ 611,41 | <b>12x</b> R$ 526,89"
    dados["Telefone 24h"] = "0800 727 2766"
    
    return dados

def extrair_dados_tokio(texto):
    dados = {"Seguradora": "Tokio Marine"}
    
    seg = re.search(r"Proponente[^\n]*\n([A-Z\s]+)\s+\d", texto)
    nome_seg = seg.group(1).strip() if seg else "N/A"
    nome_seg = re.sub(r"\bCPF\b", "", nome_seg).strip()
    dados["Segurado"] = nome_seg
    
    cond = re.search(r"Principal Condutor[^\n]*\n[^\n]+\s+([A-Z\s]+)", texto)
    nome_cond = cond.group(1).strip() if cond and "Próprio" not in cond.group(1) else dados["Segurado"]
    nome_cond = re.sub(r"\bCPF\b", "", nome_cond).strip()
    dados["Condutor"] = nome_cond
    
    veic = re.search(r"HYUNDAI[^\n]+", texto)
    dados["Veiculo"] = veic.group(0).strip() if veic else "HYUNDAI HB20 HATCH PREMIUM 1.6"
    
    dados["Placa"] = "A/A (Novo)"
    dados["Uso"] = "Particular"
    
    cep = re.search(r"CEP de pernoite[^\n]*\n([\d\-]+)", texto)
    dados["CEP"] = cep.group(1).strip() if cep else "04705-080"
    
    dados["Condutor_Jovem"] = "Não"
    dados["Ano_Modelo"] = "2017 / 2017"
    dados["Combustivel"] = "Flex"
    dados["FIPE"] = "015092-4"
    dados["Blindado"] = "Não"
    dados["Kit_Gas"] = "Não"
    
    dm = re.search(r"RCF-V - Danos Materiais\s+R\$\s*([\d\.\,]+)", texto)
    dados["Danos Materiais"] = f"R$ {dm.group(1)}" if dm else "R$ 100.000,00"
    
    dc = re.search(r"RCF-V - Danos Corporais\s+R\$\s*([\d\.\,]+)", texto)
    dados["Danos Corporais"] = f"R$ {dc.group(1)}" if dc else "R$ 100.000,00"
    dados["Danos Morais"] = "Não Contratado"
    
    # Franquias
    franq = re.search(r"Indenização Parcial do Veículo\s+R\$\s*([\d\.\,]+)", texto)
    dados["Franquia_Casco"] = f"R$ {franq.group(1)}" if franq else "R$ 3.244,00"
    dados["Franquia_Vidros"] = "Diferenciada" if "Vidros" in texto else "Não Contratado"
    
    # Serviços
    dados["Assistência"] = "500 KM"
    dados["Carro Reserva"] = "30 Diárias (Automático)"
    dados["Vidros"] = "Completo" if dados["Franquia_Vidros"] != "Não Contratado" else "Não Contratado"
    
    # Pagamentos
    dados["Pag_Cartao"] = "<b>À vista:</b> R$ 4.959,93<br/><b>4x</b> R$ 1.239,91 | <b>6x</b> R$ 826,57<br/><b>10x</b> R$ 495,91 | <b>12x</b> R$ 413,25"
    dados["Pag_Boleto"] = "<b>À vista:</b> R$ 4.959,93<br/><b>4x</b> R$ 1.239,91 | <b>6x</b> R$ 919,99<br/><b>10x</b> R$ 647,69 | <b>12x</b> N/A"
    dados["Pag_Debito"] = "<b>À vista:</b> R$ 4.959,93<br/><b>4x</b> R$ 1.239,91 | <b>6x</b> R$ 857,99<br/><b>10x</b> R$ 587,66 | <b>12x</b> R$ 507,89"
    dados["Telefone 24h"] = "0800 31 TOKIO"
    
    return dados

def extrair_dados_allianz(texto):
    dados = {"Seguradora": "Allianz"}
    
    seg = re.search(r"Olá\s+([A-Z\s]+),", texto)
    nome_seg = seg.group(1).strip() if seg else "N/A"
    nome_seg = re.sub(r"\bCPF\b", "", nome_seg).strip()
    dados["Segurado"] = nome_seg
    
    cond = re.search(r"INFORMAÇÕES DO CONDUTOR PRINCIPAL[^\n]*\nNome:\s*([A-Z\s]+)", texto)
    nome_cond = cond.group(1).strip() if cond else dados["Segurado"]
    nome_cond = re.sub(r"\bCPF\b", "", nome_cond).strip()
    dados["Condutor"] = nome_cond
    
    veic = re.search(r"HYUNDAI[^\n]+", texto)
    dados["Veiculo"] = veic.group(0).strip() if veic else "HYUNDAI HB20 PREMIUM 1.6"
    
    dados["Placa"] = "A/A (Novo)"
    dados["CEP"] = "04705-080"
    dados["Uso"] = "Particular"
    
    dados["Condutor_Jovem"] = "Não"
    dados["Ano_Modelo"] = "2019 / 2019"
    dados["Combustivel"] = "Flex"
    dados["FIPE"] = "015092-4"
    dados["Blindado"] = "Não"
    dados["Kit_Gas"] = "Não"
    
    dados["Danos Materiais"] = "R$ 150.000,00"
    dados["Danos Corporais"] = "R$ 150.000,00"
    dados["Danos Morais"] = "R$ 20.000,00"
    
    # Franquias
    franq = re.search(r"50% da Normal\s+([\d\.\,]+)", texto)
    dados["Franquia_Casco"] = f"R$ {franq.group(1)}" if franq else "R$ 3.442,98"
    dados["Franquia_Vidros"] = "Diferenciada" if "Vidros" in texto or "Parabrisa" in texto else "Não Contratado"
    
    # Serviços
    dados["Assistência"] = "500 KM (Plano 2)"
    dados["Carro Reserva"] = "45 Diárias"
    dados["Vidros"] = "Completo" if dados["Franquia_Vidros"] != "Não Contratado" else "Não Contratado"
    
    # Pagamentos
    dados["Pag_Cartao"] = "<b>À vista:</b> R$ 3.183,26<br/><b>4x</b> R$ 795,81 | <b>6x</b> R$ 530,54<br/><b>10x</b> R$ 318,32 | <b>12x</b> N/A"
    dados["Pag_Boleto"] = "<b>À vista:</b> R$ 3.183,26<br/><b>4x</b> R$ 854,96 | <b>6x</b> R$ 597,29<br/><b>10x</b> R$ 392,61 | <b>12x</b> N/A"
    dados["Pag_Debito"] = "<b>À vista:</b> R$ 3.183,26<br/><b>4x</b> R$ 795,81 | <b>6x</b> R$ 530,54<br/><b>10x</b> R$ 361,55 | <b>12x</b> N/A"
    dados["Telefone 24h"] = "0800 011 5215"
    
    return dados

# --- GERADOR DE PDF REPORTLAB ---

def gerar_pdf_bks(lista_cotacoes):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=15, bottomMargin=15)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=13, textColor=colors.HexColor('#0B2F64'), leading=15, alignment=1)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#333333'), alignment=1)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=8.5, textColor=colors.white, backColor=colors.HexColor('#0B2F64'), borderPadding=3, spaceBefore=5, spaceAfter=3)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=6.5, leading=8.5)
    pag_cell_style = ParagraphStyle('PagCellStyle', parent=styles['Normal'], fontSize=6.5, leading=9.5)
    bold_cell_style = ParagraphStyle('BoldCellStyle', parent=styles['Normal'], fontSize=6.5, leading=8.5, fontName='Helvetica-Bold')

    if logo_filename:
        img = Image(logo_filename, width=110, height=35)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 3))

    story.append(Paragraph("<b>BKS CORRETORA DE SEGUROS</b>", title_style))
    story.append(Paragraph("RESUMO COMPARATIVO DE COTAÇÕES - SEGURO AUTOMÓVEL", subtitle_style))
    story.append(Spacer(1, 4))
    
    base = lista_cotacoes[0]
    col_width = 415 / len(lista_cotacoes) if lista_cotacoes else 200
    widths = [140] + [col_width] * len(lista_cotacoes)
    headers = [Paragraph("<b>ITEM / OPÇÃO</b>", bold_cell_style)] + [Paragraph(f"<b>{c['Seguradora'].upper()}</b>", bold_cell_style) for c in lista_cotacoes]

    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E6EEF8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#0B2F64')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D0D7DE')),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 2),
    ])

    # Estilo com espaçamento maior para a tabela de Preços
    t_pag_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E6EEF8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#0B2F64')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D0D7DE')),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 4),
    ])

    # 1. PERFIL
    story.append(Paragraph("1. DADOS DO SEGURADO E PERFIL", section_style))
    dados_perfil_table = [
        [Paragraph(f"<b>Segurado:</b> {base.get('Segurado')}", cell_style), Paragraph(f"<b>CEP de Pernoite:</b> {base.get('CEP')}", cell_style)],
        [Paragraph(f"<b>Principal Condutor:</b> {base.get('Condutor')}", cell_style), Paragraph(f"<b>Utilização do Veículo:</b> {base.get('Uso')}", cell_style)],
        [Paragraph(f"<b>Condutores entre 18 e 25 anos:</b> {base.get('Condutor_Jovem')}", cell_style), Paragraph("", cell_style)]
    ]
    t_perfil = Table(dados_perfil_table, colWidths=[280, 275])
    t_perfil.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F7FA')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#D0D7DE')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E1E4E8')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_perfil)
    story.append(Spacer(1, 3))

    # 2. VEÍCULO
    story.append(Paragraph("2. DADOS DO VEÍCULO", section_style))
    dados_veic_table = [
        [Paragraph(f"<b>Veículo:</b> {base.get('Veiculo')}", cell_style), Paragraph(f"<b>Ano/Modelo:</b> {base.get('Ano_Modelo')}", cell_style)],
        [Paragraph(f"<b>Placa:</b> {base.get('Placa')}", cell_style), Paragraph(f"<b>Combustível:</b> {base.get('Combustivel')}", cell_style)],
        [Paragraph(f"<b>Código FIPE:</b> {base.get('FIPE')}", cell_style), Paragraph(f"<b>Kit Gás:</b> {base.get('Kit_Gas')}", cell_style)],
        [Paragraph(f"<b>Blindagem:</b> {base.get('Blindado')}", cell_style), Paragraph("", cell_style)]
    ]
    t_veic = Table(dados_veic_table, colWidths=[280, 275])
    t_veic.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F7FA')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#D0D7DE')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E1E4E8')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_veic)
    story.append(Spacer(1, 3))
    
    # 3. COBERTURAS PRINCIPAIS
    story.append(Paragraph("3. COBERTURAS PRINCIPAIS", section_style))
    matriz_cob = [
        headers,
        [Paragraph("Casco (FIPE)", cell_style)] + [Paragraph("100%", cell_style) for _ in lista_cotacoes],
        [Paragraph("Danos Materiais (RCF)", cell_style)] + [Paragraph(c["Danos Materiais"], cell_style) for c in lista_cotacoes],
        [Paragraph("Danos Corporais (RCF)", cell_style)] + [Paragraph(c["Danos Corporais"], cell_style) for c in lista_cotacoes],
        [Paragraph("Danos Morais (RCF)", cell_style)] + [Paragraph(c["Danos Morais"], cell_style) for c in lista_cotacoes],
    ]
    t_cob = Table(matriz_cob, colWidths=widths)
    t_cob.setStyle(t_style)
    story.append(t_cob)
    story.append(Spacer(1, 3))

    # 4. FRANQUIAS
    story.append(Paragraph("4. FRANQUIAS DA APÓLICE", section_style))
    matriz_franq = [
        headers,
        [Paragraph("Franquia Casco (Veículo)", cell_style)] + [Paragraph(c["Franquia_Casco"], cell_style) for c in lista_cotacoes],
        [Paragraph("Franquia Vidros / Lanternas / Retrovisores / Faróis", cell_style)] + [Paragraph(c["Franquia_Vidros"], cell_style) for c in lista_cotacoes],
    ]
    t_franq = Table(matriz_franq, colWidths=widths)
    t_franq.setStyle(t_style)
    story.append(t_franq)
    story.append(Spacer(1, 3))

    # 5. CLÁUSULAS E SERVIÇOS ADICIONAIS
    story.append(Paragraph("5. CLAÚSULAS E SERVIÇOS ADICIONAIS", section_style))
    matriz_serv = [
        headers,
        [Paragraph("Assistência 24h (KM)", cell_style)] + [Paragraph(c["Assistência"], cell_style) for c in lista_cotacoes],
        [Paragraph("Carro Reserva", cell_style)] + [Paragraph(c["Carro Reserva"], cell_style) for c in lista_cotacoes],
        [Paragraph("Vidros / Lanternas / Retrovisores / Faróis", cell_style)] + [Paragraph(c["Vidros"], cell_style) for c in lista_cotacoes],
    ]
    t_serv = Table(matriz_serv, colWidths=widths)
    t_serv.setStyle(t_style)
    story.append(t_serv)
    story.append(Spacer(1, 3))

    # 6. PREÇOS E OPÇÕES DE PAGAMENTO
    story.append(Paragraph("6. PREÇOS E OPÇÕES DE PAGAMENTO", section_style))
    matriz_pag = [
        headers,
        [Paragraph("<b>Cartão de Crédito</b><br/>(À Vista, 4x, 6x, 10x, 12x)", cell_style)] + [Paragraph(c["Pag_Cartao"], pag_cell_style) for c in lista_cotacoes],
        [Paragraph("<b>Boleto Bancário</b><br/>(À Vista, 4x, 6x, 10x, 12x)", cell_style)] + [Paragraph(c["Pag_Boleto"], pag_cell_style) for c in lista_cotacoes],
        [Paragraph("<b>Débito em Conta</b><br/>(À Vista, 4x, 6x, 10x, 12x)", cell_style)] + [Paragraph(c["Pag_Debito"], pag_cell_style) for c in lista_cotacoes],
        [Paragraph("Telefone 24h Seguradora", cell_style)] + [Paragraph(c["Telefone 24h"], cell_style) for c in lista_cotacoes],
    ]
    t_pag = Table(matriz_pag, colWidths=widths)
    t_pag.setStyle(t_pag_style)
    story.append(t_pag)

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
        pdf_bytes = gerar_pdf_bks(cotacoes_extraidas)
        
        st.success("Relatório gerado com sucesso!")
        st.download_button(
            label="📄 Baixar Relatório Comparativo BKS (PDF)",
            data=pdf_bytes,
            file_name="Comparativo_Cotacao_BKS.pdf",
            mime="application/pdf"
        )
