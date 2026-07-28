from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from groq import Groq
from langdetect import detect
from apscheduler.schedulers.background import BackgroundScheduler
import requests as http_requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import json
import re
import time
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxx" # ← remplace par ta clé

client_groq   = Groq(api_key=GROQ_API_KEY)
print("⏳ Chargement du modèle...")
model         = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
reranker      = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
client_chroma = chromadb.PersistentClient(path="./chroma_db")
collection    = client_chroma.get_or_create_collection(name="astree")
print("✅ Modèle et base ChromaDB chargés !")

# ─────────────────────────────────────────
# URLs à scraper
# ─────────────────────────────────────────
URLS = [
    "https://www.astree.com.tn/fr/agences",
    "https://www.astree.com.tn/fr/assistance",
    "https://www.astree.com.tn/fr/astree/presentation",
    "https://www.astree.com.tn/fr/astree/rse-esg",
    "https://www.astree.com.tn/fr/particuliers",
    "https://www.astree.com.tn/fr/particulier/voyage",
    "https://www.astree.com.tn/fr/particulier/habitation",
    "https://www.astree.com.tn/fr/particulier/automobile",
    "https://www.astree.com.tn/fr/particulier/bateau",
    "https://www.astree.com.tn/fr/particulier/garanties-des-accidents-de-la-vie",
    "https://www.astree.com.tn/fr/particulier/assurances-individuelles-scolaire",
    "https://www.astree.com.tn/fr/particulier/assurances-individuelles-accidents",
    "https://www.astree.com.tn/fr/particulier/prevoyance",
    "https://www.astree.com.tn/fr/particulier/garantie-pret",
    "https://www.astree.com.tn/fr/particulier/epargne",
    "https://www.astree.com.tn/fr/particulier/prevoyance-epargne-retraite",
    "https://www.astree.com.tn/fr/particulier/avenir-de-mes-enfants",
    "https://www.astree.com.tn/fr/particulier/materiel-informatique",
    "https://www.astree.com.tn/fr/simulateur",
    "https://www.astree.com.tn/fr/entreprises-professionnels",
    "https://www.astree.com.tn/fr/specialistes-de-la-construction",
    "https://www.astree.com.tn/fr/espace-agriculteurs",
    "https://www.astree.com.tn/fr/actualite",
    "https://www.astree.com.tn/fr/publications",
    "https://www.astree.com.tn/fr/conformite-reglementaire",
    "https://www.astree.com.tn/fr/faq",
    "https://www.astree.com.tn/fr/contact",
    "https://www.astree.com.tn/fr/carrieres",
    "https://www.astree.com.tn/fr/astree/gouvernance",
    "https://www.astree.com.tn/fr/astree/chiffres-cles",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

# ─────────────────────────────────────────
# Utilitaires nettoyage
# ─────────────────────────────────────────
def nettoyer(texte):
    if not texte: return ""
    return re.sub(r'\s+', ' ', texte).strip()

def decouper(texte, url, titre, source, taille=400, overlap=50):
    mots = texte.split()
    if len(mots) < 15: return []
    chunks, i = [], 0
    while i < len(mots):
        chunks.append({"url": url, "titre": titre, "source": source, "texte": ' '.join(mots[i:i+taille])})
        i += taille - overlap
    return chunks

def dedupliquer_sinistre(entries):
    textes = [nettoyer(e.get("texte","")) for e in entries]
    textes = [t for t in textes if t and len(t.split()) >= 8]
    return [t for i, t in enumerate(textes)
            if not any(t != a and t in a for j, a in enumerate(textes) if i != j)]

# ─────────────────────────────────────────
# Scraping
# ─────────────────────────────────────────
def scraper_site():
    print(f"\n🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M')}] Début du scraping...")
    session = http_requests.Session()
    retry   = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))

    pages = []
    for url in URLS:
        try:
            r = session.get(url, headers=HEADERS, timeout=30, verify=False)
            r.raise_for_status()
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")

            h1    = soup.find("h1")
            meta  = soup.find("meta", attrs={"name": "description"})
            desc1 = soup.find("div", class_="desc1")
            desc2 = soup.find("div", class_="desc2")

            garanties = [{"id": t.get("id"), "texte": t.get_text(" ", strip=True)}
                         for t in soup.find_all("div", class_="tab-pane") if t.get_text(strip=True)]

            avantages = [{"titre":   (i.find("div", class_="title-avantage") or object()).get_text(strip=True) if i.find("div", class_="title-avantage") else None,
                          "contenu": (i.find("div", class_="contenu-avantage") or object()).get_text(strip=True) if i.find("div", class_="contenu-avantage") else None}
                         for i in soup.find_all("div", class_="item-avantage")]

            sinistre = [{"titre": (b.find(["h2","h3","h4"]) or object()).get_text(strip=True) if b.find(["h2","h3","h4"]) else None,
                         "texte": b.get_text(" ", strip=True)}
                        for b in soup.find_all("div", class_=lambda c: c and "sinistre" in c.lower()) if b.get_text(strip=True)]

            faqs_q = soup.find_all("div", class_="views-accordion-header")
            faqs_r = soup.find_all("div", class_="views-field-body")
            faqs   = [{"question": q.get_text(strip=True), "reponse": r.get_text(strip=True)}
                      for q, r in zip(faqs_q, faqs_r) if q.get_text(strip=True)]

            pages.append({
                "url":           url,
                "titre":         h1.get_text(strip=True) if h1 else None,
                "description":   meta["content"].strip() if meta and meta.get("content") else None,
                "date_scraping": time.strftime("%Y-%m-%d"),
                "introduction":  {"desc1": desc1.get_text(" ", strip=True) if desc1 else None,
                                  "desc2": desc2.get_text(" ", strip=True) if desc2 else None},
                "garanties":  garanties,
                "avantages":  avantages,
                "sinistre":   sinistre,
                "faqs":       faqs,
            })
            time.sleep(2)

        except Exception as e:
            print(f"  ❌ Erreur sur {url} : {e}")

    print(f"  ✅ {len(pages)} pages scrapées")
    return pages

