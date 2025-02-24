from mistralai import Mistral
import os
import time 

api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)

batch_file = client.files.upload(
    file={
        "file_name": "batch_test.jsonl",
        "content": open("batch_test.jsonl", "rb")
    },
    purpose="batch"
)

print(f"✅ Fichier batch uploadé. ID : {batch_file.id}")

batch_job = client.batch.jobs.create(
    input_files=[batch_file.id],
    model="mistral-large-latest",
    endpoint="/v1/chat/completions",
    metadata={"job_type": "test_batch"}
)

print(f"🚀 Batch créé ! ID du job : {batch_job.id}")


while True:
    job_status = client.batch.jobs.get(job_id=batch_job.id)
    print(f"⏳ Statut actuel : {job_status.status}")

    if job_status.status in ["SUCCESS", "FAILED", "CANCELLED"]:
        break

    time.sleep(5)

print(f"✅ Batch terminé avec statut : {job_status.status}")

if job_status.status == "SUCCESS":
    client.files.download(file_id=job_status.output_file, output_path="batch_results.jsonl")
    print("📂 Résultats téléchargés dans `batch_results.jsonl`")
