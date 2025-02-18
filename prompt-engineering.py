import json
from collections import defaultdict, Counter
import re
import logging
import os
from datetime import datetime, timedelta
from mistralai import Mistral

# 🔑 Initialisation du client Mistral
api_key = os.environ.get("MISTRAL_API_KEY")
model = "mistral-large-latest"
client = Mistral(api_key=api_key)

# 📂 Création du répertoire des résumés
os.makedirs("summaries", exist_ok=True)

# 🛠️ Configuration des logs
logging.basicConfig(
    filename='tickets_analysis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🧹 Nettoyage et anonymisation du texte
def clean_text(text):
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\b[\w.-]+@[\w.-]+\.\w{2,4}\b', '[EMAIL_SUPPRIMÉ]', text)
    text = re.sub(r'\b\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b', '[NUMERO_SUPPRIMÉ]', text)
    return text.strip()

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

    # 📊 Calcul des statistiques
    total_tickets = len(tickets_list)
    themes = Counter(ticket.get('Themes', 'Non spécifié') for ticket in tickets_list)
    top_themes = ', '.join([f"{theme} ({count})" for theme, count in themes.most_common(5)])

    projects = Counter(ticket.get('project', 'Inconnu') for ticket in tickets_list)
    top_projects = ', '.join([f"{proj} ({count})" for proj, count in projects.most_common(3)])

    # 📆 Analyse temporelle sur les 6 derniers mois
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

    # 🧠 Construction du prompt simplifié
    today_str = today.strftime("%d/%m/%Y")
    prompt = f"""
    IMPORTANT : La réponse doit être exclusivement au format JSON.
Analyse les tickets ci-dessous et produis un **rapport structuré en JSON** contenant les sections suivantes :
IMPORTANT : La réponse doit être exclusivement au format JSON.

## 📊 **Statistiques générales**  
- Nombre total de tickets : {total_tickets}  
- Thèmes principaux (top 5) : {top_themes}  
- Projets principaux : {top_projects}  
- Évolution des tickets sur les 6 derniers mois : {ticket_trend}  
IMPORTANT : La réponse doit être exclusivement au format JSON.

**🔍 Analyse attendue :**  
- Identifie les **pics d'activité** et explique leurs causes.  
- Analyse les tendances et **explique leur signification** en lien avec les activités et événements connus.  
- Compare les **différences entre les projets** et **les thèmes récurrents**.  
IMPORTANT : La réponse doit être exclusivement au format JSON.

---
IMPORTANT : La réponse doit être exclusivement au format JSON.
## ⚠️ **Analyse approfondie des problèmes critiques**  
- Détaille les **problèmes les plus fréquents** et les **thèmes associés**.  
- Explique les **causes racines** (techniques, humaines, organisationnelles) en utilisant une **analyse causale**.  
- Classe les problèmes par ordre d'importance et d'impact.  
IMPORTANT : La réponse doit être exclusivement au format JSON.

**🔍 Analyse attendue :**  
- Utilise la **méthode des 5 pourquoi** pour identifier la cause fondamentale.  
- Donne des **exemples d'incidents** et explique pourquoi ils sont représentatifs.  
- Met en évidence les **facteurs externes** (mises à jour, changements de process) qui ont pu influer.  

---IMPORTANT : La réponse doit être exclusivement au format JSON.

## 🧠 **Analyse des solutions existantes**  
- Liste les solutions appliquées et évalue leur **efficacité** et leur **pérennité**.  
- Indique quelles solutions ont été **réutilisées** et pourquoi.  
- Décrit les **limites et contraintes** observées.  
IMPORTANT : La réponse doit être exclusivement au format JSON.

**🔍 Analyse attendue :**  
- Explique pourquoi certaines solutions sont réutilisées et d'autres non.  
- Identifie les **facteurs de succès et d'échec** des interventions.  
- Donne des recommandations sur les solutions à **généraliser** et celles à **abandonner**.  

---
IMPORTANT : La réponse doit être exclusivement au format JSON.
## 🔧 **Propositions d'amélioration**  
- Suggère des actions concrètes pour **réduire les incidents récurrents**.  
- Précise les **résultats attendus** et les **KPIs** à suivre.  
- Propose des améliorations organisationnelles et techniques.  
IMPORTANT : La réponse doit être exclusivement au format JSON.

**🔍 Analyse attendue :**  
- Précise les **coûts et bénéfices attendus**.  
- Propose des **actions à court et long terme**.  
- Suggère des **outils ou process** pertinents en fonction des problématiques.  

---
IMPORTANT : La réponse doit être exclusivement au format JSON.
## 🚨 **Points de vigilance et risques**  
- Liste les **risques potentiels** et leur **impact**.  
- Identifie les zones critiques nécessitant un suivi particulier.  
- Propose des stratégies de prévention et d'anticipation.  
IMPORTANT : La réponse doit être exclusivement au format JSON.

**🔍 Analyse attendue :**  
- Explique **comment les risques peuvent évoluer** si aucune action n'est prise.  
- Propose des **scénarios de gestion des risques** (plan B/C).  
- Précise les **indicateurs d'alerte précoce** à surveiller.  
IMPORTANT : La réponse doit être exclusivement au format JSON.

💡 **Sortie attendue :** Un **JSON clair et structuré**.  
IMPORTANT : La réponse doit être exclusivement au format JSON.
📂 **Tickets à analyser** :

"""

    # 🧾 Ajouter les tickets nettoyés
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

    prompt += "\n🔔 **IMPORTANT : La réponse doit être exclusivement au format JSON.**\n"
    # 🔍 Envoi vers l'API Mistral
    try:
        response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192
        )
        final_summary = response.choices[0].message.content

        # Vérifier si la réponse est un JSON valide
        try:
            json_data = json.loads(final_summary)
            logging.info(f"✅ Analyse complète réalisée pour {company}")

            # 💾 Enregistrer le résumé dans un fichier JSON
            filename = f"summaries/{company.replace(' ', '_')}_summary.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            print(f"\n✅ Résumé final enregistré pour {company} : {filename}\n")

        except json.JSONDecodeError:
            logging.error(f"❌ Erreur : Mistral n'a pas renvoyé un JSON valide.")
            print("🚨 Erreur : La réponse n'était pas un JSON valide.")

    except Exception as e:
        logging.error(f"❌ Erreur lors de l'analyse pour {company}: {e}")
        print(f"🚨 Erreur API Mistral : {e}")

print("🎯 Analyse complète terminée.")
