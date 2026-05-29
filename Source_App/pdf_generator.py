import os
from fpdf import FPDF
from datetime import datetime

class CAPAPDF(FPDF):
    def header(self):
        # Logo ARC-CSU
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 30)
        self.set_font("helvetica", "B", 14)
        self.cell(40)
        self.cell(110, 10, "Plan d'Actions Correctives (CAPA) - ARC-CSU", align="C")
        self.ln(8)
        self.set_font("helvetica", "I", 10)
        self.cell(40)
        self.cell(110, 10, "Rapport Officiel d'Evaluation EPVG", align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} - Genere le {datetime.now().strftime('%d/%m/%Y')}", align="C")

def generate_capa_pdf(etablissement: str, score_total: float, niveau: str, failed_rubriques: list) -> bytearray:
    """
    Génère un PDF avec le logo de l'ARC-CSU détaillant les rubriques échouées (< 60%).
    Retourne un bytearray prêt à être téléchargé par Streamlit.
    """
    pdf = CAPAPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Info Etablissement
    pdf.set_font("helvetica", "B", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f" Etablissement : {etablissement}", ln=1, fill=True)
    pdf.cell(0, 10, f" Score Global : {score_total}% (Niveau {niveau})", ln=1, fill=True)
    pdf.ln(8)
    
    # Section 1
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "1. Constatations des Ecarts (Rubriques < 60%)", ln=1)
    
    pdf.set_font("helvetica", "", 11)
    if not failed_rubriques:
        pdf.cell(0, 10, "Aucun ecart majeur constate. L'etablissement respecte les BPSD.", ln=1)
    else:
        for r in failed_rubriques:
            pdf.set_text_color(200, 0, 0) # Red
            text = f"- {r['label']} (Score: {r['score']}%)"
            pdf.multi_cell(0, 8, text)
            
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Section 2
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "2. Actions Correctives et Preventives (CAPA) Exigees", ln=1)
        pdf.set_font("helvetica", "", 11)
        
        msg = (
            "Il est exige de l'etablissement de mettre en place un plan d'actions correctives "
            "pour les rubriques mentionnees ci-dessus dans un delai de 3 mois. Une contre-visite "
            "de l'ARC-CSU pourra etre diligentee pour verifier la mise en conformite."
        )
        pdf.multi_cell(0, 8, msg)
        
        pdf.ln(20)
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(0, 10, "Signature de l'Inspecteur / Jury : ___________________________", align="R", ln=1)
        
    return pdf.output()
