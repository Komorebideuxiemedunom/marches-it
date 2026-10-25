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
STYLE = """<link rel="preload" href="fonts/source-serif.woff2" as="font" type="font/woff2" crossorigin><style>
@font-face{font-family:"Source Serif";src:url(fonts/source-serif.woff2) format("woff2");font-weight:200 900;font-display:swap}
@font-face{font-family:"Franklin";src:url(fonts/libre-franklin.woff2) format("woff2");font-weight:100 900;font-display:swap}
:root{--bg:#F4F1EA;--ink:#141414;--muted:#4A4844;--accent:#A8231B;--line:#D9D3C6;--s1:8px;--s2:16px;--s3:24px;--s4:32px;--s6:48px;--s8:64px}
@media (prefers-color-scheme:dark){:root{--bg:#121212;--ink:#EEEBE3;--muted:#B5B1A8;--accent:#FF7A6E;--line:#2E2D2B}}
*{box-sizing:border-box}html{background:var(--bg)}body{margin:0;color:var(--ink);font:400 18px/1.6 "Source Serif",Georgia,serif}
main{max-width:1120px;margin:0 auto;padding:var(--s3) var(--s3) var(--s8)}
a{color:var(--ink);text-decoration-color:var(--accent);text-underline-offset:3px}a:hover,a:focus-visible{color:var(--accent);text-decoration-thickness:2px}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
p,li{color:var(--muted);max-width:66ch}strong{color:var(--ink)}
.une{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:var(--s1);border-bottom:4px double var(--ink);padding-bottom:var(--s1);margin-bottom:var(--s6);font:600 13px "Franklin",sans-serif;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}
.marque{font:800 26px "Franklin",sans-serif;letter-spacing:-.01em;text-transform:none;color:var(--ink);text-decoration:none}
.marque:hover{color:var(--accent)}
h1{font-weight:700;font-size:clamp(40px,6vw,76px);line-height:1;letter-spacing:-.02em;margin:0 0 var(--s3);max-width:20ch}
h2{font:700 14px "Franklin",sans-serif;text-transform:uppercase;letter-spacing:.1em;color:var(--ink);border-top:2px solid var(--ink);padding-top:var(--s1);margin:var(--s6) 0 var(--s2)}
.chapeau{font-size:clamp(20px,2.2vw,24px);line-height:1.45;color:var(--ink);max-width:44ch}
.chiffres{font-size:clamp(22px,2.6vw,32px);line-height:1.35;color:var(--ink);max-width:none;margin:var(--s4) 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:var(--s3) 0}
.chiffres strong{font-weight:800;color:var(--accent)}
.cta{border:2px solid var(--ink);padding:var(--s4);margin:var(--s6) 0;display:grid;grid-template-columns:minmax(0,2fr) auto;gap:var(--s3);align-items:center}
.cta p{color:var(--ink);margin:0}
.btn{display:inline-block;background:var(--accent);color:var(--bg);font:700 16px "Franklin",sans-serif;padding:14px 22px;text-decoration:none;white-space:nowrap}
.btn:hover,.btn:focus-visible{background:var(--ink);color:var(--bg)}
.avis-liste{columns:2 360px;column-gap:var(--s6);column-rule:1px solid var(--line)}
.avis{break-inside:avoid;border-top:1px solid var(--line);padding:var(--s2) 0}.avis a{font-weight:650;font-size:19px;line-height:1.3;text-decoration:none}.avis a:hover{text-decoration:underline}
.avis small{display:block;color:var(--muted);font:400 14px/1.5 "Franklin",sans-serif;margin-top:4px}
.cats{font:500 16px/2 "Franklin",sans-serif}.note{font:400 14px "Franklin",sans-serif}
footer{margin-top:var(--s8);padding-top:var(--s2);border-top:4px double var(--ink);font:400 14px "Franklin",sans-serif;color:var(--muted)}
@media (max-width:720px){main{padding:var(--s2) var(--s2) var(--s6)}.cta{grid-template-columns:1fr}.une{margin-bottom:var(--s4)}}
</style>"""


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def date_longue(d):
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year}"


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
    return '<div class="avis-liste">' + "".join(out) + "</div>" if out else ""


def page(chemin, titre, description, corps, faq=()):
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]} if faq else None
    doc = (f'{HEAD}\n<title>{esc(titre)}</title>\n<meta name="description" content="{esc(description)}">\n'
           f'<link rel="canonical" href="{BASE}{"" if chemin == "index.html" else chemin}">{STYLE}'
           + (f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else "")
           + f'</head>\n<body><main><div class="une"><a class="marque" href="index.html">Marchés IT</a>'
           f'<span>Le bulletin des marchés publics informatiques</span><span>{date_longue(dt.date.today())}</span></div>\n{corps}\n'
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
             f'<p class="chapeau">Sites internet, applications, logiciels, hébergement, cybersécurité, matériel : Marchés IT relit le BOAMP tous les jours '
             f'et t\'envoie seulement les marchés de ton métier, dans tes départements.</p>'
             f'<p class="chiffres"><strong>{par_semaine}</strong> avis informatiques publiés ces 7 derniers jours, '
             f'<strong>{ouverts}</strong> marchés encore ouverts aux réponses, <strong>{len(recents)}</strong> avis récents réservés aux abonnés.</p>'
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
    open("sitemap.xml", "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                   + "".join(f"<url><loc>{u}</loc><lastmod>{aujourdhui.isoformat()}</lastmod></url>" for u in urls) + "</urlset>\n")
