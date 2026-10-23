"""Marchés IT : veille quotidienne des appels d'offres publics en informatique et web.

1. Lit les avis récents du BOAMP (open data DILA, licence ouverte) et garde ceux qui touchent
   à l'informatique : descripteurs BOAMP et mots-clés de l'objet.
2. Les range par catégorie dans data/annonces.json (90 jours glissants).
3. Envoie aux abonnés les avis vus pour la première fois aujourd'hui, filtrés par leurs
   départements et catégories (secret ABONNES, jamais écrit dans le dépôt).
4. Régénère le site public (tools/site.py), qui montre les avis avec 3 jours de retard.

Usage, depuis la racine : python3 tools/veille.py [--sans-envoi]
"""
import datetime as dt
import json
import os
import smtplib
import ssl
import sys
import unicodedata
import urllib.parse
import urllib.request
from email.message import EmailMessage

import site_public

API = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
DONNEES = "data/annonces.json"
JOURS_GARDES = 90
FENETRE = int(os.environ.get("FENETRE", 4))  # jours relus à chaque passage, pour rattraper une publication tardive
CHAMPS = "idweb,objet,nomacheteur,code_departement,datelimitereponse,dateparution,url_avis,type_marche,procedure_libelle,descripteur_libelle"
DESCRIPTEURS = ["Informatique (prestations de services)", "Logiciel", "Progiciel", "Informatique (matériel)",
                "Informatique (maintenance serveurs et réseaux)", "Télécommunications"]
# Recherche plein texte côté BOAMP : seulement des termes sans ambiguïté (« développement » ou
# « hébergement » seuls ramènent du développement économique et de l'hébergement touristique).
MOTS_OBJET = ["site internet", "site web", "informatique", "logiciel", "progiciel", "SaaS", "cybersécurité", "infogérance",
              "intranet", "application mobile", "application web", "applicatif", "applicative", "TMA", "Microsoft 365",
              "serveur", "serveurs", "datacenter", "cloud", "téléphonie", "numérique", "ordinateurs", "dématérialisation"]
# Les mêmes, sans accents, pour accepter un avis qui n'a pas de descripteur informatique.
FORTS = ["site internet", "site web", "informatique", "logiciel", "progiciel", "saas", "cybersecurite", "infogerance",
         "intranet", "extranet", "application mobile", "application web", "applicatif", "applicative", " tma", "microsoft 365",
         "serveur", "datacenter", "cloud", "telephonie", "numerique", "ordinateur", "dematerialisation"]

# Catégories dans l'ordre de priorité : la première qui correspond l'emporte.
CATEGORIES = [
    ("web", "Sites et applications", ["site internet", "site web", "portail web", "portail internet", "application mobile", "application web",
                                      "intranet", "extranet", " tma ", "maintenance applicative", "applicatif", "developpement informatique",
                                      "developpement logiciel", "developpement web", "refonte du site", "accessibilite numerique", "plateforme numerique", "plateforme web"]),
    ("cyber", "Cybersécurité", ["cybersecurite", "securite informatique", "securite des systemes d'information", " ssi ", "pentest",
                                "test d'intrusion", "tests d'intrusion", "audit de securite"]),
    ("logiciel", "Logiciels et SaaS", ["logiciel", "progiciel", "saas", "licence", "erp", " ged ", "dematerialisation", "microsoft 365"]),
    ("infra", "Infrastructure et hébergement", ["serveur", "hebergement informatique", "hebergement de donnees", "hebergement web", "stockage",
                                                "cloud", "infogerance", "sauvegarde", "datacenter", "virtualisation", "messagerie",
                                                "maintenance informatique", "infrastructure informatique", "systeme d'information", "systemes d'information"]),
    ("materiel", "Matériel", ["materiel informatique", "materiels informatiques", "ordinateur", "poste de travail", "postes de travail",
                              "tablette", "ecran", "imprimante", "equipements numeriques", "materiels numeriques", "copieur", "photocopieur"]),
    ("telecom", "Télécoms", ["telephonie", "telecommunication", "fibre optique", "acces internet", "acces a internet", "reseau informatique",
                             "reseaux informatiques", "wifi", "wi-fi", "operateur"]),
]
NOMS_CATEGORIES = {c: n for c, n, _ in CATEGORIES}
# Descripteurs BOAMP sans mot-clé reconnu dans l'objet.
PAR_DESCRIPTEUR = {"Logiciel": "logiciel", "Progiciel": "logiciel", "Informatique (matériel)": "materiel",
                   "Informatique (maintenance serveurs et réseaux)": "infra", "Télécommunications": "telecom",
                   "Informatique (prestations de services)": "web"}


def sans_accents(texte):
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower()) if unicodedata.category(c) != "Mn")


def categorie(objet, descripteurs):
    texte = " " + sans_accents(objet) + " "
    for code, _, mots in CATEGORIES:
        if any(m in texte for m in mots):
            return code
    for d in descripteurs or []:
        if d in PAR_DESCRIPTEUR:
            return PAR_DESCRIPTEUR[d]
    return None


def lire_boamp(depuis):
    descripteurs = ",".join(json.dumps(d, ensure_ascii=False) for d in DESCRIPTEURS)
    mots = " or ".join(f'search(objet,{json.dumps(m, ensure_ascii=False)})' for m in MOTS_OBJET)
    where = f"dateparution>=date'{depuis}' and nature=\"APPEL_OFFRE\" and (descripteur_libelle in ({descripteurs}) or {mots})"
    avis, offset = [], 0
    while True:
        params = urllib.parse.urlencode({"where": where, "select": CHAMPS, "limit": 100, "offset": offset, "order_by": "dateparution desc"})
        with urllib.request.urlopen(f"{API}?{params}", timeout=60) as reponse:
            page = json.load(reponse)
        avis += page["results"]
        offset += 100
        if offset >= page["total_count"] or offset >= 1000:
            return avis


