import streamlit as st
import math
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
#from fpdf import FPDF # usa fpdf2
#from io import BytesIO
import datetime

st.set_page_config(
    page_title="Calculadora de Índices Financeiros",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def safe_div(numerador, denominador):
    """Divisão segura — retorna None se o denominador for zero."""
    if denominador is None or numerador is None:
        return None
    if denominador == 0:
        return None
    return numerador / denominador

def fmt(valor, casas=4, pct=False):
    """Formata um número para exibição."""
    if valor is None:
        return "—"
    if pct:
        return f"{valor * 100:.2f}%"
    return f"{valor:.{casas}f}"

# ─────────────────────────────────────────────
#  Cabeçalho
# ─────────────────────────────────────────────

st.title("📊 Calculadora de Índices Financeiros")
st.markdown(
    "Preencha os dados financeiros na barra lateral e visualize os índices calculados automaticamente. "
    "Ao final, exporte um **Relatório PDF** completo."
)
st.divider()

# ─────────────────────────────────────────────
#  Sidebar — entradas
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("📋 Dados de Entrada")
    st.caption("Valores monetários na mesma moeda / unidade.")

    with st.expander("📂 Balanço Patrimonial", expanded=True):
        AC   = st.number_input("AC – Ativo Circulante",           value=0.0, format="%.2f")
        PC   = st.number_input("PC – Passivo Circulante",         value=0.0, format="%.2f")
        RLP  = st.number_input("RLP – Realizável a Longo Prazo",  value=0.0, format="%.2f")
        ELP  = st.number_input("ELP – Exigível a Longo Prazo",    value=0.0, format="%.2f")
        AT   = st.number_input("AT – Ativo Total",                value=0.0, format="%.2f")
        PL   = st.number_input("PL – Patrimônio Líquido",         value=0.0, format="%.2f")
        ESTQ = st.number_input("ESTQ – Estoques",                  value=0.0, format="%.2f")
        DISP = st.number_input("DISP – Disponível",               value=0.0, format="%.2f")
        DupRec  = st.number_input("DupRec – Duplicatas a Receber",    value=0.0, format="%.2f")
        DupDesc = st.number_input("DupDesc – Duplicatas Descontadas", value=0.0, format="%.2f")
        Imob = st.number_input("Imob – Imobilizado",              value=0.0, format="%.2f")
        F    = st.number_input("F – Fornecedores",                value=0.0, format="%.2f")
        BCM  = st.number_input("BCM – Banco Conta Movimento",     value=0.0, format="%.2f")
        EB   = st.number_input("EB – Empréstimos Bancários",      value=0.0, format="%.2f")
        Fin  = st.number_input("Fin – Financiamentos",            value=0.0, format="%.2f")

    with st.expander("📂 Demonstração de Resultados (DRE)", expanded=False):
        VB   = st.number_input("VB – Vendas Brutas",              value=0.0, format="%.2f")
        C    = st.number_input("C – Compras",                     value=0.0, format="%.2f")
        CV   = st.number_input("CV – Custo das Vendas",           value=0.0, format="%.2f")
        LL   = st.number_input("LL – Lucro Líquido",              value=0.0, format="%.2f")
        Div  = st.number_input("Div – Dividendos",                value=0.0, format="%.2f")
        Imp  = st.number_input("Imp – Impostos",                  value=0.0, format="%.2f")
        LuRin = st.number_input("LuRin – Lucro Reinvestido",      value=0.0, format="%.2f")
        Juros = st.number_input("Juros – Juros (DRE)",            value=0.0, format="%.2f")

    with st.expander("📂 Demonstração de Fluxo de Caixa (DFC)", expanded=False):
        CGOP      = st.number_input("CGOP – Caixa Gerado nas Operações",                        value=0.0, format="%.2f")
        CGOPAOF   = st.number_input("CGOPAOF – Caixa Gerado nas Op. Após Op. Financeiras",      value=0.0, format="%.2f")
        JPP       = st.number_input("JPP – Juros Pagos no Período",                             value=0.0, format="%.2f")
        CGV       = st.number_input("CGV – Caixa Gerado nas Vendas",                            value=0.0, format="%.2f")
        RV        = st.number_input("RV – Receita com Vendas",                                  value=0.0, format="%.2f")
        NII       = st.number_input("NII – Novos Investimentos no Imobilizado",                 value=0.0, format="%.2f")
        Fino      = st.number_input("Fino – Financiamentos Onerosos",                           value=0.0, format="%.2f")

    with st.expander("📂 Valor Adicionado (DVA)", expanded=False):
        VAD   = st.number_input("VAD – Valor Adicionado",         value=0.0, format="%.2f")
        RT    = st.number_input("RT – Receita Total",             value=0.0, format="%.2f")
        NFunc = st.number_input("NFunc – Nº de Funcionários (média)", value=0.0, step=1.0, format="%.0f")

    with st.expander("📂 Dados do Investidor", expanded=False):
        NACS = st.number_input("NACS – Nº de Ações do Capital Social", value=0.0, format="%.2f")
        VA_v = st.number_input("VA – Valor da Ação",              value=0.0, format="%.2f")

# ─────────────────────────────────────────────
#  Cálculos intermediários
# ─────────────────────────────────────────────

PExig = PC + ELP  # Passivo Exigível

# ── Liquidez ──────────────────────────────────
LC = safe_div(AC, PC)
LS = safe_div(AC - ESTQ, PC)
LG = safe_div(AC + RLP, PExig)
LI = safe_div(DISP, PC)

# ── Endividamento ─────────────────────────────
PCT  = safe_div(PExig, PExig + PL)
GCPaoCT = safe_div(PL, PExig)
CE   = safe_div(PC, PExig)

# ── Prazos ────────────────────────────────────
PMRV = safe_div(360 * DupRec, VB)
PMPC = safe_div(360 * F,      C)
PMRE = safe_div(360 * ESTQ,   CV)
if PMRV is not None and PMRE is not None and PMPC is not None:
    PA = safe_div(PMRE + PMRV, PMPC)
else:
    PA = None

# ── Investimentos e Retornos ──────────────────
ROI  = safe_div(LL, AT)
ROE  = safe_div(LL, PL)

# ── Investidor ────────────────────────────────
VPA  = safe_div(PL,  NACS)
LLA  = safe_div(LL,  NACS)
IPL_inv = safe_div(VA_v, LLA)   # IP/L
DACS = safe_div(Div, NACS)

# ── Estrutura de Capital ──────────────────────
IPL  = safe_div(Imob, PL)
IRLPePL = safe_div(Imob, ELP + PL)
PCTRP = safe_div(PExig, PL)

# ── Bancos ────────────────────────────────────
IDD  = safe_div(DupDesc, DupRec)
RB   = safe_div(BCM, DupDesc + EB)
PRB  = safe_div(DupDesc + EB + Fin, PExig)

# ── DFC ───────────────────────────────────────
CJ   = safe_div(CGOP, JPP)
CQD  = safe_div(CGOPAOF, Fino)
TRC  = safe_div(CGOP, AT)
NRV  = safe_div(CGV, RV)
CNI  = safe_div(CGOPAOF, NII)

# ── Valor Adicionado ──────────────────────────
PGRA  = safe_div(VAD, AT)
RR    = safe_div(VAD, RT)
VADPC = safe_div(VAD, NFunc)

# ── Participações do VAD ──────────────────────
part_emp  = safe_div(NFunc, VAD)   # conforme arquivo: NFunc / VAD  (revisão: pode ser Remuneração/VAD)
part_jur  = safe_div(Juros, VAD)
part_div  = safe_div(Div,   VAD)
part_imp  = safe_div(Imp,   VAD)
part_luri = safe_div(LuRin, VAD)

# ─────────────────────────────────────────────
#  Estrutura de resultados para exibição e PDF
# ─────────────────────────────────────────────

RESULTADOS = [
    {
        "titulo": "LIQUIDEZ",
        "indices": [
            ("LC",  "Liquidez Corrente",               "AC / PC",                                         LC),
            ("LS",  "Liquidez Seca",                   "(AC − ESTQ) / PC",                               LS),
            ("LG",  "Liquidez Geral",                  "(AC + RLP) / PExig",                             LG),
            ("LI",  "Liquidez Imediata",               "DISP / PC",                                       LI),
        ],
    },
    {
        "titulo": "ENDIVIDAMENTO",
        "indices": [
            ("PCT",      "Participação de Capitais de Terceiros",              "PExig / (PExig + PL)",    PCT),
            ("GCPaoCT",  "Garantia do Capital Próprio ao Capital de Terceiros","PL / PExig",              GCPaoCT),
            ("CE",       "Composição de Endividamento",                        "PC / PExig",              CE),
        ],
    },
    {
        "titulo": "PRAZOS DE VENDAS, RECEBIMENTOS E PAGAMENTOS",
        "indices": [
            ("PMRV", "Prazo Médio de Recebimento de Vendas",    "(360 × DupRec) / VB",     PMRV),
            ("PMPC", "Prazo Médio de Pagamento de Compras",     "(360 × F) / C",           PMPC),
            ("PMRE", "Prazo Médio de Renovação de Estoques",    "(360 × ESTQ) / CV",       PMRE),
            ("PA",   "Posicionamento de Atividade (PA/PR)",     "(PMRE + PMRV) / PMPC",    PA),
        ],
    },
    {
        "titulo": "INVESTIMENTOS E RETORNOS",
        "indices": [
            ("ROI / TRI", "Retorno Sobre Investimentos",         "LL / AT",  ROI),
            ("ROE / TRPL","Retorno Sobre Capital Investido / PL","LL / PL",  ROE),
        ],
    },
    {
        "titulo": "AVALIAÇÕES DO INVESTIDOR",
        "indices": [
            ("VPA",  "Valor Patrimonial da Ação",        "PL / NACS",   VPA),
            ("LLA",  "Lucro Líquido por Ação",           "LL / NACS",   LLA),
            ("IP/L", "Índice Preço/Lucro",               "VA / LLA",    IPL_inv),
            ("DACS", "Dividendos por Ação",              "Div / NACS",  DACS),
        ],
    },
    {
        "titulo": "ESTRUTURA DE CAPITAL",
        "indices": [
            ("IPL",     "Imobilizado do PL",                                  "Imob / PL",          IPL),
            ("IRLPePL", "Imobilização dos Recursos de LP e do PL",            "Imob / (ELP + PL)",  IRLPePL),
            ("PCTRP",   "Participação de Capital de Terceiros / Rec. Próprios","PExig / PL",         PCTRP),
        ],
    },
    {
        "titulo": "AVALIAÇÕES DOS BANCOS",
        "indices": [
            ("IDD", "Índice de Desconto de Duplicatas",               "DupDesc / DupRec",              IDD),
            ("RB",  "Reciprocidade Bancária",                         "BCM / (DupDesc + EB)",          RB),
            ("PRB", "Participação dos Recursos Bancários / CT",       "(DupDesc + EB + Fin) / PExig",  PRB),
        ],
    },
    {
        "titulo": "ÍNDICES DA DFC",
        "indices": [
            ("CJ",  "Cobertura de Juros",               "CGOP / JPP",       CJ),
            ("CQD", "Capacidade de Quitar Dívidas",     "CGOPAOF / Fino",   CQD),
            ("TRC", "Taxa de Retorno do Caixa",         "CGOP / AT",        TRC),
            ("NRV", "Nível de Recebimento das Vendas",  "CGV / RV",         NRV),
            ("CNI", "Capacidade de Novos Investimentos","CGOPAOF / NII",    CNI),
        ],
    },
    {
        "titulo": "ANÁLISES DO VALOR ADICIONADO",
        "indices": [
            ("PGRA",  "Potencial de Gerar Riqueza do Ativo", "VAD / AT",    PGRA),
            ("RR",    "Retenção da Receita",                 "VAD / RT",    RR),
            ("VADPC", "Valor Adicionado per Capita",         "VAD / NFunc", VADPC),
        ],
    },
    {
        "titulo": "PARTICIPAÇÕES DO VALOR ADICIONADO",
        "indices": [
            ("Empregados",       "Empregados / VAD",        "NFunc / VAD",  part_emp),
            ("JurosPagos",       "Juros / VAD",             "Juros / VAD",  part_jur),
            ("Dividendos",       "Dividendos / VAD",        "Div / VAD",    part_div),
            ("Impostos",         "Impostos / VAD",          "Imp / VAD",    part_imp),
            ("LucroReinvestido", "Lucro Reinvestido / VAD", "LuRin / VAD",  part_luri),
        ],
    },
]

# ─────────────────────────────────────────────
#  Exibição no Streamlit
# ─────────────────────────────────────────────

for grupo in RESULTADOS:
    st.subheader(grupo["titulo"])
    colunas = st.columns(len(grupo["indices"]) if len(grupo["indices"]) <= 4 else 4)
    for i, (sigla, nome, formula, valor) in enumerate(grupo["indices"]):
        col = colunas[i % 4]
        with col:
            display = fmt(valor) if valor is not None else "—"
            st.metric(label=f"{sigla}", value=display, help=f"**{nome}**\n\n`{formula}`")
    st.caption(" · ".join([f"**{s}** = {fmt(v)}" for s, n, f, v in grupo["indices"]]))
    st.divider()

# ─────────────────────────────────────────────
#  Geração de PDF
# ─────────────────────────────────────────────

def gerar_pdf(resultados, dados_entrada):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    estilos = getSampleStyleSheet()

    # Estilos customizados
    titulo_doc = ParagraphStyle(
        "TituloDoc",
        parent=estilos["Title"],
        fontSize=16,
        textColor=colors.HexColor("#1a3a6b"),
        spaceAfter=4,
    )
    subtitulo_doc = ParagraphStyle(
        "SubtituloDoc",
        parent=estilos["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    secao = ParagraphStyle(
        "Secao",
        parent=estilos["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#1a3a6b"),
        spaceAfter=4,
        spaceBefore=10,
        fontName="Helvetica-Bold",
    )
    rodape_txt = ParagraphStyle(
        "Rodape",
        parent=estilos["Normal"],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )

    story = []

    # ── Cabeçalho ──
    story.append(Paragraph("Relatório de Índices Financeiros", titulo_doc))
    story.append(Paragraph(
        f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
        subtitulo_doc,
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a3a6b")))
    story.append(Spacer(1, 0.4*cm))

    # ── Dados de Entrada ──
    story.append(Paragraph("Dados de Entrada", secao))

    entradas = [
        ["Variável", "Descrição", "Valor"],
        ["AC",       "Ativo Circulante",              f"{dados_entrada['AC']:,.2f}"],
        ["PC",       "Passivo Circulante",            f"{dados_entrada['PC']:,.2f}"],
        ["RLP",      "Realizável a Longo Prazo",      f"{dados_entrada['RLP']:,.2f}"],
        ["ELP",      "Exigível a Longo Prazo",        f"{dados_entrada['ELP']:,.2f}"],
        ["AT",       "Ativo Total",                   f"{dados_entrada['AT']:,.2f}"],
        ["PL",       "Patrimônio Líquido",            f"{dados_entrada['PL']:,.2f}"],
        ["PExig",    "Passivo Exigível (PC + ELP)",   f"{dados_entrada['PExig']:,.2f}"],
        ["ESTQ",     "Estoques",                      f"{dados_entrada['ESTQ']:,.2f}"],
        ["DISP",     "Disponível",                    f"{dados_entrada['DISP']:,.2f}"],
        ["DupRec",   "Duplicatas a Receber",          f"{dados_entrada['DupRec']:,.2f}"],
        ["DupDesc",  "Duplicatas Descontadas",        f"{dados_entrada['DupDesc']:,.2f}"],
        ["Imob",     "Imobilizado",                   f"{dados_entrada['Imob']:,.2f}"],
        ["F",        "Fornecedores",                  f"{dados_entrada['F']:,.2f}"],
        ["BCM",      "Banco Conta Movimento",         f"{dados_entrada['BCM']:,.2f}"],
        ["EB",       "Empréstimos Bancários",         f"{dados_entrada['EB']:,.2f}"],
        ["Fin",      "Financiamentos",                f"{dados_entrada['Fin']:,.2f}"],
        ["VB",       "Vendas Brutas",                 f"{dados_entrada['VB']:,.2f}"],
        ["C",        "Compras",                       f"{dados_entrada['C']:,.2f}"],
        ["CV",       "Custo das Vendas",              f"{dados_entrada['CV']:,.2f}"],
        ["LL",       "Lucro Líquido",                 f"{dados_entrada['LL']:,.2f}"],
        ["Div",      "Dividendos",                    f"{dados_entrada['Div']:,.2f}"],
        ["Imp",      "Impostos",                      f"{dados_entrada['Imp']:,.2f}"],
        ["LuRin",    "Lucro Reinvestido",             f"{dados_entrada['LuRin']:,.2f}"],
        ["Juros",    "Juros (DRE)",                   f"{dados_entrada['Juros']:,.2f}"],
        ["CGOP",     "Caixa Gerado nas Operações",    f"{dados_entrada['CGOP']:,.2f}"],
        ["CGOPAOF",  "CGOP Após Op. Financeiras",     f"{dados_entrada['CGOPAOF']:,.2f}"],
        ["JPP",      "Juros Pagos no Período",        f"{dados_entrada['JPP']:,.2f}"],
        ["CGV",      "Caixa Gerado nas Vendas",       f"{dados_entrada['CGV']:,.2f}"],
        ["RV",       "Receita com Vendas",            f"{dados_entrada['RV']:,.2f}"],
        ["NII",      "Novos Investimentos Imob.",     f"{dados_entrada['NII']:,.2f}"],
        ["Fino",     "Financiamentos Onerosos",       f"{dados_entrada['Fino']:,.2f}"],
        ["VAD",      "Valor Adicionado",              f"{dados_entrada['VAD']:,.2f}"],
        ["RT",       "Receita Total",                 f"{dados_entrada['RT']:,.2f}"],
        ["NFunc",    "Nº de Funcionários (média)",    f"{dados_entrada['NFunc']:,.0f}"],
        ["NACS",     "Nº de Ações",                   f"{dados_entrada['NACS']:,.2f}"],
        ["VA",       "Valor da Ação",                 f"{dados_entrada['VA_v']:,.2f}"],
    ]

    ts_ent = TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#1a3a6b")),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f8")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#c0c8d8")),
        ("ALIGN",       (2, 0), (2, -1),  "RIGHT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ])

    t_ent = Table(entradas, colWidths=[2.2*cm, 9.5*cm, 4*cm])
    t_ent.setStyle(ts_ent)
    story.append(t_ent)
    story.append(Spacer(1, 0.4*cm))

    # ── Seções de índices ──
    for grupo in resultados:
        story.append(Paragraph(grupo["titulo"], secao))

        dados_tabela = [["Sigla", "Nome do Índice", "Fórmula", "Resultado"]]
        for sigla, nome, formula, valor in grupo["indices"]:
            display = fmt(valor) if valor is not None else "—"
            dados_tabela.append([sigla, nome, formula, display])

        ts = TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#1a3a6b")),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f8")]),
            ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#c0c8d8")),
            ("ALIGN",       (3, 0), (3, -1),  "RIGHT"),
            ("FONTNAME",    (3, 1), (3, -1),  "Helvetica-Bold"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ])

        tabela = Table(dados_tabela, colWidths=[2.5*cm, 7*cm, 4.5*cm, 2.5*cm])
        tabela.setStyle(ts)
        story.append(tabela)
        story.append(Spacer(1, 0.3*cm))

    # ── Rodapé ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Relatório gerado pela Calculadora de Índices Financeiros · Os cálculos são baseados nos dados informados pelo usuário.",
        rodape_txt,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
#  Botão de download do PDF
# ─────────────────────────────────────────────

st.subheader("📄 Relatório PDF")

dados_entrada_dict = {
    "AC": AC, "PC": PC, "RLP": RLP, "ELP": ELP, "AT": AT, "PL": PL,
    "PExig": PExig, "ESTQ": ESTQ, "DISP": DISP, "DupRec": DupRec,
    "DupDesc": DupDesc, "Imob": Imob, "F": F, "BCM": BCM, "EB": EB,
    "Fin": Fin, "VB": VB, "C": C, "CV": CV, "LL": LL, "Div": Div,
    "Imp": Imp, "LuRin": LuRin, "Juros": Juros, "CGOP": CGOP,
    "CGOPAOF": CGOPAOF, "JPP": JPP, "CGV": CGV, "RV": RV, "NII": NII,
    "Fino": Fino, "VAD": VAD, "RT": RT, "NFunc": NFunc, "NACS": NACS,
    "VA_v": VA_v,
}

pdf_bytes = gerar_pdf(RESULTADOS, dados_entrada_dict)
nome_arquivo = f"indices_financeiros_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

st.download_button(
    label="⬇️ Baixar Relatório PDF",
    data=pdf_bytes,
    file_name=nome_arquivo,
    mime="application/pdf",
    type="primary",
    use_container_width=True,
)

st.caption("O relatório PDF contém todos os dados de entrada e os índices calculados.")

# ─────────────────────────────────────────────
#  Download do código-fonte
# ─────────────────────────────────────────────

st.subheader("💾 Código-Fonte")

with open(__file__, "r", encoding="utf-8") as f:
    codigo = f.read()

st.download_button(
    label="⬇️ Baixar app.py (código completo)",
    data=codigo,
    file_name="app.py",
    mime="text/plain",
    use_container_width=True,
)

st.caption(
    "Requisitos para execução local: `pip install streamlit reportlab`  →  `streamlit run app.py`"
)
