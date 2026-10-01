# Compatibilité des plateformes et matrice des dépendances de Novel OS

<!-- language-navigation -->

[繁體中文](platform-compatibility.md) | [English](platform-compatibility.en.md) | [日本語](platform-compatibility.ja.md) | [한국어](platform-compatibility.ko.md) | [Español](platform-compatibility.es.md) | **Français** | [Deutsch](platform-compatibility.de.md) | [Português](platform-compatibility.pt.md)

Ce document doit accompagner le ZIP. Novel OS est un ensemble d’**instructions de compétences + modèles locaux/validateurs Python**, et non un modèle autonome, une plateforme de chat, une base vectorielle ou un service cloud. La possibilité d’un « déploiement automatique » dépend de l’autorisation du framework d’IA cible de lire des compétences multifichiers, d’écrire des fichiers, d’exécuter des commandes et, éventuellement, d’appeler des modèles/d’accéder au réseau.

```text
- 1 coordinateur + 16 compétences collaboratrices, soit 17 Skills d’exécution au total (les sources comprennent aussi l’exportateur)
- Compatibilité des capacités de modèles : novel-model-capability-compatibility, responsable des sondes du point de terminaison réel, L0–L5, adaptateurs, repli et régressions après changement
- État de réalité : novel-reality-state-engine, chaîne de validation événement → état → capacité → comportement → prose
- Bases d’univers : novel-world-database-builder
- Bases d’objets spéciaux : special-object-database-builder, racine faisant autorité à SPECIAL_OBJECT_DATABASE_ROOT
- Achèvement des œuvres abandonnées : unfinished-novel-completion
```

## 1. Composants de base et dépendances

| Composant/fonction | Système/format utilisé | Dépendances minimales | Dépendances facultatives | Repli si indisponible |
|---|---|---|---|---|
| Dispatch des compétences | En-tête YAML + Markdown de `SKILL.md` ; `novel-operating-system` | IA/agent pouvant charger plusieurs fichiers texte | Runtime Skills déclenchant les compétences automatiquement selon leur description | Utiliser le coordinateur comme prompt système/instructions du projet et joindre manuellement les autres compétences |
| Persistance du projet | Markdown, JSON, dossiers ordinaires | Lecture/écriture UTF-8 | Git | Maintenir des fichiers de même nom dans chat/Canvas/documents cloud ; préciser que la persistance entre tours n’est pas garantie |
| Initialisation longue et contrôles locaux | CLI Python, bibliothèque standard | **Python 3.10+**, shell, disque inscriptible | Git | Copier manuellement modèles et listes de contrôle ; ne pas prétendre avoir exécuté contrôles/instantanés |
| Graphe de relations faisant autorité | JSON nœuds-liens compatible Graphify | Python 3.10+ (initialisation, validation JSON) | `networkx` : path/affected ; `graphifyy` + `networkx` : HTML, communautés, export Cypher | Sauvegarder/lire graph.json ; examiner les relations manuellement sans affirmer avoir généré visualisations ou plus courts chemins |
| Base d’univers | JSON compatible Graphify ; nœuds monde/lieu/faction/ressource/règle/événement/affirmation, preuves sources et lots incrémentaux | Python 3.10+, fichiers UTF-8 persistants | `networkx`/`graphifyy` : path, affected, HTML, GraphML, Cypher | Sauvegarder graph.json et registres Markdown ; vérifier versions/connaissances manuellement sans déclarer les exports visuels terminés |
| Base d’objets spéciaux | JSON compatible Graphify ; nœuds objet/version/variante/module/capacité/spécification/énergie/contrainte/possession/opération/cycle de vie et preuves sources | Python 3.10+, fichiers UTF-8 persistants | `networkx`/`graphifyy` : path, affected, HTML, GraphML, Cypher | Sauvegarder graph.json et registres d’objets ; vérifier manuellement les conflits de versions/spécifications sans déclarer les exports visuels terminés |
| Fiction interactive | État compatible JSON, journal des tours Markdown | Lecture/écriture de fichiers ; Python 3.10+ pour validation/points de reprise | Mémoire à long terme/base de données | Examiner l’état collé dans le chat à chaque tour ; sa conservation après réouverture n’est pas garantie |
| Recherche et validation des sources d’achèvement | Œuvres inachevées | `unfinished-novel-completion` ; outils de recherche/pièces jointes facultatifs | `source_ingest.py` enregistre empreintes, versions, complétude et droits ; `completion_gate.py` contrôle les affirmations excessives sur l’intention et les limites de publication | |
| Revue indépendante par modèle | CLI/API d’appel de modèles de l’hôte | Aucune ; non requise | Capacité d’appeler un second modèle ou sous-agent | Utiliser une liste manuelle/du même modèle ; ne pas affirmer « examiné par un modèle indépendant » |

