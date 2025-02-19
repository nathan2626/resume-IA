import json
from collections import defaultdict, Counter
import re
import logging
import os
from datetime import datetime, timedelta
from mistralai import Mistral

# 🔑 Initialisation
api_key = os.environ.get("MISTRAL_API_KEY")
model = "mistral-large-latest"
client = Mistral(api_key=api_key)

# 📂 Répertoire des résumés
os.makedirs("summaries", exist_ok=True)

# 🛠️ Logs
logging.basicConfig(
    filename='tickets_analysis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🧹 Nettoyage texte
def clean_text(text):
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\b[\w.-]+@[\w.-]+\.\w{2,4}\b', '[EMAIL_SUPPRIMÉ]', text)
    text = re.sub(r'\b\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b', '[NUMERO_SUPPRIMÉ]', text)
    return text.strip()

# 🚀 Chargement des tickets
with open("data.json", "r", encoding="utf-8") as f:
    tickets = json.load(f)

# 🏢 Regroupement par entreprise
company_tickets = defaultdict(list)
for ticket in tickets:
    company = ticket.get("company", "Inconnue")
    company_tickets[company].append(ticket)

# 🎯 Traitement par entreprise
for company, tickets_list in company_tickets.items():
    logging.info(f"📊 Analyse en cours pour : {company} (Total : {len(tickets_list)})")

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

    # 🧠 Prompt pour analyse approfondie des causes
    prompt = f"""
Tu es un analyste expert en support IT, en support User, en IT. Tu es considéré comme le top 0.0001% dans ton domaine.  
Analyse les tickets fournis et produis un **rapport détaillé** en texte brut avec les sections suivantes :  

---

## 📊 1. Statistiques générales  
- Nombre total de tickets : {total_tickets}  
- Nombre de tickets vides ou très courts : {empty_tickets}  
- Thèmes principaux : {top_themes}  
- Projets principaux : {top_projects}  
- Évolution sur les 6 derniers mois : {ticket_trend}  
- Évolution hebdomadaire : {weekly_trend}  
- Évolution quotidienne : {daily_trend}  

🔍 **Analyse attendue :**  
- Identifier les **pics d'activité** et leurs causes.  
- Détecter des tendances récurrentes (par jour de la semaine, début de mois, fin de mois, etc.).  
- Comparer les **projets et thèmes récurrents**.  

---

## ⚠️ 2. Analyse approfondie des problèmes critiques  
- Identifier les **problèmes récurrents** et leurs **thèmes associés**.  
- Expliquer les **causes racines** : techniques, humaines, organisationnelles.  
- Classer les problèmes par **fréquence et impact**.  
- Identifier les problèmes persistants vs. les nouveaux problèmes.  
- Regrouper les tickets en **catégories et sous-catégories** pour mieux comprendre leur nature.  

🔍 **Analyse attendue :**  
- Utiliser les **méthodes d’analyse avancées** :
  - **5 Pourquoi** (Root Cause Analysis)  : fais le en détails pour les principaux problèmes
  - **Diagramme d’Ishikawa (5M ou Fishbone)**  : fais le en détails en expliquant ton raisonnement
  - **Analyse de Pareto (80/20)**  : fais le en détails en expliquant ton raisonnement
  - **Analyse de séries temporelles**  : fais le en détails en expliquant ton raisonnement
  - **Méthode des cartes de contrôle (SPC - Statistical Process Control)**  : fais le en détails en expliquant ton raisonnement
  - **Text Mining & NLP** sur les tickets  : fais le en détails en expliquant ton raisonnement
  - **Corrélation et analyse factorielle**  : fais le en détails en expliquant ton raisonnement

- Distinguer les problèmes liés à des **changements récents** (mises à jour, nouvelles fonctionnalités) des **problèmes persistants**.  
- Examiner les **corrélations entre les tickets** pour identifier des modèles cachés.  
- Repérer si certains types de tickets apparaissent de façon récurrente à des **moments spécifiques** (début/fin de semaine, début de mois, etc.).  

---

📂 **Tickets à analyser** :  

"""

    # 🧾 Ajout des tickets
    for ticket in tickets_list:
        description = clean_text(ticket['description'] or "Aucune description.")
        prompt += (
            f"Ticket #{ticket['id']} :\n"
            f"- Titre : {ticket['title']}\n"
            f"- Description : {description}\n"
            f"- Priorité : {ticket['priority']}\n"
            f"- Thèmes : {ticket['Themes'] or 'Non spécifié'}\n"
            f"- Temps suivi : {ticket['trackedHours']}h\n"
            f"- Date de création : {ticket['dateCreation']}\n\n"
        )

    prompt += "\n🔔 **IMPORTANT : La réponse doit être rédigée en texte clair et professionnel, sans instructions visibles.**\n"

    # 🔍 Envoi vers l'API Mistral
    try:
        response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=int(8192)
        )
        final_summary = response.choices[0].message.content

        # 💾 Enregistrer la réponse
        filename = f"summaries/{company.replace(' ', '_')}_causes2_summary.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_summary)

        print(f"\n✅ Rapport final enregistré pour {company} : {filename}\n")

    except Exception as e:
        logging.error(f"❌ Erreur lors de l'analyse pour {company}: {e}")
        print(f"🚨 Erreur API Mistral : {e}")

print("🎯 Analyse complète terminée.")
