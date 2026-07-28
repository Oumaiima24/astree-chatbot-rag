import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

# ─────────────────────────────────────────
# 1. Configuration
# ─────────────────────────────────────────
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxx"

client_groq = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────
# 2. Charger le modèle d'embedding + ChromaDB
# ─────────────────────────────────────────
print(" Chargement du modèle...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

client_chroma = chromadb.PersistentClient(path="./chroma_db")
collection = client_chroma.get_collection(name="astree")
print(" Prêt !")

# ─────────────────────────────────────────
# 3. Fonction de recherche (Retrieval)
# ─────────────────────────────────────────
def rechercher_contexte(question, n_results=4):
    vecteur = model.encode(question).tolist()
    resultats = collection.query(query_embeddings=[vecteur], n_results=n_results)

    chunks = resultats["documents"][0]
    metas  = resultats["metadatas"][0]

    contexte = ""
    sources = []
    for chunk, meta in zip(chunks, metas):
        contexte += f"\n---\n[Source: {meta['titre']}]\n{chunk}\n"
        sources.append({"titre": meta["titre"], "url": meta["url"]})

    return contexte, sources

# ─────────────────────────────────────────
# 4. Fonction de génération (Augmented Generation)
# ─────────────────────────────────────────
SYSTEM_PROMPT = """Tu es l'assistant virtuel du site Astrée Assurances (Tunisie).
Réponds UNIQUEMENT à partir des informations fournies dans le contexte ci-dessous.
Si l'information n'est pas dans le contexte, dis honnêtement :
"Je n'ai pas cette information, je vous invite à contacter Astrée directement."
Réponds en français, de manière claire et professionnelle, sans inventer de détails."""

def generer_reponse(question, contexte):
    prompt = f"""Contexte :
{contexte}

Question : {question}

Réponse :"""

    completion = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )
    return completion.choices[0].message.content

# ─────────────────────────────────────────
# 5. Pipeline RAG complet
# ─────────────────────────────────────────
def chatbot(question):
    contexte, sources = rechercher_contexte(question)
    reponse = generer_reponse(question, contexte)
    return reponse, sources

# ─────────────────────────────────────────
# 6. Test interactif
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n Chatbot Astrée — tape 'quit' pour sortir\n")

    while True:
        question = input("❓ Vous : ")
        if question.lower() in ["quit", "exit", "q"]:
            break

        reponse, sources = chatbot(question)

        print(f"\n Assistant : {reponse}")
        print(f"\n Sources :")
        for s in sources:
            print(f"   - {s['titre']} ({s['url']})")
        print()