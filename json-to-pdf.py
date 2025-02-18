import json
from fpdf import FPDF
from bs4 import BeautifulSoup

# Charger le fichier JSON
with open('summaries/Novo_nordisk_summary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

company = data.get('company', 'Inconnue')
summary = data.get('summary', '')

# Créer un document PDF avec une meilleure mise en page
class PDF(FPDF):
    def header(self):
        self.set_font('DejaVu', 'B', 14)
        self.cell(0, 10, f"Rapport d'Analyse des Tickets - {company}", new_x='LMARGIN', new_y='NEXT', align='C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('DejaVu', 'B', 12)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT', align='L')
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def sub_chapter_title(self, subtitle):
        self.set_font('DejaVu', 'I', 10)
        self.set_text_color(0, 102, 204)
        self.cell(0, 8, subtitle, new_x='LMARGIN', new_y='NEXT', align='L')
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('DejaVu', '', 8)
        self.multi_cell(0, 6, body)
        self.ln(2)

    def clean_text(self, text):
        """Nettoyer et adapter le contenu HTML en texte brut."""
        text = text.replace("•", "-")  # Puces en tirets
        text = text.replace("\xa0", " ")  # Supprimer les espaces insécables
        text = text.replace("&nbsp;", " ")
        return text

    def add_html_content(self, html_content):
        """Parse le contenu HTML et l'ajoute au PDF."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Parcourir les éléments HTML et les ajouter au PDF
        for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'li']):
            if tag.name == 'h1':
                self.chapter_title(f"📘 {tag.get_text(strip=True)}")
            elif tag.name == 'h2':
                self.sub_chapter_title(f"🔹 {tag.get_text(strip=True)}")
            elif tag.name == 'h3':
                self.sub_chapter_title(f"➡️ {tag.get_text(strip=True)}")
            elif tag.name == 'p':
                self.chapter_body(self.clean_text(tag.get_text(strip=True)))
            elif tag.name == 'ul':
                for li in tag.find_all('li'):
                    self.chapter_body(f"• {self.clean_text(li.get_text(strip=True))}")
            elif tag.name == 'ol':
                count = 1
                for li in tag.find_all('li'):
                    self.chapter_body(f"{count}. {self.clean_text(li.get_text(strip=True))}")
                    count += 1

# Initialisation du PDF
pdf = PDF()
pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf', uni=True)
pdf.add_font('DejaVu', 'B', 'fonts/DejaVuSans-Bold.ttf', uni=True)
pdf.add_font('DejaVu', 'I', 'fonts/DejaVuSans-Oblique.ttf', uni=True)
pdf.add_page()

# Ajouter le contenu HTML converti en texte
pdf.add_html_content(summary)

# Enregistrer le PDF
pdf.output(f'Rapport_{company}.pdf')
print(f"📄 Rapport généré : Rapport_{company}.pdf")
