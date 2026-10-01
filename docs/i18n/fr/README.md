# Novel OS

<!-- language-navigation -->

[繁體中文](../zh-TW/README.md) | [English](../../../README.md) | [日本語](../ja/README.md) | [한국어](../ko/README.md) | [Español](../es/README.md) | **Français** | [Deutsch](../de/README.md) | [Português](../pt/README.md)

Novel OS est un ensemble réutilisable de compétences pour agents d’IA et d’outils Python locaux destiné aux romans longs, à la fiction interactive, à la continuité, à la recherche sur les personnages et les univers, à la cohérence comportementale, aux graphes tenant compte de la provenance et à la validation narrative.

> **Licence :** code source accessible sous la [licence commerciale de partage des bénéfices de Novel OS](LICENSE.md), copyright teateatea03. L’utilisation non commerciale est gratuite ; l’utilisation commerciale entraîne le versement de 0,5 % du bénéfice net annuel positif lié aux éléments concernés. Les modifications et redistributions conservent les mêmes conditions et mentions. Il ne s’agit ni d’une licence MIT ou GPL, ni d’une licence open source conforme à l’OSI.

Pour l’utilisation commerciale et le paiement avec les deux jetons acceptés, consultez les [informations sur le partage des bénéfices et les paiements](COMMERCIAL_TERMS.md). Les droits sur les romans et autres productions des utilisateurs ne sont pas transférés au propriétaire du système.

## Langues couvertes

La documentation publique est disponible en huit langues. Les compétences d’exécution, les modèles de fichiers et leurs références techniques conservent actuellement leur langue d’origine. Cette publication de documentation en huit langues ne traduit pas l’environnement d’exécution.

## Périmètre de confidentialité

Ce dépôt de sources exclut délibérément :

- les manuscrits, brouillons de chapitres, sessions de jeu interactif, états narratifs et jeux de données de retours d’auteur ;
- les bases de recherche sur les personnages, univers, objets spéciaux et personnes réelles ;
- les mémoires de conversation, états locaux des appareils, sauvegardes, exports, identifiants d’accès, points de terminaison privés et fichiers d’environnement.

Les exemples et jeux de données de test publics doivent être synthétiques. Avant chaque envoi ou publication, exécutez le scanner de confidentialité et examinez la liste des fichiers placés dans l’index.

## Structure du dépôt

- `skills/` : paquets de compétences réutilisables, scripts, modèles et données de test synthétiques
- `scripts/` : utilitaires de confidentialité, de validation et de test
- `docs/` : documentation sur la gouvernance du projet et le périmètre de publication

L’arborescence contient 18 répertoires de compétences : 17 compétences d’exécution installables (un coordinateur et 16 collaborateurs), plus l’exportateur de paquets. L’exportateur est un outil de conditionnement et n’est pas installé comme compétence d’exécution.

## Prérequis

- Python 3.10+
- Stockage persistant UTF-8
- Parcours de base utilisant uniquement la bibliothèque standard
- Fonctions facultatives : voir `requirements-optional.txt` et [THIRD_PARTY.md](THIRD_PARTY.md)

Installez les dépendances Python facultatives dans un environnement isolé :

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

L’intégration Graphify est facultative et s’installe séparément selon la documentation du projet amont.

## Première exécution locale (sans modèle ni réseau)

Depuis la racine du dépôt, utilisez Python 3.10+ et Git. Les vérifications de base et la démonstration synthétique ne nécessitent ni paquet facultatif, ni clé d’API, ni manuscrit privé :

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 scripts/run_tests.py

# Conserver l’état de projet généré hors du dépôt de sources.
DEMO_ROOT="$(mktemp -d)"
python3 skills/long-form-novel-writer/scripts/init_novel_project.py \
  --title "Synthetic Demo" --slug synthetic-demo --root "$DEMO_ROOT"
python3 skills/knowledge-relationship-graph/scripts/relationship_graph.py \
  validate --root "$DEMO_ROOT/synthetic-demo"
```

L’initialiseur crée une structure vide de planification et d’état ; il ne génère pas de roman et n’appelle aucun modèle. Conservez vos propres récits dans un répertoire privé distinct. L’initialiseur refuse d’écraser un projet existant.

Pour un hôte d’agent, conservez les compétences d’exécution dans des répertoires voisins et enregistrez `novel-operating-system` comme point d’entrée. Les hôtes sans fichiers persistants ou sans lanceur de processus Python ne permettent que le mode documentaire/manuel. Consultez le [guide de construction et d’installation locales testé](GETTING_STARTED.md) pour les commandes de paquet, les tests de bon fonctionnement, les intégrations facultatives et les limites des plateformes.

## Vérification

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

La suite Novel Judge doit être exécutée par `scripts/run_tests.py` ; le lancement individuel de ses fichiers de test utilisant des imports relatifs au paquet n’est pas pris en charge.

Les contrôles de confidentialité et JSON inspectent les fichiers sources, y compris les fichiers non suivis ou ignorés par Git. Ils excluent les métadonnées Git, les caches Python/de test générés et les environnements virtuels confirmés à la racine ; les fichiers suivis restent contrôlés. Les liens symboliques, fichiers illisibles et textes non UTF-8 entraînent un refus par sécurité. Gardez les paquets générés et les états narratifs hors de cette copie de travail. Le scanner signale les noms de fichiers et les catégories de résultats, jamais le contenu correspondant ; c’est une vérification heuristique, pas une preuve de confidentialité ni une analyse de l’historique.

## Chemins des plateformes

La documentation utilise des paramètres tels que `<SKILLS_ROOT>`, `<WORKSPACE_ROOT>` et `<NOVEL_PROJECTS_ROOT>`. Configurez-les pour la plateforme hôte. Les initialiseurs exécutables utilisent par défaut `~/.novel-os/novels`, sauf si `NOVEL_PROJECTS_ROOT` ou un argument explicite `--root` est fourni.

## Sécurité et périmètre de recherche

Les compétences de recherche sont conçues pour des ressources publiques accessibles légalement. Elles ne doivent pas contourner les connexions obligatoires, CAPTCHA, péages, contrôles robots/d’accès ou restrictions de plateforme. La recherche sur des personnes réelles exige une provenance des sources et ne doit pas transformer des éléments non vérifiés ou sensibles en affirmations factuelles.

## Gouvernance

À lire :

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [THIRD_PARTY.md](THIRD_PARTY.md)

## Licence et contributions

Lisez la [licence](LICENSE.md) et les [modalités de paiement commercial](COMMERCIAL_TERMS.md) avant toute utilisation commerciale. Seul le bénéfice net annuel positif des produits, services et romans concernés est inclus ; les activités sans rapport sont exclues. La déclaration est faite par l’utilisateur, sans télémétrie cachée ni prélèvement automatique. Les composants tiers conservent leurs propres licences et mentions.

Les utilisateurs commerciaux reconnaissent explicitement la version de la licence avant utilisation. Commencez par une issue GitHub sans données privées ou financières pour convenir d’un canal de déclaration privé ; ne publiez pas d’états financiers ou de justificatifs de paiement. Les règles de contribution et de redistribution figurent dans [CONTRIBUTING.md](CONTRIBUTING.md).

## Limites de la vérification

Des tests du noyau sous Linux et des contrôles d’installation synthétiques sont fournis. Les services Graphify/MCP/Instagram facultatifs, les modèles réels, les intégrations natives d’agents et une matrice multiplateforme/multiversion Python ne sont pas certifiés. Les exemples de rapports de modèles sont des illustrations synthétiques, pas des preuves de performances mesurées de fournisseurs ou de modèles.
