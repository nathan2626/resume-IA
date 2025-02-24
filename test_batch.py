import json
import os
import time
from mistralai import Mistral

# 🔑 Initialisation du client
api_key = os.environ.get("MISTRAL_API_KEY")
model = "mistral-large-latest"  # Modèle plus rapide pour le test
client = Mistral(api_key=api_key)

# 📂 Création du fichier batch test
batch_file = "test_batch.jsonl"
batch_requests = [
    {"custom_id": "1", "body": {"max_tokens": 100, "messages": [{"role": "user", "content": "Quelle est la meilleure pizza italienne ?"}]}},
    {"custom_id": "2", "body": {"max_tokens": 100, "messages": [{"role": "user", "content": "Quel est le plus grand pays du monde ?"}]}},
    {"custom_id": "3", "body": {"max_tokens": 100, "messages": [{"role": "user", "content": "Donne-moi une blague sur les développeurs."}]}},
    {"custom_id": "4", "body": {"max_tokens": 100, "messages": [{"role": "user", "content": "Explique-moi la théorie de la relativité en une phrase."}]}},
    {"custom_id": "5", "body": {"max_tokens": 100, "messages": [{"role": "user", "content": "Quels sont les avantages du langage Python ?"}]}}
]

# 📂 Écriture du fichier JSONL
with open(batch_file, "w", encoding="utf-8") as f:
    for request in batch_requests:
        f.write(json.dumps(request) + "\n")

print(f"✅ Fichier batch généré : {batch_file}")

# 📤 Envoi du fichier batch à Mistral
with open(batch_file, "rb") as f:
    batch_data = client.files.upload(
        file={"file_name": batch_file, "content": f.read()},
        purpose="batch"
    )

print(f"🚀 Fichier batch uploadé. ID du fichier : {batch_data.id}")

# 🏁 Création du job batch
batch_job = client.batch.jobs.create(
    input_files=[batch_data.id],
    model=model,
    endpoint="/v1/chat/completions",
    metadata={"job_type": "test"}
)

print(f"🚀 Batch soumis ! ID du job : {batch_job.id}")

# ⏳ Attente des résultats
timeout = 300  # 5 minutes max
start_time = time.time()

while True:
    batch_status = client.batch.jobs.get(job_id=batch_job.id)
    print(f"⏳ En attente... Statut actuel : {batch_status.status}")

    if batch_status.status == "SUCCESS":
        print("✅ Batch terminé avec succès !")
        break

    if time.time() - start_time > timeout:
        print("⏰ Temps d'attente dépassé ! Le batch prend trop de temps.")
        break

    time.sleep(5)

# 📥 Téléchargement des résultats
if batch_status.status == "SUCCESS":
    output_file = client.files.download(file_id=batch_status.output_file)
    output_path = "test_batch_results.jsonl"
    
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in output_file.stream:
            f.write(chunk.decode("utf-8"))
    
    print(f"📥 Résultats téléchargés : {output_path}")