### Recherche de sources et outils pour œuvres inachevées

Les outils de base de `unfinished-novel-completion` n’utilisent que la bibliothèque standard Python : `init_completion_project.py`, `source_ingest.py`, `compare_source_versions.py`, `branch_diff.py`, `feasibility_report.py`, `sync_graph.py`, `completion_gate.py`, `provenance_report.py` et `run_regression.py`. Réseau, OCR, outils PDF, navigateurs et deuxième modèle sont tous facultatifs. Sans eux, les fichiers de l’utilisateur restent traitables, mais le périmètre des sources et les inconnues doivent être identifiés ; ne prétendez pas qu’une vérification a eu lieu.

### Environnement minimal « entièrement automatisé »

- **Python 3.10 ou ultérieur :** les scripts de base utilisent la syntaxe d’union de types `X | None` ; Python 3.11+ est recommandé.
- **Shell POSIX ou lanceur de processus équivalent :** pour exécuter la CLI Python.
- **Système de fichiers persistant inscriptible :** pour installer les compétences et sauvegarder les romans ; au moins un répertoire de compétences et un de projets inscriptibles sont requis.
- **Prise en charge UTF-8 :** récits, modèles, JSON et chinois traditionnel utilisent tous UTF-8.
- **Extraction ZIP :** requise seulement pour la distribution ZIP ; Git/téléversement de dossier peut la remplacer.
- **Bibliothèque standard locale :** initialiseur, registres, contrôles, état et scripts de paquet ne dépendent que de la bibliothèque standard ; le test de base ne nécessite pas `pip install`.

Ces fonctions ne nécessitent ni clé d’API, ni base de données, ni Node.js, ni réseau.

### Dépendances facultatives (enrichissements, pas le flux de base)

```bash
# Chemins de graphes, requêtes en cascade, GraphML
python -m pip install networkx

# Exports Graphify HTML/communautés/Cypher ; le paquet amont s’appelle graphifyy
python -m pip install graphifyy networkx

# Instantanés de versions Git et commits protégés par les contrôles
git --version
```

- `relationship_graph.py init/validate/search/neighbors/timeline/add/import/snapshot` peut n’utiliser que la bibliothèque standard ; `path`/certains contrôles de cycles exigent `networkx`.
- `relationship_graph.py export` exige **`networkx` + `graphifyy`**. Sans eux, conservez `graph.json` et ne prétendez pas avoir généré des sorties HTML/GraphML/Cypher.
- `independent_review.py` est actuellement un **adaptateur spécifique à Minis** appelant `minis-model-use`. Dans un autre framework, remplacez-le par son adaptateur deuxième modèle/sous-agent/API, ou désactivez cette revue facultative.
- `novel_git.py` est une couche facultative de gestion de versions. Sans Git, `snapshot_project.py` peut toujours créer des instantanés de fichiers.

## 3.2 Points de liaison à l’hôte et remplacements requis

Les formats de données de base du paquet sont portables, mais l’intégrateur doit traiter ces **points de liaison hôte/framework** :

| Point de liaison | Usage Minis actuel | Actions requises des autres frameworks |
|---|---|---|
| Racine de romans par défaut | `<NOVEL_PROJECTS_ROOT>` | Définir `NOVEL_PROJECTS_ROOT` ou passer `--root <persistent-projects-root>` à chaque initialiseur ; ne pas supposer que `<MINIS_ROOT>` existe |
| Racine de base de personnages | `<CHARACTER_DATABASE_ROOT>` | Associer `<CHARACTER_DATABASE_ROOT>` et la préparation de lots à `<CHARACTER_DATABASE_WORK_ROOT>` ; les deux doivent être accessibles au même projet/agent |
| Racine de base d’objets spéciaux | `<SPECIAL_OBJECT_DATABASE_ROOT>` | Associer `<SPECIAL_OBJECT_DATABASE_ROOT>` et la préparation de lots à `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>` ; les deux doivent être accessibles au même projet/agent |
| Racine d’état de fiction interactive | `<INTERACTIVE_PROJECTS_ROOT>` | Associer `<INTERACTIVE_PROJECTS_ROOT>` et assurer la lecture des états/points de reprise/journaux entre exécutions |
| Revue indépendante | `minis-model-use run` | Réécrire l’adaptateur de commande de `independent_review.py` ou créer un sous-agent équivalent ; conserver schéma JSON, pièces d’erreur et interdiction de promotion automatique au canon |
| Découverte de compétences | Registre Minis + répertoires voisins | Enregistrer **17** descriptions (coordinateur + seize spécialisés), ou créer un routeur d’intentions ; permettre la lecture à la demande des ressources voisines |
| État à long terme | Répertoire partagé Minis | Associer volume durable, base de données, stockage d’artefacts ou système de points de reprise du framework, avec récupération par identifiant de projet |
| Outils de recherche | Navigateur/shell Minis | Associer les outils navigateur/recherche/fichiers du framework ; sinon limiter aux ressources fournies par l’utilisateur |

