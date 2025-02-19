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
    for t in tickets_list:
        try:
            date_obj = datetime.strptime(t['dateCreation'], '%d/%m/%Y %H:%M')
        except ValueError:
            try:
                date_obj = datetime.strptime(t['dateCreation'], '%Y-%m-%d')
            except ValueError:
                logging.warning(f"⚠️ Format de date inconnu : {t['dateCreation']}")
                continue

        if date_obj >= six_months_ago:
            month = date_obj.strftime('%Y-%m')
            monthly_counts[month] += 1

    ticket_trend = ', '.join([f"{month}: {count}" for month, count in sorted(monthly_counts.items())])

    # 🧠 Prompt simplifié
    prompt = f"""
Tu es un expert en support IT.  
Analyse les tickets fournis et produis un **rapport clair et détaillé** en texte brut avec les sections suivantes :

--- 

## 📊 1. Statistiques générales  
- Nombre total de tickets : {total_tickets}  
- Thèmes principaux : {top_themes}  
- Projets principaux : {top_projects}  
- Évolution sur les 6 derniers mois : {ticket_trend}  

🔍 **Analyse attendue** :  
- Identifier les **pics d'activité** et leurs causes.  
- Expliquer les tendances et les corrélations pertinentes.  
- Comparer les projets et les thèmes récurrents.  

---

## ⚠️ 2. Analyse approfondie des problèmes critiques  
- Identifier les **problèmes récurrents** et leurs **thèmes associés**.  
- Expliquer les **causes racines** : techniques, humaines, organisationnelles.  
- Classer les problèmes par **fréquence et impact**.  

🔍 **Analyse attendue** :  
- Utiliser la **méthode des 5 pourquoi** pour comprendre les causes profondes.  
- Distinguer les problèmes liés à des **changements récents** (mises à jour, nouvelles fonctionnalités) des **problèmes persistants**.  
- Proposer des **actions correctives** et expliquer pourquoi elles seraient efficaces.  

---

## 🧠 3. Analyse des solutions existantes  
- Dresser la liste des **solutions appliquées** et leur efficacité.  
- Identifier celles qui ont été **réutilisées** et pourquoi.  
- Souligner les **limitations et axes d'amélioration**.  

🔍 **Analyse attendue** :  
- Expliquer les **succès et échecs**.  
- Montrer **comment les solutions réutilisées** ont permis de résoudre d'autres problèmes.  
- Proposer des **ajustements** pour augmenter l'efficacité des solutions.  

---

## 🔧 4. Propositions d'amélioration  
- Proposer des actions concrètes pour **réduire la récurrence des incidents**.  
- Détailler les **résultats attendus** et les **indicateurs à suivre**.  
- Suggérer des évolutions techniques et organisationnelles.  

🔍 **Analyse attendue** :  
- Inclure des recommandations de **processus d'automatisation**.  
- Proposer des **ajustements dans la gestion des tickets**.  
- Indiquer les **risques d'inaction** et leurs conséquences.  

---

## 🚨 5. Points de vigilance et risques  
- Identifier les **zones critiques** et les **risques potentiels**.  
- Proposer des **mesures d'anticipation** et des **plans d'action**.  

🔍 **Analyse attendue** :  
- Expliquer **les risques associés à l'évolution de la charge**.  
- Proposer un **plan de suivi** avec des **indicateurs de performance**.  
- Recommander des **tests réguliers** et des **audits internes**.  

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
            max_tokens=8192
        )
        final_summary = response.choices[0].message.content

        # 💾 Enregistrer la réponse
        filename = f"summaries/{company.replace(' ', '_')}_summary.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_summary)

        print(f"\n✅ Rapport final enregistré pour {company} : {filename}\n")

    except Exception as e:
        logging.error(f"❌ Erreur lors de l'analyse pour {company}: {e}")
        print(f"🚨 Erreur API Mistral : {e}")

print("🎯 Analyse complète terminée.")