def nettoyer(r, aujourdhui):
    texte = " " + sans_accents(r["objet"] or "") + " "
    descripteur = bool(set(r.get("descripteur_libelle") or []) & set(DESCRIPTEURS))
    if not descripteur and not any(m in texte for m in FORTS):
        return None
    if not descripteur and any(m in texte for m in ["travaux", "voirie", "nettoyage", "restauration", "formation", "hebergement des"]):
        return None
    cat = categorie(r["objet"] or "", r.get("descripteur_libelle"))
    if not cat:
        return None
    return {
        "id": r["idweb"], "objet": " ".join((r["objet"] or "").split()), "acheteur": r["nomacheteur"] or "",
        "departements": r.get("code_departement") or [], "parution": (r["dateparution"] or "")[:10],
        "limite": (r.get("datelimitereponse") or "")[:16], "url": r.get("url_avis") or f"https://www.boamp.fr/pages/avis/?q=idweb:{r['idweb']}",
        "type": ", ".join(t.capitalize() for t in (r.get("type_marche") or [])), "procedure": r.get("procedure_libelle") or "",
        "categorie": cat, "vu_le": aujourdhui,
    }


def charger():
    try:
        return json.load(open(DONNEES, encoding="utf-8"))
    except FileNotFoundError:
        return {}


def corps_mail(avis, abonne):
    lignes = []
    for cat, nom, _ in CATEGORIES:
        du_lot = [a for a in avis if a["categorie"] == cat]
        if not du_lot:
            continue
        lignes.append(f'<h2 style="font-size:17px;margin:22px 0 6px">{nom} ({len(du_lot)})</h2>')
        for a in du_lot:
            limite = dt.datetime.fromisoformat(a["limite"]).strftime("%d/%m/%Y à %H:%M") if a["limite"] else "non précisée"
            lignes.append(
                f'<p style="margin:0 0 12px"><a href="{a["url"]}" style="color:#1F5FD1;font-weight:600">{a["objet"]}</a><br>'
                f'<span style="color:#555;font-size:14px">{a["acheteur"]} · {", ".join(a["departements"]) or "France"} · réponse avant le {limite}</span></p>')
    filtres = []
    if abonne.get("departements"):
        filtres.append("départements " + ", ".join(abonne["departements"]))
    if abonne.get("categories"):
        filtres.append(", ".join(NOMS_CATEGORIES[c].lower() for c in abonne["categories"] if c in NOMS_CATEGORIES))
    return (f'<div style="font-family:-apple-system,Segoe UI,sans-serif;max-width:640px;color:#111">'
            f'<p>{len(avis)} nouvel{"s" if len(avis) > 1 else ""} appel{"s" if len(avis) > 1 else ""} d\'offres '
            f'{"pour tes critères (" + " ; ".join(filtres) + ")" if filtres else "en informatique et web"}.</p>{"".join(lignes)}'
            f'<p style="color:#777;font-size:12px;margin-top:28px">Marchés IT · source : BOAMP (DILA), licence ouverte. '
            f'Pour changer tes critères ou te désabonner, réponds simplement à ce message.</p></div>')


def envoyer(nouveaux):
    abonnes = json.loads(os.environ.get("ABONNES") or "[]")
    expediteur, mot_de_passe = os.environ.get("GMAIL_EXPEDITEUR"), os.environ.get("GMAIL_APP_PASSWORD")
    if not abonnes or not expediteur or not mot_de_passe:
        print("Envoi ignoré : pas d'abonné ou pas d'identifiants Gmail.")
        return
    jour = dt.date.today().strftime("%d/%m")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as serveur:
        serveur.login(expediteur, mot_de_passe)
        for abonne in abonnes:
            deps, cats = set(abonne.get("departements") or []), set(abonne.get("categories") or [])
            siens = [a for a in nouveaux if (not deps or deps & set(a["departements"]) or not a["departements"])
                     and (not cats or a["categorie"] in cats)]
            if not siens:
                continue
            message = EmailMessage()
            message["Subject"] = f"{len(siens)} appel{'s' if len(siens) > 1 else ''} d'offres informatique · {jour}"
            message["From"] = f"Marchés IT <{expediteur}>"
            message["To"] = abonne["email"]
            message.set_content("Ouvre ce message dans un client qui affiche le HTML.")
            message.add_alternative(corps_mail(siens, abonne), subtype="html")
            serveur.send_message(message)
            print(f"Envoyé : {len(siens)} avis à un abonné.")


def main():
    aujourdhui = dt.date.today().isoformat()
    depuis = (dt.date.today() - dt.timedelta(days=FENETRE)).isoformat()
    base = charger()
    nouveaux = []
    for r in lire_boamp(depuis):
        a = nettoyer(r, aujourdhui)
        if a and a["id"] not in base:
            base[a["id"]] = a
            nouveaux.append(a)
    limite = (dt.date.today() - dt.timedelta(days=JOURS_GARDES)).isoformat()
    base = {k: v for k, v in sorted(base.items(), key=lambda kv: kv[1]["parution"], reverse=True) if v["parution"] >= limite}
    os.makedirs("data", exist_ok=True)
    json.dump(base, open(DONNEES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(nouveaux)} nouveaux avis, {len(base)} en base.")
    if nouveaux and "--sans-envoi" not in sys.argv:
        envoyer(sorted(nouveaux, key=lambda a: a["limite"] or "9999"))
    site_public.generer(list(base.values()), CATEGORIES)


if __name__ == "__main__":
    main()
