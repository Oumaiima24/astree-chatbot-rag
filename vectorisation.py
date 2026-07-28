import json
import chromadb
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────
# 1. Charger les chunks
# ─────────────────────────────────────────
with open("astree_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f" Chunks chargés : {len(chunks)}")

# ─────────────────────────────────────────
# 2. Charger le modèle d'embedding
# ─────────────────────────────────────────
print(" Chargement du modèle (1 minute la première fois)...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print(" Modèle chargé !")

# ─────────────────────────────────────────
# 3. Créer la base ChromaDB
# ─────────────────────────────────────────
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="astree")
print(" Base ChromaDB créée !")

# ─────────────────────────────────────────
# 4. Indexer tous les chunks
# ─────────────────────────────────────────
textes = [c["texte"] for c in chunks]
ids    = [f"chunk_{i}" for i in range(len(chunks))]
metas  = [{"url": c["url"], "titre": c["titre"], "source": c["source"]} for c in chunks]

print(" Vectorisation en cours...")
embeddings = model.encode(textes, show_progress_bar=True).tolist()

collection.add(documents=textes, embeddings=embeddings, metadatas=metas, ids=ids)
print(f" {len(chunks)} chunks indexés dans ChromaDB !")

# ─────────────────────────────────────────
# 5. Test de recherche
# ─────────────────────────────────────────
print("\n Test de recherche...")
questions_test = [
    "Comment assurer mon véhicule ?",
    "Quelles sont les garanties habitation ?",
    "Comment contacter Astrée ?"
]

for question in questions_test:
    vecteur = model.encode(question).tolist()
    resultats = collection.query(query_embeddings=[vecteur], n_results=2)
    print(f"\n❓ {question}")
    for doc, meta in zip(resultats["documents"][0], resultats["metadatas"][0]):
        print(f"    [{meta['source']}] {meta['titre']}")
        print(f"      {doc[:120]}...")