- `init_novel_project.py` prend déjà en charge `NOVEL_PROJECTS_ROOT` ; un `--root` explicite prime. Les paramètres `<..._ROOT>` des bases de personnages/univers/objets spéciaux et de la fiction interactive doivent être remplacés par le routeur/la configuration de déploiement. Chaque `<MINIS_ROOT>/...` de la documentation d’origine est, hors Minis, un **exemple de chemin par défaut**, pas une exigence ferme du système.

## 4. Niveaux de capacité des frameworks d’IA

### A | Skills natifs + shell + système de fichiers (mode complet)

Pour les frameworks avec runtime Skill, outils d’agent et sandbox/terminal. Installez directement le paquet complet :

```bash
python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test
```

**Le framework doit :**

1. Enregistrer `<SKILLS_DIR>/novel-operating-system/SKILL.md` comme compétence principale déclenchable.
2. Conserver les **17** dossiers (coordinateur + seize collaborateurs) comme voisins ; ne pas téléverser seulement le point d’entrée.
3. Autoriser l’agent à lire les `SKILL.md`, modèles, références et scripts voisins.
4. Fournir un outil de commande ou lanceur de processus sûr pour `python3`.
5. Après réindexation/redémarrage du registre, utiliser les résultats du test de bon fonctionnement pour l’acceptation.

**Ajouts recommandés :** recherche web, adaptateur deuxième modèle, Git, `networkx` et `graphifyy`.

### B | Frameworks d’agents/appels d’outils personnalisés (adaptateur requis)

Pour les frameworks avec prompt système, appels de fonctions et outils de fichiers, mais sans compréhension de `SKILL.md`.

**L’intégrateur doit :**

1. Placer `novel-operating-system/SKILL.md` dans les instructions système/développeur ; garder la description YAML comme règles de routage.
2. Rendre les **seize** autres compétences consultables comme références ou construire un routeur chargeant le `SKILL.md` approprié selon l’intention.
3. Associer les outils :
   - shell → scripts Python ;
   - lecture/écriture/liste de fichiers → fichiers et état du projet ;
   - recherche web/navigateur → recherche de sources publiques ;
   - deuxième modèle/sous-agent → remplacement de `independent_review.py`.
4. Remplacer l’appel Minis `minis-model-use` par le client modèle du framework. Préserver le schéma JSON de revue, les pièces d’échec et le principe « machine_suggestion n’est pas automatiquement promue au canon ».
5. Définir une clé de stockage/espace durable pour conserver les fichiers de la même œuvre entre conversations/workers.
6. Implémenter le déclenchement automatique des compétences ou le désactiver explicitement ; placer **17 documents Skill** dans le contexte ne permet pas d’affirmer qu’ils collaboreront automatiquement.

### C | IA de chat acceptant uniquement des fichiers de connaissances/instructions personnalisées (mode documentaire)

Conventions d’écriture, modèles, schémas et listes de contrôle sont portables, mais une véritable automatisation est indisponible.

**Requis :** téléverser tout le sous-arbre `skills/` ; utiliser le coordinateur comme instructions de projet ; à chaque tour, joindre ou faire consulter par l’IA l’état actuel, la bible, la chronologie, les fichiers de personnages, le registre du lecteur et le résumé du chapitre précédent.

**Ne pas promettre :** création automatique de dossiers, contrôles CLI, vérification d’empreintes, Git, exports Graphify, mémoire entre chats, tâches en arrière-plan ou revue par second modèle.

### D | Modèles avec un seul prompt système (repli manuel)

Collez un coordinateur condensé dans le prompt système et utilisez les compétences spécialisées et modèles de projet comme base de connaissances. L’utilisateur/l’intégrateur doit sauvegarder manuellement les documents d’état produits à chaque tour. Cela conserve le cadre de raisonnement sans équivaloir au Novel OS complet.

## 5. Liste d’intégration des frameworks courants