# ─────────────────────────────────────────
# Extraction des candidats
# ─────────────────────────────────────────
def extraire_candidats(pages):
    candidats = []
    for page in pages:
        if "erreur" in page: continue
        url, titre = page.get("url",""), page.get("titre","")

        desc = nettoyer(page.get("description",""))
        if desc: candidats.append({"texte": desc, "url": url, "titre": titre, "source": "description"})

        intro   = page.get("introduction",{})
        t_intro = nettoyer((intro.get("desc1") or "") + " " + (intro.get("desc2") or ""))
        if t_intro: candidats.append({"texte": t_intro, "url": url, "titre": titre, "source": "introduction"})

        for g in page.get("garanties",[]):
            t = nettoyer(g.get("texte",""))
            if t: candidats.append({"texte": t, "url": url, "titre": titre, "source": "garanties"})

        for av in page.get("avantages",[]):
            t = nettoyer((av.get("titre") or "") + " : " + (av.get("contenu") or ""))
            if t: candidats.append({"texte": t, "url": url, "titre": titre, "source": "avantages"})

        for t in dedupliquer_sinistre(page.get("sinistre",[])):
            candidats.append({"texte": t, "url": url, "titre": titre, "source": "sinistre"})

        for faq in page.get("faqs",[]):
            q = nettoyer(faq.get("question",""))
            r = nettoyer(faq.get("reponse",""))
            if q and r:
                candidats.append({"texte": f"Question : {q} Réponse : {r}", "url": url, "titre": titre, "source": "faq"})

    return candidats

