import json
import os
import re
import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from io import BytesIO
from mistralai import Mistral

# 🔑 Initialisation du client Mistral
api_key = os.environ.get("MISTRAL_API_KEY")
model = "mistral-large-latest"
client = Mistral(api_key=api_key)

# 📂 Création des répertoires
os.makedirs("summaries", exist_ok=True)

# 🛠️ Configuration des logs
logging.basicConfig(
    filename="synthese_tickets.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 🧹 Nettoyage du texte
def clean_text(text):
    if not text:
        return "Aucune description."
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

# 🚀 Chargement des données JSON
json_file = "data.json"
try:
    with open(json_file, "r", encoding="utf-8") as f:
        tickets = json.load(f)
except Exception as e:
    logging.error(f"Erreur lors du chargement du fichier JSON : {e}")
    exit("❌ Impossible de charger les données.")

# 🏢 Sélection d'une entreprise à analyser
company = "Novo nordisk"  # Remplace avec l'entreprise à analyser
tickets_list = [t for t in tickets if t.get("company") == company]

if not tickets_list:
    exit(f"❌ Aucun ticket trouvé pour l'entreprise {company}")

logging.info(f"📊 Analyse en cours pour : {company} (Total : {len(tickets_list)})")

# 📂 Création des dossiers pour l'entreprise
company_folder = f"summaries/{company.replace(' ', '_')}"
batch_folder = f"{company_folder}/batches"
os.makedirs(company_folder, exist_ok=True)
os.makedirs(batch_folder, exist_ok=True)

# 📊 Statistiques
total_tickets = len(tickets_list)
themes = Counter(ticket.get('Themes', 'Non spécifié') for ticket in tickets_list)
top_themes = ', '.join([f"{theme} ({count})" for theme, count in themes.most_common(5)])

projects = Counter(ticket.get('project', 'Inconnu') for ticket in tickets_list)
top_projects = ', '.join([f"{proj} ({count})" for proj, count in projects.most_common(3)])

# 📆 Analyse temporelle
today = datetime.now()
six_months_ago = today - timedelta(days=180)
monthly_counts = defaultdict(int)
weekly_counts = defaultdict(int)
daily_counts = defaultdict(int)

empty_tickets = 0
for t in tickets_list:
    try:
        date_obj = datetime.strptime(t['dateCreation'], '%d/%m/%Y %H:%M')
    except ValueError:
        try:
            date_obj = datetime.strptime(t['dateCreation'], '%Y-%m-%d')
        except ValueError:
            logging.warning(f"⚠️ Format de date inconnu : {t['dateCreation']}")
            continue

    if not t['description'] or len(t['description'].split()) < 5:
        empty_tickets += 1

    if date_obj >= six_months_ago:
        month = date_obj.strftime('%Y-%m')
        week = date_obj.strftime('%Y-%U')
        day = date_obj.strftime('%A')

        monthly_counts[month] += 1
        weekly_counts[week] += 1
        daily_counts[day] += 1

ticket_trend = ', '.join([f"{month}: {count}" for month, count in sorted(monthly_counts.items())])
weekly_trend = ', '.join([f"{week}: {count}" for week, count in sorted(weekly_counts.items())])
daily_trend = ', '.join([f"{day}: {count}" for day, count in sorted(daily_counts.items())])

# 🛠️ **Création du fichier batch JSONL**
batch_requests = []
methods = [
    ("5_pourquoi", "Analyse détaillée des causes profondes avec la méthode des 5 pourquoi."),
    ("fishbone", "Analyse des causes avec le Diagramme d’Ishikawa (5M ou Fishbone)."),
    ("pareto", "Analyse de Pareto (80/20) pour identifier les problèmes les plus impactants."),
    ("series_temporelles", "Analyse de séries temporelles des tendances des incidents."),
    ("spc", "Méthode des cartes de contrôle (SPC - Statistical Process Control)."),
    ("text_mining", "Analyse Text Mining & NLP pour détecter les tendances cachées."),
    ("correlation", "Corrélation et analyse factorielle des incidents."),
]

for i, (method_key, method_desc) in enumerate(methods):
    batch_requests.append({
        "custom_id": str(i),
        "body": {
            "max_tokens": 4096,
            "messages": [
                {"role": "user", "content": f"""
## 🔬 Analyse avancée : {method_desc}  
- Applique cette méthode pour analyser les données disponibles.  
- Explique en détail les résultats et ton raisonnement.  
"""}
            ]
        }
    })

batch_file_path = f"{batch_folder}/batch_requests.jsonl"
with open(batch_file_path, "w", encoding="utf-8") as f:
    for request in batch_requests:
        f.write(json.dumps(request) + "\n")

# 📤 **Upload du batch file**
with open(batch_file_path, "rb") as f:
    batch_data = client.files.upload(
        file={
            "file_name": "batch_requests.jsonl",
            "content": f.read()
        },
        purpose="batch"
    )

# 🚀 **Création du batch job**
batch_job = client.batch.jobs.create(
    input_files=[batch_data.id],
    model=model,
    endpoint="/v1/chat/completions",
    metadata={"job_type": "analysis"}
)

# ⏳ **Suivi du batch**
while True:
    batch_status = client.batch.jobs.get(job_id=batch_job.id)
    print(f"⏳ En attente des résultats... Statut actuel : {batch_status.status}")
    if batch_status.status == "SUCCESS":
        break
    time.sleep(10)

# 📥 **Téléchargement des résultats**
output_file_path = f"{batch_folder}/batch_results.jsonl"
with open(output_file_path, "wb") as f_out:
    output_file = client.files.download(file_id=batch_status.output_file)
    for chunk in output_file.stream:
        f_out.write(chunk)

print(f"\n✅ Synthèse batch enregistrée pour {company} : {output_file_path}")

print("🎯 Analyse complète avec Batches terminée.")
