"""Site public de Marchés IT : page de vente et une page par catégorie, régénérées à chaque veille.

Les avis n'apparaissent ici que 3 jours après leur parution : les abonnés les reçoivent le matin même.
"""
import datetime as dt
import html
import json

BASE = "https://komorebideuxiemedunom.github.io/marches-it/"
RETARD = 3
PRIX = "19 €"
CONTACT = ("mailto:inceept@gmail.com?subject=" + "Essai%20gratuit%20March%C3%A9s%20IT"
           + "&body=" + "Bonjour%2C%0A%0AJe%20veux%20essayer%20March%C3%A9s%20IT%20pendant%2014%20jours.%0A%0AD%C3%A9partements%20(ou%20%C2%AB%20toute%20la%20France%20%C2%BB)%20%3A%20%0ACat%C3%A9gories%20(sites%20et%20applications%2C%20logiciels%2C%20infrastructure%2C%20cybers%C3%A9curit%C3%A9%2C%20mat%C3%A9riel%2C%20t%C3%A9l%C3%A9coms%2C%20ou%20%C2%AB%20toutes%20%C2%BB)%20%3A%20%0AEntreprise%20%3A%20%0A")
HEAD = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"><meta name="referrer" content="no-referrer"><meta name="viewport" content="width=device-width,initial-scale=1">"""
STYLE = """<style>
:root{--bg:#F6F6F3;--ink:#16181C;--muted:#5E636B;--card:#fff;--accent:#1F5FD1;--line:rgba(0,0,0,.09)}
@media (prefers-color-scheme:dark){:root{--bg:#0F1013;--ink:#ECEADF;--muted:#A3A39A;--card:#1A1B20;--accent:#7AA7FF;--line:rgba(255,255,255,.09)}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:760px;margin:0 auto;padding:44px 20px}h1{font-size:34px;line-height:1.2;margin:8px 0 10px}h2{font-size:21px;margin-top:34px}
p,li{color:var(--muted)}a{color:var(--accent)}.marque{font-weight:700;letter-spacing:.02em;color:var(--ink);text-decoration:none}
.card{background:var(--card);border-radius:18px;padding:18px 20px;margin:20px 0;box-shadow:0 4px 16px rgba(0,0,0,.05)}
.chiffres{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;text-align:center}.chiffres p{margin:0;font-size:14px}
.chiffres strong{display:block;font-size:30px;color:var(--ink)}
.cta{background:var(--accent);border-radius:18px;padding:20px 22px;margin:26px 0}.cta p,.cta strong{color:#fff}
.btn{display:inline-block;background:#fff;color:#1F5FD1;font-weight:700;border-radius:12px;padding:11px 18px;text-decoration:none;margin-top:4px}
.avis{border-top:1px solid var(--line);padding:10px 0}.avis a{font-weight:600}.avis small{display:block;color:var(--muted);font-size:14px}
.cats{font-size:15px;line-height:2}.note{font-size:13px}footer{margin-top:40px;font-size:14px;color:var(--muted)}
@media (max-width:560px){.chiffres{grid-template-columns:1fr}}
</style>"""


def esc(v):
    return html.escape(str(v), quote=True)


def date_fr(iso):
    return dt.date.fromisoformat(iso[:10]).strftime("%d/%m/%Y")


def bloc_avis(avis):
    out = []
    for a in avis:
        lieu = ", ".join(a["departements"][:4]) + ("…" if len(a["departements"]) > 4 else "") if a["departements"] else "France"
        limite = f" · réponse avant le {date_fr(a['limite'])}" if a["limite"] else ""
        out.append(f'<div class="avis"><a href="{esc(a["url"])}" rel="nofollow">{esc(a["objet"])}</a>'
                   f'<small>{esc(a["acheteur"])} · {esc(lieu)} · publié le {date_fr(a["parution"])}{limite}</small></div>')
    return "".join(out)


def page(chemin, titre, description, corps, faq=()):
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]} if faq else None
    doc = (f'{HEAD}\n<title>{esc(titre)}</title>\n<meta name="description" content="{esc(description)}">\n'
           f'<link rel="canonical" href="{BASE}{"" if chemin == "index.html" else chemin}">{STYLE}'
           + (f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else "")
           + f'</head>\n<body><main><a class="marque" href="index.html">Marchés IT</a>\n{corps}\n'
           + "".join(f"<h2>{esc(q)}</h2><p>{esc(r)}</p>" for q, r in faq)
           + '\n<footer>Source : BOAMP, Direction de l\'information légale et administrative, licence ouverte. '
           'Marchés IT n\'est pas affilié au BOAMP. · <a href="mailto:inceept@gmail.com?subject=March%C3%A9s%20IT">Contact</a> · © 2026 Lucas Dansac</footer></main></body></html>\n')
    open(chemin, "w", encoding="utf-8").write(doc)