| Type | Emplacement | Configuration requise | Précaution essentielle |
|---|---|---|---|
| Type OpenAI Assistants/Responses | Instructions système + recherche vectorielle/fichiers + interpréteur de code/sandbox personnalisé | Construire routeur, stockage persistant et adaptateur d’exécution Python | Ne pas supposer la synchronisation automatique entre exécutions ; réenregistrer explicitement les fichiers du projet |
| Type Claude Projects/MCP | Instructions de projet + fichiers de connaissances ; serveur MCP fichiers/shell | Exposer les compétences comme ressources ; utiliser MCP pour lectures/écritures/exécution/web | Sans MCP, niveau C sans exécution de scripts |
| Type Gemini Gems/Vertex Agent | Instructions système + File Search/Code Execution/Cloud Storage | Relier stockage durable, routeur de fonctions et lanceur Python | Les seules instructions Gem ne fournissent généralement pas de flux de fichiers entre conversations |
| Type LangChain/LangGraph/CrewAI/AutoGen | Nœud routeur + outils de fichiers + sous-processus + points de reprise durables | Charger selon l’intention, préserver l’identifiant du projet et créer un adaptateur d’agent de revue | Découverte des compétences et points de reprise doivent être implémentés ; l’extraction seule ne les active pas |
| Type Open WebUI/AnythingLLM/Dify/Flowise | Base de connaissances + flux d’agent/nœuds d’outils | Téléverser les compétences, connecter shell/Python et monter un volume persistant | Le chat RAG seul est de niveau C ; des flux sont nécessaires pour A/B |
| Hôte de base d’univers | `WORLD_DATABASE_ROOT` + `WORLD_DATABASE_WORK_ROOT` | Monter graphe persistant et espace de lots ; fournir snapshot/validate/affected/export | Sans lanceur de processus, ne sauvegarder que JSON/Markdown et ne pas prétendre avoir exécuté la CLI Graphify |
| Hôte de base d’objets spéciaux | `SPECIAL_OBJECT_DATABASE_ROOT` + `SPECIAL_OBJECT_DATABASE_WORK_ROOT` | Monter graphe persistant d’objets et espace de lots ; fournir snapshot/validate/affected/export | Sans lanceur, ne sauvegarder que JSON/Markdown et ne pas prétendre avoir exécuté validation ou export d’objets |
| Agents de programmation tels que Cursor/Claude Code/Codex CLI | Répertoire skills/commands + espace de travail | Installer **17** dossiers et configurer Python et la racine de travail | L’adaptateur de revue conversationnelle par modèle doit être réécrit pour la CLI concernée |

Ces noms illustrent uniquement des types d’intégration. Versions, offres et permissions des produits varient ; confirmez leur documentation actuelle avant déploiement.

## 6. Liste d’acceptation du déploiement

Après intégration, l’hôte ou l’intégrateur doit vérifier chaque point :

- [ ] `novel-operating-system` et les seize compétences spécialisées voisines sont lisibles.
- [ ] Après écriture d’un fichier de test, une nouvelle exécution/conversation peut le relire.
- [ ] `python3 --version` est ≥ 3.10 ; si les exportateurs de graphes sont requis, `networkx`/`graphifyy` sont importables.
- [ ] `python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test` réussit, ou les éléments non exécutables sont explicitement documentés.
- [ ] Un nouveau roman de test possède bible, état, chronologie, registre du lecteur et graph.json.
- [ ] L’agent écrit un court passage, met à jour l’état et poursuit dans une nouvelle exécution, montrant que la continuité ne dépend pas seulement du contexte restant.
- [ ] Si la recherche est activée, URL/sources/confiance sont enregistrables au lieu de traiter les extraits de recherche comme canon.
- [ ] Si la revue par deuxième modèle est activée, les échecs d’adaptateur produisent seulement une pièce d’indisponibilité, sans bloquer ni fabriquer des résultats.

## 7. Limites de plateforme et responsabilités

- Les politiques de contenu, permissions d’outils, limites de jetons, conservation des données et règles réseau du modèle cible sont indépendantes de Novel OS ; ce Skill ne peut les contourner.
- « Déploiement automatique » signifie installation, création de structures et chargement du routeur automatiques dans un **framework d’agent doté des permissions d’installation/fichiers/shell**. Cela ne signifie pas installer définitivement le ZIP en le donnant à n’importe quel modèle de chat.
- Modèles externes, navigateurs et Git sont des enrichissements facultatifs. En leur absence, indiquez explicitement le mode de repli ; ne cachez pas les lacunes de capacité derrière une déclaration d’achèvement.
