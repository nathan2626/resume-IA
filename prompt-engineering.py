import json
from collections import defaultdict
import re
import logging
import os
import time
from mistralai import Mistral

# 🔑 Lecture de la clé API et de l'URL
api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"

client = Mistral(api_key=api_key)

# 📂 Création d'un répertoire pour enregistrer les résumés
os.makedirs("summaries", exist_ok=True)

# 🛠️ Configuration des logs
logging.basicConfig(
    filename='tickets_analysis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🧹 Nettoyage et anonymisation du texte
def clean_text(text):
    text = re.sub(r'\n+', ' ', text)  # Remplacer les sauts de ligne par des espaces
    text = re.sub(r'\s{2,}', ' ', text)  # Supprimer les espaces multiples
    text = re.sub(r'\b[\w.-]+@[\w.-]+\.\w{2,4}\b', '[EMAIL_SUPPRIMÉ]', text)  # Supprimer les emails
    text = re.sub(r'\b\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b', '[NUMERO_SUPPRIMÉ]', text)  # Numéros de tel
    return text.strip()

# 🧠 Découper les tickets en lots de 50
def batch_tickets(tickets, batch_size=50):
    for i in range(0, len(tickets), batch_size):
        yield tickets[i:i + batch_size]

# 🚀 Chargement et tri des tickets
with open("data.json", "r", encoding="utf-8") as f:
    tickets = json.load(f)

# 🏢 Regrouper les tickets par entreprise
company_tickets = defaultdict(list)
for ticket in tickets:
    company = ticket.get("company", "Inconnue")
    company_tickets[company].append(ticket)

# 🎯 Traitement par entreprise
for company, tickets_list in company_tickets.items():
    logging.info(f"📊 Début de l'analyse pour : {company} (Total : {len(tickets_list)})")
    all_summaries = []

    # 💥 Envoi par batch de 50 tickets
    for batch_num, batch in enumerate(batch_tickets(tickets_list, 50), start=1):
        logging.info(f"📦 Traitement du batch {batch_num} pour {company} (Tickets: {len(batch)})")

        # 📄 Construction du prompt optimisé
        prompt = f"""
🎯 **Contexte** : 
Tu es un assistant expert en support IT. Tu dois analyser les tickets de support de l'entreprise **'{company}'**. 
Ces tickets proviennent de l'outil **Tucania** et concernent des incidents, demandes et optimisations sur diverses fonctionnalités.

📊 **Objectif** : 
Produire un rapport détaillé et structuré en plusieurs parties :

---

🔍 **1. Statistiques générales**
- Total de tickets : indique le nombre total.
- Répartition par thème (top 5) et fréquence en pourcentage.
- Entreprises et projets concernés : donne les 3 principaux acteurs impliqués.
- Analyse temporelle : évolution des tickets sur les 6 derniers mois (si données disponibles).

---

⚠️ **2. Analyse des problèmes critiques**
- Identifie les **problèmes récurrents** et les **thèmes associés**.
- Fournis des exemples concrets de tickets illustrant ces problèmes.
- Donne un **classement des problèmes** par fréquence décroissante.

---

🧠 **3. Analyse des solutions existantes**
- Liste les solutions déjà appliquées et leur efficacité.
- Évalue si certaines solutions ont été réutilisées pour plusieurs tickets.

---

🔧 **4. Propositions d'amélioration**
- Recommande des actions spécifiques pour éviter la récurrence des problèmes.
- Suggère des processus d'automatisation ou d'amélioration des outils existants.
- Donne des **bonnes pratiques** basées sur les problèmes observés.

---

🚨 **5. Points de vigilance et risques**
- Identifie les zones critiques qui pourraient nécessiter une attention particulière.
- Propose des stratégies de prévention et d'anticipation.

---

📝 **Style demandé** :
- Présente les résultats avec des **titres clairs et des puces**.
- Utilise des **chiffres et pourcentages** pour appuyer les constats.
- Rends le texte **lisible et détaillé**.
- Utilise des **émoticônes** pour aider à la compréhension visuelle.

---

🎛️ **Données à analyser** :

"""

        # 🧾 Ajouter les tickets dans le prompt
        for ticket in batch:
            description = clean_text(ticket['description'] or "Aucune description.")
            prompt += (
                f"🔹 **Ticket #{ticket['id']}**\n"
                f"- 🏷️ Titre : {ticket['title']}\n"
                f"- 📝 Description : {description}\n"
                f"- 🚨 Priorité : {ticket['priority']}\n"
                f"- 🎯 Thèmes : {ticket['Themes'] or 'Non spécifié'}\n"
                f"- 🕒 Temps suivi : {ticket['trackedHours']}h\n"
                f"- 📅 Date de création : {ticket['dateCreation']}\n\n"
            )

        prompt += "\n🔔 **Analyse complète et détaillée attendue**.\n"

        # 🔍 Envoi vers Mistral
        try:
            chat_response = client.chat.complete(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=8192
            )
            summary = chat_response.choices[0].message.content
            all_summaries.append(summary)
            logging.info(f"✅ Batch {batch_num} traité avec succès pour {company}")

            time.sleep(1)
        except Exception as e:
            logging.error(f"❌ Erreur lors du traitement du batch {batch_num} pour {company}: {e}")
            continue

    # 📝 Fusionner les résumés
    final_summary = "\n\n".join(all_summaries)

    # 💾 Enregistrer le résumé dans un fichier JSON
    filename = f"summaries/{company.replace(' ', '_')}_summary.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"company": company, "summary": final_summary}, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Résumé final enregistré pour {company} : {filename}\n")
    logging.info(f"📁 Résumé final enregistré : {filename}")

print("🎯 Analyse complète terminée.")