def cta(texte):
    return (f'<div class="cta"><p><strong>{texte}</strong> Chaque matin, les nouveaux appels d\'offres de tes départements et de ton métier, '
            f'avec l\'acheteur et la date limite, sans aller fouiller le BOAMP. {PRIX} par mois, sans engagement.</p>'
            f'<a class="btn" href="{CONTACT}">Essayer 14 jours gratuitement</a></div>')


def generer(avis, categories):
    aujourdhui = dt.date.today()
    visible = (aujourdhui - dt.timedelta(days=RETARD)).isoformat()
    semaine = (aujourdhui - dt.timedelta(days=7)).isoformat()
    publics = sorted([a for a in avis if a["parution"] <= visible], key=lambda a: a["parution"], reverse=True)
    recents = [a for a in avis if a["parution"] > visible]
    par_semaine = len([a for a in avis if a["parution"] > semaine])
    ouverts = len([a for a in avis if a["limite"] and a["limite"][:10] >= aujourdhui.isoformat()])
    liens_cats = " · ".join(f'<a href="appels-offres-{c}.html">{n}</a>' for c, n, _ in categories)

    faq = [
        ("Où trouver les appels d'offres publics en informatique ?",
         "Ils sont publiés au BOAMP (Bulletin officiel des annonces des marchés publics) et, au-delà des seuils européens, au JOUE. Marchés IT relit le BOAMP chaque matin et ne garde que ce qui touche à l'informatique : sites et applications, logiciels, infrastructure, cybersécurité, matériel et télécoms."),
        ("Pourquoi les avis de cette page ont-ils 3 jours de retard ?",
         "La page publique sert d'aperçu. Les abonnés reçoivent les nouveaux avis le matin de leur parution, filtrés par département et par catégorie : ça laisse plusieurs jours de plus pour préparer une réponse."),
        ("Combien coûte l'abonnement ?",
         f"{PRIX} par mois, sans engagement, après 14 jours d'essai gratuit. Un seul marché remporté le rembourse pour des années."),
        ("Une petite entreprise ou un indépendant peut-il répondre ?",
         "Oui. Beaucoup de marchés informatiques sont des procédures adaptées (MAPA), ouvertes aux TPE et aux indépendants, parfois découpées en lots. On peut aussi répondre en groupement avec d'autres entreprises."),
    ]
    corps = (f'<h1>Les appels d\'offres publics en informatique et web, chaque matin</h1>'
             f'<p>Sites internet, applications, logiciels, hébergement, cybersécurité, matériel : Marchés IT relit le BOAMP tous les jours '
             f'et t\'envoie seulement les marchés de ton métier, dans tes départements.</p>'
             f'<div class="card chiffres"><p><strong>{par_semaine}</strong>avis informatiques publiés ces 7 derniers jours</p>'
             f'<p><strong>{ouverts}</strong>marchés encore ouverts aux réponses</p><p><strong>{len(recents)}</strong>avis récents réservés aux abonnés</p></div>'
             + cta("Ne rate plus un marché.")
             + f'<h2>Par catégorie</h2><p class="cats">{liens_cats}</p>'
             f'<h2>Derniers avis publics</h2><p class="note">Avis publiés il y a au moins {RETARD} jours. Les abonnés les ont reçus le jour même.</p>'
             f'{bloc_avis(publics[:40])}')
    page("index.html", "Appels d'offres informatique et web : veille quotidienne du BOAMP | Marchés IT",
         f"Chaque matin, les nouveaux appels d'offres publics en informatique, sites web, logiciels, cybersécurité et matériel, filtrés par département. {par_semaine} avis cette semaine. Essai gratuit 14 jours.",
         corps, faq)

    for code, nom, _ in categories:
        du_lot = [a for a in publics if a["categorie"] == code]
        attente = len([a for a in recents if a["categorie"] == code])
        corps = (f'<h1>Appels d\'offres : {nom.lower()}</h1>'
                 f'<p>Les marchés publics récents de la catégorie « {nom} », relevés au BOAMP. {attente} avis plus récents sont réservés aux abonnés.</p>'
                 + cta(f"Reçois les marchés « {nom.lower()} » le jour de leur parution.")
                 + f'<p class="note">Autres catégories : {liens_cats}</p>{bloc_avis(du_lot[:60]) or "<p>Aucun avis public pour l&#x27;instant.</p>"}')
        page(f"appels-offres-{code}.html", f"Appels d'offres {nom.lower()} : marchés publics récents | Marchés IT",
             f"Les appels d'offres publics récents en {nom.lower()}, relevés au BOAMP : acheteur, département, date limite. Alerte quotidienne par e-mail.",
             corps)

    urls = [BASE] + [f"{BASE}appels-offres-{c}.html" for c, _, _ in categories]
    open("sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                   + "".join(f"<url><loc>{u}</loc><lastmod>{aujourdhui.isoformat()}</lastmod></url>" for u in urls) + "</urlset>\n")
