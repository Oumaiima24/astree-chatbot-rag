import json
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# ─────────────────────────────────────────
# Charger les données
# ─────────────────────────────────────────
with open("astree_data.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

print(f" Pages chargées : {len(pages)}")

# ─────────────────────────────────────────
# Fonctions utilitaires
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
# Étape 1 — Extraire tous les textes candidats
# ─────────────────────────────────────────
def extraire_candidats(pages):
    candidats = []
    for page in pages:
        if "erreur" in page: continue
        url, titre = page.get("url",""), page.get("titre","")

        desc = nettoyer(page.get("description",""))
        if desc: candidats.append({"texte": desc, "url": url, "titre": titre, "source": "description"})

        intro = page.get("introduction",{})
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
# Étape 2 — Détecter le bruit avec TF-IDF
# ─────────────────────────────────────────
def detecter_bruit_tfidf(candidats, seuil_longueur=10):
    """
    Détecte automatiquement les textes de navigation/bruit.
    
    Principe :
    - TF-IDF calcule l'importance de chaque mot dans un texte par rapport au corpus
    - Un mot présent dans presque tous les textes (navigation) a un score TF-IDF bas
    - Un texte dont le score moyen est très bas = bruit de navigation
    - Le seuil est calculé automatiquement via un saut naturel dans la distribution
    """
    textes = [c["texte"] for c in candidats]

    vectorizer = TfidfVectorizer(
        max_df=0.85,
        min_df=1,
        ngram_range=(1, 2),
        strip_accents=None,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(textes)
    except ValueError:
        print("  TF-IDF : corpus trop petit, on garde tout")
        return candidats, []

    scores = np.asarray(tfidf_matrix.mean(axis=1)).flatten()

    # Seuil automatique : saut naturel dans la distribution
    # On trie les scores et on cherche le plus grand écart
    scores_tries = np.sort(scores)
    diffs = np.diff(scores_tries)
    idx_saut = np.argmax(diffs[:len(diffs)//2])  # chercher dans la première moitié
    seuil_auto = scores_tries[idx_saut + 1]

    print(f"\n   Seuil automatique détecté : {seuil_auto:.5f}")
    print(f"   (plus grand saut naturel dans la distribution des scores)")

    utiles, bruits = [], []
    for i, c in enumerate(candidats):
        nb_mots = len(c["texte"].split())
        if scores[i] <= seuil_auto or nb_mots < seuil_longueur:
            bruits.append(c)
        else:
            utiles.append(c)

    return utiles, bruits

# ─────────────────────────────────────────
# Étape 3 — Construire les chunks finaux
# ─────────────────────────────────────────
def construire_chunks(candidats_utiles):
    tous_chunks, vus = [], set()
    groupes = {}
    singles = []

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
# Pipeline principal
# ─────────────────────────────────────────
print("\n Étape 1 — Extraction des candidats...")
candidats = extraire_candidats(pages)
print(f"   {len(candidats)} textes candidats extraits")

print("\n Étape 2 — Détection automatique du bruit (TF-IDF)...")
utiles, bruits = detecter_bruit_tfidf(candidats, seuil_longueur=10)
print(f"\n    Textes utiles  : {len(utiles)}")
print(f"     Textes bruit   : {len(bruits)}")

print(f"\n  Exemples de textes filtrés automatiquement :")
for b in bruits[:5]:
    print(f"   [{b['source']}] {b['texte'][:100]}")

print("\n Étape 3 — Construction des chunks...")
chunks = construire_chunks(utiles)

with open("astree_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

sources   = Counter(c["source"] for c in chunks)
longueurs = [len(c["texte"].split()) for c in chunks]

print(f"\n Résumé final :")
print(f"   Chunks finaux    : {len(chunks)}")
print(f"\n Par source :")
for s, n in sources.most_common():
    print(f"   {s:<20} : {n}")
print(f"\n📏 Longueur :")
print(f"   Moyenne : {sum(longueurs)//len(longueurs)} mots")
print(f"   Min     : {min(longueurs)} mots")
print(f"   Max     : {max(longueurs)} mots")
print(f"\n astree_chunks.json prêt pour la vectorisation !")