import markdown2
import pdfkit
import os

# 📂 Configuration de wkhtmltopdf
pdfkit_config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

# 🖹 Lecture du fichier markdown
input_file = "/summaries/ALK_summary.txt"
output_pdf = "Rapport_Analyse_IT.pdf"

if not os.path.exists(input_file):
    print(f"❌ Fichier introuvable : {input_file}")
    exit()

with open(input_file, "r", encoding="utf-8") as f:
    markdown_content = f.read()

# 🖼️ Conversion Markdown → HTML
html_content = markdown2.markdown(markdown_content)

# 🎨 Insertion d'un style CSS
styled_html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport d'Analyse IT</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 20px;
        }}
        h1, h2, h3 {{
            color: #1F618D;
            border-bottom: 2px solid #1F618D;
            padding-bottom: 5px;
            margin-top: 25px;
        }}
        h4 {{
            color: #117A65;
            margin-top: 15px;
        }}
        ul {{
            margin: 15px 0;
            padding-left: 20px;
        }}
        li::before {{
            content: "• ";
            color: #E74C3C;
            font-weight: bold;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background-color: #AED6F1;
            color: #000;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 0.8em;
            color: #555;
        }}
    </style>
</head>
<body>

<h1>📊 Rapport d'Analyse IT</h1>
{html_content}

<div class="footer">
    📑 Rapport généré automatiquement par Tucania AI - {input_file}
</div>

</body>
</html>
"""

# 💾 Enregistrer le contenu HTML temporaire
temp_html = "temp_rapport.html"
with open(temp_html, "w", encoding="utf-8") as f:
    f.write(styled_html)

# 🖨️ Génération du PDF
try:
    pdfkit.from_file(temp_html, output_pdf, configuration=pdfkit_config)
    print(f"✅ PDF généré avec succès : {output_pdf}")
except Exception as e:
    print(f"🚨 Erreur lors de la génération du PDF : {e}")

# 🧹 Nettoyage du fichier temporaire
os.remove(temp_html)