# ─────────────────────────────────────────
# Détection automatique du bruit (TF-IDF)
# ─────────────────────────────────────────
def detecter_bruit_tfidf(candidats, seuil_longueur=10):
    textes = [c["texte"] for c in candidats]
    vectorizer = TfidfVectorizer(max_df=0.85, min_df=1, ngram_range=(1,2), strip_accents=None)
    try:
        tfidf_matrix = vectorizer.fit_transform(textes)
    except ValueError:
        return candidats, []

    scores       = np.asarray(tfidf_matrix.mean(axis=1)).flatten()
    scores_tries = np.sort(scores)
    diffs        = np.diff(scores_tries)
    idx_saut     = np.argmax(diffs[:len(diffs)//2])
    seuil_auto   = scores_tries[idx_saut + 1]

    utiles, bruits = [], []
    for i, c in enumerate(candidats):
        if scores[i] <= seuil_auto or len(c["texte"].split()) < seuil_longueur:
            bruits.append(c)
        else:
            utiles.append(c)

    print(f"  🔍 Seuil TF-IDF auto : {seuil_auto:.5f} | Utiles : {len(utiles)} | Bruit : {len(bruits)}")
    return utiles, bruits

# ─────────────────────────────────────────
# Construction des chunks
# ─────────────────────────────────────────
def construire_chunks(candidats_utiles):
    tous_chunks, vus, groupes, singles = [], set(), {}, []

    for c in candidats_utiles:
        if c["source"] in ("garanties", "avantages", "sinistre"):
            groupes.setdefault((c["url"], c["source"], c["titre"]), []).append(c["texte"])
        else:
            singles.append(c)

    for c in singles:
        for chunk in decouper(c["texte"], c["url"], c["titre"], c["source"]):
            cle = chunk["texte"][:150]
            if cle not in vus:
                vus.add(cle)
                tous_chunks.append(chunk)

    for (url, source, titre), textes in groupes.items():
        for chunk in decouper(" | ".join(textes), url, titre, source):
            cle = chunk["texte"][:150]
            if cle not in vus:
                vus.add(cle)
                tous_chunks.append(chunk)

    return tous_chunks

# ─────────────────────────────────────────
# Mise à jour ChromaDB
# ─────────────────────────────────────────
def mettre_a_jour_chromadb(chunks):
    print(f"  🔄 Mise à jour ChromaDB avec {len(chunks)} chunks...")
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    textes     = [c["texte"] for c in chunks]
    ids        = [f"chunk_{i}" for i in range(len(chunks))]
    metas      = [{"url": c["url"], "titre": c["titre"], "source": c["source"]} for c in chunks]
    embeddings = model.encode(textes, show_progress_bar=False).tolist()
    collection.add(documents=textes, embeddings=embeddings, metadatas=metas, ids=ids)
    print(f"  ✅ ChromaDB mis à jour — {len(chunks)} chunks indexés !")

# ─────────────────────────────────────────
# Tâche planifiée complète
# ─────────────────────────────────────────
def tache_mise_a_jour():
    try:
        pages     = scraper_site()
        candidats = extraire_candidats(pages)
        utiles, _ = detecter_bruit_tfidf(candidats)
        chunks    = construire_chunks(utiles)
        mettre_a_jour_chromadb(chunks)

        with open("astree_data.json", "w", encoding="utf-8") as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)
        with open("astree_chunks.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        print(f"  🎉 Mise à jour terminée — {len(chunks)} chunks indexés")

    except Exception as e:
        print(f"  ❌ Erreur lors de la mise à jour : {e}")

# ─────────────────────────────────────────
# Scheduler : 10h00 et 18h00
# ─────────────────────────────────────────
scheduler = BackgroundScheduler()
scheduler.add_job(tache_mise_a_jour, "cron", hour=10, minute=0)
scheduler.add_job(tache_mise_a_jour, "cron", hour=18, minute=0)
scheduler.start()
print("⏰ Scheduler actif — mise à jour automatique à 10h00 et 18h00")

# ─────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────
app = FastAPI(title="Astree RAG Service")

class MessageHistorique(BaseModel):
    role: str
    text: str

class Question(BaseModel):
    message: str
    historique: Optional[List[MessageHistorique]] = []

# ─────────────────────────────────────────
# 1. Détection de langue
# ─────────────────────────────────────────
def detecter_langue(texte):
    """Détecte automatiquement la langue : français, anglais ou arabe."""
    try:
        langue = detect(texte)
        if langue == "ar":   return "arabe"
        elif langue == "en": return "anglais"
        else:                return "français"
    except:
        return "français"

def prompt_selon_langue(langue):
    """Retourne le prompt système dans la bonne langue."""
    if langue == "arabe":
        return """أنت المساعد الافتراضي لشركة أسترى للتأمين (تونس).
أجب فقط بناءً على المعلومات الواردة في السياق.
إذا لم تجد المعلومة، قل: "لا أملك هذه المعلومة، يرجى الاتصال بأسترى على الرقم +216 71 104 555"
القواعد: أجب في 2-3 جمل كحد أقصى، بشكل مهني ومباشر."""
    elif langue == "anglais":
        return """You are the virtual assistant of Astrée Insurance (Tunisia).
Answer ONLY from the information provided in the context.
If the information is not available, say: "I don't have this information. Please contact Astrée at +216 71 104 555"
Rules: Maximum 3 sentences, professional and direct."""
    else:
        return """Tu es l'assistant virtuel d'Astrée Assurances (Tunisie).
Réponds UNIQUEMENT à partir des informations fournies dans le contexte.
Si l'information n'est pas dans le contexte, dis :
"Je n'ai pas cette information, contactez Astrée au +216 71 104 555."
Règles strictes :
- Maximum 3 phrases par réponse
- Sois direct et précis
- Ne jamais inventer de détails
- Langue : français professionnel"""

# ─────────────────────────────────────────
# 2. Traduction en français pour la recherche
# ─────────────────────────────────────────
def traduire_en_francais(question):
    """Traduit une question en français pour la recherche dans ChromaDB."""
    try:
        completion = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Traduis cette question en français, réponds UNIQUEMENT avec la traduction : {question}"}],
            temperature=0.1,
            max_tokens=100
        )
        traduit = completion.choices[0].message.content.strip()
        print(f"  🔄 Traduit pour recherche : {traduit}")
        return traduit
    except:
        return question

# ─────────────────────────────────────────
# 3. Reformulation automatique des questions floues
# ─────────────────────────────────────────
def reformuler_question(question, historique=[]):
    """
    Reformule automatiquement une question floue ou trop courte
    en utilisant l'historique de conversation.
    """
    mots = question.strip().split()
    est_flou = (
        len(mots) <= 3 or
        any(mot in question.lower() for mot in ["ça", "ca", "cela", "celui", "celle", "et après", "comment ça", "précise", "plus"])
    )

    if not est_flou or not historique:
        return question

    historique_texte = "\n".join([
        f"{'Utilisateur' if h.role == 'user' else 'Assistant'}: {h.text}"
        for h in historique[-4:]
    ])

    prompt_reformulation = f"""Voici une conversation :
{historique_texte}
Utilisateur: {question}

La dernière question est floue. Reformule-la en une question claire et complète
en tenant compte du contexte de la conversation.
Réponds UNIQUEMENT avec la question reformulée, rien d'autre."""

    try:
        completion = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_reformulation}],
            temperature=0.1,
            max_tokens=100
        )
        question_reformulee = completion.choices[0].message.content.strip()
        print(f"  🔄 Reformulée : '{question}' → '{question_reformulee}'")
        return question_reformulee
    except:
        return question

