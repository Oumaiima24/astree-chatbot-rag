import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import json
import time
import urllib3

# ─────────────────────────────────────────
# Désactiver les warnings SSL
# ─────────────────────────────────────────
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────────────────────
# Session avec retry automatique
# ─────────────────────────────────────────
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

# ─────────────────────────────────────────
# URLs à scraper
# ─────────────────────────────────────────
urls = [
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

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

results = []

for url in urls:
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        response.encoding = "utf-8"
        print(f" {response.status_code} | {url}")
        soup = BeautifulSoup(response.text, "html.parser")

        # ── Titre H1 ──────────────────────────────
        h1 = soup.find("h1")
        titre = h1.get_text(strip=True) if h1 else None

        # ── Meta description ──────────────────────
        meta = soup.find("meta", attrs={"name": "description"})
        description = meta["content"].strip() if meta and meta.get("content") else None

        # ── Téléphone ──────────────────────────────
        tel = soup.find("a", href=lambda x: isinstance(x, str) and x.startswith("tel:"))
        telephone = tel["href"].replace("tel:", "").strip() if tel else None

        # ── Introduction (desc1 / desc2) ──────────
        desc1 = soup.find("div", class_="desc1")
        desc2 = soup.find("div", class_="desc2")

        # ── Garanties / Onglets ────────────────────
        garanties = []
        for tab in soup.find_all("div", class_="tab-pane"):
            texte_tab = tab.get_text(" ", strip=True)
            if texte_tab:
                garanties.append({"id": tab.get("id"), "texte": texte_tab})

        # ── Avantages ──────────────────────────────
        avantages = []
        for item in soup.find_all("div", class_="item-avantage"):
            titre_av   = item.find("div", class_="title-avantage")
            contenu_av = item.find("div", class_="contenu-avantage")
            avantages.append({
                "titre":   titre_av.get_text(strip=True)   if titre_av   else None,
                "contenu": contenu_av.get_text(strip=True) if contenu_av else None
            })

        # ── Sinistre (procédure de déclaration) ───
        sinistre = []
        for block in soup.find_all("div", class_=lambda c: c and "sinistre" in c.lower()):
            titre_s = block.find(["h2", "h3", "h4"])
            texte_s = block.get_text(" ", strip=True)
            if texte_s:
                sinistre.append({
                    "titre": titre_s.get_text(strip=True) if titre_s else None,
                    "texte": texte_s
                })

        # ── Cards (blocs produits liés) ────────────
        cards = []
        for card in soup.find_all("div", class_=lambda c: c and "card" in c.lower()):
            titre_c = card.find(["h2", "h3", "h4", "h5"])
            contenu_c = card.get_text(" ", strip=True)
            if contenu_c:
                cards.append({
                    "titre": titre_c.get_text(strip=True) if titre_c else "",
                    "contenu": contenu_c
                })

        # ── FAQ ─────────────────────────────────────
        faqs = []
        questions = soup.find_all("div", class_="views-accordion-header")
        reponses  = soup.find_all("div", class_="views-field-body")
        for q, r in zip(questions, reponses):
            qt = q.get_text(strip=True)
            if qt:
                faqs.append({"question": qt, "reponse": r.get_text(strip=True)})

        # ── Assemblage du résultat ─────────────────
        data = {
            "url":           url,
            "titre":         titre,
            "description":   description,
            "telephone":     telephone,
            "date_scraping": time.strftime("%Y-%m-%d"),
            "introduction": {
                "desc1": desc1.get_text(" ", strip=True) if desc1 else None,
                "desc2": desc2.get_text(" ", strip=True) if desc2 else None
            },
            "garanties": garanties,
            "avantages": avantages,
            "sinistre":  sinistre,
            "cards":     cards,
            "faqs":      faqs,
        }

        results.append(data)
        time.sleep(2)

    except requests.exceptions.Timeout:
        print(f" TIMEOUT | {url}")
        results.append({"url": url, "erreur": "Timeout après 30 secondes"})

    except requests.exceptions.HTTPError as e:
        print(f" HTTP {e.response.status_code} | {url}")
        results.append({"url": url, "erreur": f"HTTP {e.response.status_code}"})

    except requests.exceptions.ConnectionError:
        print(f" CONNEXION ÉCHOUÉE | {url}")
        results.append({"url": url, "erreur": "Erreur de connexion"})

    except Exception as e:
        print(f" ERREUR INATTENDUE | {url} → {e}")
        results.append({"url": url, "erreur": str(e)})

# ─────────────────────────────────────────
# Sauvegarde JSON
# ─────────────────────────────────────────
output_file = "astree_data_v3.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────
# Résumé final
# ─────────────────────────────────────────
succes = sum(1 for r in results if "erreur" not in r)
echecs = len(results) - succes

print(f"\n Fichier '{output_file}' généré avec succès !")
print(f"   Pages récupérées : {succes}/{len(urls)}")
if echecs:
    print(f"   Pages en erreur  : {echecs}")
    for r in results:
        if "erreur" in r:
            print(f"     {r['url']} → {r['erreur']}")