"""Erzeugt den Enterprise-One-Pager (2 Seiten) als PDF. Einmalig genutzt."""
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ACCENT = colors.HexColor("#6d5cff")
ACCENT2 = colors.HexColor("#ff8c2a")
INK = colors.HexColor("#14162a")
MUTED = colors.HexColor("#5b6072")
BG = colors.HexColor("#f2f2f8")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Title"], textColor=INK, fontSize=24, leading=27, spaceAfter=2)
KICKER = ParagraphStyle("K", parent=styles["Normal"], textColor=ACCENT, fontSize=10, leading=12,
                        spaceAfter=6, alignment=TA_LEFT, fontName="Helvetica-Bold")
SUB = ParagraphStyle("SUB", parent=styles["Normal"], textColor=MUTED, fontSize=12, leading=17, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=INK, fontSize=13, leading=16, spaceBefore=8, spaceAfter=4)
BODY = ParagraphStyle("BODY", parent=styles["Normal"], textColor=INK, fontSize=10, leading=14)
SMALL = ParagraphStyle("SM", parent=styles["Normal"], textColor=MUTED, fontSize=8.5, leading=11)
CARDT = ParagraphStyle("CT", parent=styles["Normal"], textColor=INK, fontSize=11, leading=13, fontName="Helvetica-Bold")
CARDB = ParagraphStyle("CB", parent=styles["Normal"], textColor=MUTED, fontSize=9, leading=12)
MARK = ParagraphStyle("MK", parent=styles["Normal"], textColor=ACCENT, fontSize=8, leading=10, fontName="Helvetica-Bold")


def card(title, mark, body):
    inner = [Paragraph(mark, MARK), Spacer(1, 3), Paragraph(title, CARDT), Spacer(1, 3), Paragraph(body, CARDB)]
    t = Table([[inner]], colWidths=[85 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e3e3ee")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    return t


BEWEISE = [
    ("Ihre Daten verlassen das Haus nicht", "LOCAL_ONLY-ROUTING",
     "Datenklasse «nur lokal» bindet die Verarbeitung hart an Ihre Infrastruktur - kein Dokument geht in eine fremde Cloud."),
    ("Kunde A sieht nie Daten von Kunde B", "RLS - DB-EBENE",
     "Mandantentrennung per Postgres Row-Level-Security. Selbst bei einem Code-Fehler liefert die Datenbank keine fremden Zeilen."),
    ("Echte KI im eigenen Rechenzentrum", "LOKALE INFERENZ",
     "Eigene, lokale Modelle (Ollama/vLLM) über einen Modell-Router. Cloud nur, wenn Sie es erlauben. Kein Anbieter-Lock-in."),
    ("Sicherer Zugang, klare Rechte", "AUTH - RBAC - AUDIT",
     "Anbindung an Ihr Firmen-Login (Keycloak/SSO), Rollen mit Default-Deny und ein lückenloses, unveränderliches Audit-Log."),
    ("Betreibbar und nachvollziehbar", "OBSERVABILITY",
     "Metriken (Prometheus), Health-/Readiness-Prüfungen, Backup/Restore und fertige Kubernetes-Manifeste - für 24/7-Betrieb."),
    ("In Tagen startklar, nicht Monaten", "CUTOVER",
     "Stufenweiser, jederzeit umkehrbarer Rollout per Feature-Flags. Demo -> Pilot in einer Abteilung -> voller Betrieb."),
]


def build():
    doc = SimpleDocTemplate(
        "/home/user/Nate/docs/Enterprise-OnePager.pdf", pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
        title="AI Command Center - Enterprise / On-Premise-KI",
    )
    s = []
    s.append(Paragraph("AI COMMAND CENTER - ENTERPRISE", KICKER))
    s.append(Paragraph("Ihre KI-Abteilung - im eigenen Haus.", H1))
    s.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=6, spaceAfter=10))
    s.append(Paragraph(
        "Datenhoheit, Mandantentrennung und Nachvollziehbarkeit - ohne dass ein einziges Dokument Ihr "
        "Netz verlässt. Für Gesundheit, Recht, Finanzen, Industrie und die öffentliche Hand.", SUB))

    rows, row = [], []
    for i, (t, m, b) in enumerate(BEWEISE):
        row.append(card(t, m, b))
        if len(row) == 2:
            rows.append(row); row = []
    grid = Table(rows, colWidths=[87 * mm, 87 * mm], hAlign="CENTER")
    grid.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    s.append(grid)
    s.append(Spacer(1, 10))
    s.append(Paragraph(
        "<b>Jedes Leistungsversprechen ist durch ausführbare Tests gedeckt - nicht bloss behauptet.</b>", BODY))

    # Seite 2
    from reportlab.platypus import PageBreak
    s.append(PageBreak())
    s.append(Paragraph("SO KOMMEN SIE AN", KICKER))
    s.append(Paragraph("Angebot & Ablauf", H1))
    s.append(HRFlowable(width="100%", thickness=2, color=ACCENT2, spaceBefore=6, spaceAfter=10))

    s.append(Paragraph("Für wen", H2))
    s.append(Paragraph(
        "Mittelstand und Konzerne in regulierten oder datensensiblen Branchen im DACH-Raum, die KI wollen, "
        "aber ihre Daten nicht in fremde Clouds geben dürfen oder wollen.", BODY))

    s.append(Paragraph("Bausteine", H2))
    tbl = Table([
        [Paragraph("<b>Enterprise Cloud</b>", BODY), Paragraph("Gehostet, jeder Mandant isoliert. Ab CHF 790/Monat.", BODY)],
        [Paragraph("<b>On-Premise / Private</b>", BODY), Paragraph("Installation im Kundennetz (Docker/k3s), SSO-Anbindung, eigene Modelle. Projektpreis.", BODY)],
        [Paragraph("<b>Add-ons</b>", BODY), Paragraph("ERP/CRM-Integration, dedizierte GPU, Compliance-/Audit-Export.", BODY)],
    ], colWidths=[45 * mm, 129 * mm])
    tbl.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e3e3ee")),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    s.append(tbl)

    s.append(Paragraph("In vier Schritten", H2))
    for i, step in enumerate([
        "Demo: das Live-Dashboard mit echten Kennzahlen aus Ihrer Umgebung.",
        "Pilot: eine Abteilung im Kundennetz, echte Daten, echte Modelle.",
        "Rollout: stufenweise per Feature-Flags - jederzeit umkehrbar.",
        "Betrieb: SLA, Monitoring, Backup, Schulung - alles inklusive.",
    ], 1):
        s.append(Paragraph(f"<b>{i}.</b>&nbsp;&nbsp;{step}", BODY))
        s.append(Spacer(1, 3))

    s.append(Spacer(1, 12))
    cta = Table([[Paragraph("<b>Kontakt aufnehmen &nbsp;-&nbsp; Pilot in Ihrer Abteilung in Tagen, nicht Monaten.</b>",
                            ParagraphStyle("cta", parent=BODY, textColor=colors.white, fontSize=11))]],
                colWidths=[174 * mm])
    cta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("ROUNDEDCORNERS", [8, 8, 8, 8]),
    ]))
    s.append(cta)
    s.append(Spacer(1, 8))
    s.append(Paragraph(
        "AI Command Center - ZEHNTAGE. Technische Nachweise: VERIFIKATION-LIVE-DIENSTE, SECURITY-REVIEW, CUTOVER.", SMALL))

    doc.build(s)
    print("PDF geschrieben: /home/user/Nate/docs/Enterprise-OnePager.pdf")


build()
