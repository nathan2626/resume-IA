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

    # 🧠 Construction du prompt en HTML structuré
    today_str = today.strftime("%d/%m/%Y")
    prompt = f"""
🎯 **Contexte** : 
Tu es un **expert en support IT**. Analyse les tickets de support de l'entreprise **'{company}'**, issus de l'outil **Tucania**.  
**Produis un rapport structuré en HTML** avec une présentation professionnelle et claire.  

---

### 🖹 **Sommaire** *(cliquer pour accéder aux sections)*  
1️⃣ [Statistiques générales](#stats)  
2️⃣ [Analyse approfondie des problèmes critiques](#problems)  
3️⃣ [Analyse des solutions existantes](#solutions)  
4️⃣ [Propositions d'amélioration](#improvements)  
5️⃣ [Points de vigilance et risques](#risks)  

---

## 1️⃣ Statistiques générales *(id="stats")*  
**Présente sous forme de tableau professionnel avec les colonnes : Catégorie | Détail | Analyse**.  
- Total de tickets : {total_tickets}  
- Thèmes principaux : {top_themes}  
- Projets principaux : {top_projects}  
- Évolution 6 derniers mois : {ticket_trend}  

💡 **Instruction :** Fournis des analyses sur les hausses, baisses et tendances remarquables.  

---

## 2️⃣ Analyse approfondie des problèmes critiques *(id="problems")*  
- Analyse les causes racines avec un raisonnement détaillé : **techniques, humaines et organisationnelles**.  
- Utilise les **données temporelles et contextuelles** pour trouver des **corrélations significatives**.  
- Donne des recommandations sur les **actions correctrices prioritaires**.  

💡 **Exemple attendu :**  
- **Problème :** Erreurs de signature électronique.  
- **Causes :** Incompatibilité entre les composants et workflows mal définis.  
- **Raisonnement :** Les erreurs ont augmenté de 15 % après une mise à jour système, suggérant un problème de configuration.  
- **Recommandation :** Ajuster les paramètres et effectuer des tests de non-régression après chaque mise à jour.  

---

## 3️⃣ Analyse des solutions existantes *(id="solutions")*  
- Évalue les solutions appliquées en termes de **fréquence de réutilisation** et **efficacité observée**.  
- Explique pourquoi certaines solutions fonctionnent mieux.  
- Propose des **axes d'amélioration** sur les solutions inefficaces.  

💡 **Exemple attendu :**  
- **Solution testée :** Automation des workflows.  
- **Résultat :** 70 % des incidents liés aux erreurs humaines ont disparu.  
- **Prochaine étape :** Étendre l'automatisation à d'autres processus critiques.  

---

## 4️⃣ Propositions d'amélioration *(id="improvements")*  
- Propose des **mesures techniques et organisationnelles** en détaillant les impacts attendus.  
- Donne des exemples d'implémentation et des **KPIs** pour suivre les progrès.  

💡 **Exemple attendu :**  
- **Amélioration :** Surveillance en temps réel des workflows.  
- **Impact attendu :** Diminution des erreurs de 30 % et des temps d’intervention de 25 %.  
- **Recommandation :** Mettre en place l'outil X et former les équipes IT.  

---

## 5️⃣ Points de vigilance et risques *(id="risks")*  
- Dresse la liste des **risques potentiels** et de leurs conséquences.  
- Propose des **plans d'atténuation et stratégies de prévention**.  

💡 **Exemple attendu :**  
- **Risque :** Perte de compétences internes.  
- **Conséquence :** Allongement des temps de résolution et erreurs répétées.  
- **Plan d'action :** Mettre en place un **programme de formation continue** et une **documentation centralisée**.  

---

🎨 **Instructions de style :**  
- Mise en page avec **tableaux professionnels**, **paragraphes aérés**, et **titres différenciés**.  
- Inclure des **icônes visuelles** et des **couleurs différenciées** selon les sections.  
- Utiliser des **ancrages hypertextes** dans le sommaire.  

---

📂 **Tickets fournis pour analyse :**

"""

    # 🧾 Ajouter les tickets nettoyés
    for ticket in tickets_list:
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

    prompt += "\n🔔 **Analyse approfondie et complète attendue en format HTML.**\n"

    # 🔍 Envoi vers l'API Mistral
    try:
        response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192
        )
        final_summary = response.choices[0].message.content
        logging.info(f"✅ Analyse complète réalisée pour {company}")

        # 💾 Enregistrer le résumé dans un fichier JSON
        filename = f"summaries/{company.replace(' ', '_')}_summary.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"company": company, "summary": final_summary}, f, ensure_ascii=False, indent=4)

        print(f"\n✅ Résumé final enregistré pour {company} : {filename}\n")

    except Exception as e:
        logging.error(f"❌ Erreur lors de l'analyse pour {company}: {e}")
        print(f"🚨 Erreur API Mistral : {e}")

print("🎯 Analyse complète terminée.")
