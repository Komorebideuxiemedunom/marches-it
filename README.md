# Marchés IT

Veille quotidienne des appels d'offres publics en informatique et web, à partir du BOAMP
(open data DILA, licence ouverte). Site : https://komorebideuxiemedunom.github.io/marches-it/

- `tools/veille.py` : lit le BOAMP, classe les avis (`data/annonces.json`, 90 jours), envoie les
  nouveaux aux abonnés, régénère le site. `--sans-envoi` pour tester ; `FENETRE=30` pour rattraper.
- `tools/site_public.py` : page de vente et pages par catégorie, avis publics avec 3 jours de retard.
- `.github/workflows/veille.yml` : chaque matin vers 6 h-7 h (heure de Paris).

Secrets du dépôt :
- `GMAIL_EXPEDITEUR`, `GMAIL_APP_PASSWORD` : compte Gmail d'envoi (mot de passe d'application).
- `ABONNES` : liste JSON, par exemple
  `[{"email": "a@b.fr", "departements": ["33", "40"], "categories": ["web", "logiciel"]}]`
  (listes vides = toute la France / toutes les catégories ; catégories : web, cyber, logiciel,
  infra, materiel, telecom).
