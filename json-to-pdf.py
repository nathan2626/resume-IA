import json
from fpdf import FPDF

# Charger le fichier JSON
with open('summaries/ALK_summary.json', 'r', encoding='utf-8') as f:
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
        self.set_text_color(0, 51, 102)  # Bleu foncé
        self.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT', align='L')
        self.set_text_color(0, 0, 0)  # Noir
        self.ln(2)

    def sub_chapter_title(self, subtitle):
        self.set_font('DejaVu', 'I', 10)
        self.set_text_color(0, 102, 204)  # Bleu
        self.cell(0, 8, subtitle, new_x='LMARGIN', new_y='NEXT', align='L')
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def clean_body(self, body):
        body = body.replace("**", "")  # Enlever les ** autour des mots
        body = body.replace(" *", "-")  # Transformer * en tirets
        body = body.replace("- ", "• ")  # Transformer - en puces
        return body

    def chapter_body(self, body):
        self.set_font('DejaVu', '', 8)
        body = self.clean_body(body)
        self.multi_cell(0, 8, body)
        self.ln(3)

    def replace_emojis(self, text):
        replacements = {
            '📊': '[Statistiques]',
            '⚠️': '[Problèmes critiques]',
            '🧠': '[Solutions]',
            '🔧': '[Améliorations]',
            '🚨': '[Risques]',
            '🎯': '[Objectif]',
            '🔍': '[Recherche]',
        }
        for emoji, replacement in replacements.items():
            text = text.replace(emoji, replacement)
        return text

    def add_section(self, title, content):
        title = self.replace_emojis(title)
        self.chapter_title(title)
        subsections = content.split('### ')
        for section in subsections:
            lines = section.split('\n')
            if len(lines) > 1:
                self.sub_chapter_title(lines[0].strip())
                self.chapter_body('\n'.join(lines[1:]).strip())
            else:
                self.chapter_body(section.strip())

# Diviser le résumé en sections sur les balises ---
sections = summary.split('---')

pdf = PDF()
pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf')
pdf.add_font('DejaVu', 'B', 'fonts/DejaVuSans-Bold.ttf')
pdf.add_font('DejaVu', 'I', 'fonts/DejaVuSans-Oblique.ttf')

pdf.add_page()

# Ajouter chaque section au PDF
for section in sections:
    lines = section.strip().split('\n')
    if lines:
        title = lines[0].strip() if lines[0].startswith('📊') or lines[0].startswith('⚠️') or lines[0].startswith('🧠') or lines[0].startswith('🔧') or lines[0].startswith('🚨') else 'Section'
        content = '\n'.join(lines[1:]).strip()
        pdf.add_section(title, content)

# Enregistrer le PDF
pdf.output(f'Rapport_{company}.pdf')
print(f"Rapport généré : Rapport_{company}.pdf")