# ─────────────────────────────────────────
# 4. Retrieval + Reranking
# ─────────────────────────────────────────
def rechercher_et_reranker(question, n_retrieve=8, n_final=4):
    """
    Étape 1 — Retrieval : récupère les 8 chunks les plus proches (embedding)
    Étape 2 — Reranking : le CrossEncoder retrie par pertinence réelle
    Étape 3 — Garde les 4 meilleurs chunks
    """
    vecteur   = model.encode(question).tolist()
    resultats = collection.query(
        query_embeddings=[vecteur],
        n_results=n_retrieve,
        include=["documents", "metadatas"]
    )

    chunks = resultats["documents"][0]
    metas  = resultats["metadatas"][0]

    if not chunks:
        return "", []

    paires           = [(question, chunk) for chunk in chunks]
    scores_reranking = reranker.predict(paires)

    resultats_tries = sorted(
        zip(chunks, metas, scores_reranking),
        key=lambda x: x[2],
        reverse=True
    )[:n_final]

    contexte, sources, urls_vus = "", [], set()
    for chunk, meta, score in resultats_tries:
        print(f"  📊 Score reranking : {score:.3f} | {meta['titre']}")
        contexte += f"\n---\n[Source: {meta['titre']}]\n{chunk}\n"
        if meta["url"] not in urls_vus:
            sources.append({"titre": meta["titre"], "url": meta["url"]})
            urls_vus.add(meta["url"])

    return contexte, sources

# ─────────────────────────────────────────
# 5. Génération avec mémoire + langue
# ─────────────────────────────────────────
def generer_reponse(question, contexte, historique=[], langue="français"):
    """Génère une réponse courte avec mémoire et prompt adapté à la langue."""
    system_prompt = prompt_selon_langue(langue)
    messages = [{"role": "system", "content": system_prompt}]

    for h in historique[-5:]:
        messages.append({"role": h.role, "content": h.text})

    messages.append({
        "role": "user",
        "content": f"""Contexte extrait du site Astrée Assurances :
{contexte if contexte else "Aucun contexte pertinent trouvé."}

Question : {question}

IMPORTANT : Réponds OBLIGATOIREMENT en {langue}, 2-3 phrases maximum."""
    })

    completion = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        max_tokens=200,
        top_p=0.9,
    )
    return completion.choices[0].message.content.strip()

# ─────────────────────────────────────────
# Routes FastAPI
# ─────────────────────────────────────────
@app.post("/rag")
def rag_endpoint(payload: Question):
    try:
        question_originale = payload.message.strip()
        if not question_originale:
            return {"error": "Question vide"}

        historique = payload.historique or []

        # 1. Détection de langue
        langue = detecter_langue(question_originale)
        print(f"  🌐 Langue détectée : {langue}")

        # 2. Traduire en français si nécessaire pour la recherche
        question_recherche = question_originale
        if langue in ["anglais", "arabe"]:
            question_recherche = traduire_en_francais(question_originale)

        # 3. Reformulation si question floue
        question_recherche = reformuler_question(question_recherche, historique)

        # 4. Retrieval + Reranking (sur la question en français)
        contexte, sources = rechercher_et_reranker(question_recherche)

        # 5. Génération (dans la langue originale)
        reponse = generer_reponse(question_originale, contexte, historique, langue)

        return {"reponse": reponse, "sources": sources}

    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok", "chunks": collection.count()}

@app.post("/refresh")
def refresh_manuel():
    """Déclenche une mise à jour manuelle immédiate."""
    try:
        tache_mise_a_jour()
        return {"status": "ok", "message": "Mise à jour effectuée", "chunks": collection.count()}
    except Exception as e:
        return {"error": str(e)}