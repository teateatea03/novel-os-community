# Contrat d’adaptateur hôte de Novel OS

<!-- language-navigation -->

[繁體中文](host-adapter-contract.md) | [English](host-adapter-contract.en.md) | [日本語](host-adapter-contract.ja.md) | [한국어](host-adapter-contract.ko.md) | [Español](host-adapter-contract.es.md) | **Français** | [Deutsch](host-adapter-contract.de.md) | [Português](host-adapter-contract.pt.md)

Ce contrat s’adresse aux intégrateurs de frameworks d’IA autres que Minis. Novel OS n’est pas un plugin qui obtient l’accès aux fichiers, aux modèles ou une mémoire entre conversations par le simple téléversement d’un ZIP. L’hôte doit fournir les capacités suivantes pour que le déploiement soit considéré comme automatisé.

## A. Interfaces minimales à fournir par l’hôte

| Capacité | Opérations minimales | Utilisation par Novel OS | Si indisponible |
|---|---|---|---|
| Routeur de compétences | `load_skill(name)`/lecture de ressources | Le coordinateur charge seize compétences spécialisées selon l’intention | Inclure manuellement le Skill approprié dans le prompt |
| Stockage persistant | `read(path)`, `write(path)`, `list(path)`, `mkdir(path)` | Bible du projet, chapitres, registres, état, graphes et instantanés | Mode documentaire uniquement ; continuité entre exécutions non garantie |
| Lanceur de processus | `run(argv, cwd)` | Exécuter les outils Python d’initialisation, de contrôle, d’état et de graphe | Utiliser manuellement modèles et listes de contrôle ; ne pas prétendre avoir exécuté la validation |
| Identité du projet | `project_id` stable → racine de stockage | Lire l’état du même roman dans une nouvelle conversation/un nouveau worker | L’utilisateur fournit manuellement fichiers/résumés à chaque fois |
| Verrou d’écriture de branche | `lock(project,session,branch)`/verrou transactionnel | Sérialiser les commits de récupération, hash périmé, événements, état et manifeste | N’autoriser qu’un seul rédacteur ; ne pas revendiquer la sûreté multi-worker |
| Adaptateur de tâches de modèle | Accepter `minis.model-task.v1`, persister d’abord le calendrier, attribuer les tâches aux workers avec un bail, renvoyer un schéma fixe | Limiter les modèles L1/L2 aux tâches individuelles extract/plan/render/repair ; permettre reprise/annulation/résultats périmés/récupération après redémarrage | Mode documentaire ou formulaires manuels ; les modèles n’ont aucune autorité sur l’état |
| Versions de runtime/événements | Build du runtime, schéma d’événement, contrat de transition, données de rejeu de référence | Après mise à niveau, rejouer l’historique produit toujours la même empreinte d’état ; les contrats inconnus sont bloqués | Figer l’ancien runtime ; mise à niveau uniquement après migration manuelle |
| Solveur narratif | Exploration bornée des états de storylets | Détecter états inaccessibles, cibles cassées et blocages logiques en précisant les limites d’exploration | Revue manuelle des parcours ; ne pas prétendre les avoir tous validés |
| Contrôle des suggestions d’événements aléatoires | `off`/`on-suggestion` par branche, fenêtre sémantique, réserve à graine fixe, audit non canonique | Proposer des cartes de direction facultatives uniquement dans les fenêtres autorisées, avec possibilité de non-événement et provenance reproductible | Rester sur `off` ; ne pas tirer secrètement via les prompts ni traiter les suggestions comme canon |
| Projection mémoire/graphe | Événement → mémoire épisodique ; événements → projection Graphify | Mémoire traçable et graphes reconstructibles | Conserver les événements ; marquer les index dérivés comme non mis à jour |
| Index d’achèvement Graphify | `sync_graph.py` synchronise sources, affirmations et branches vers le `graph.json` existant | Sources, preuves, versions et hypothèses d’achèvement interrogeables | Le graphe est un index dérivé et ne doit pas écraser en retour prose/canon |

Le lanceur de processus doit privilégier les **tableaux argv plutôt que les chaînes shell concaténées**, rester dans les espaces de travail du projet/des compétences et conserver stdout, stderr et code de sortie comme pièces de contrôle.

## B. Correspondance des chemins

La configuration de déploiement doit fournir les valeurs suivantes. Ne codez pas en dur les chemins Minis dans un autre environnement :

```text
SKILLS_ROOT=/agent/skills
NOVEL_PROJECTS_ROOT=/agent/data/novels
CHARACTER_DATABASE_ROOT=/agent/data/character-databases
CHARACTER_DATABASE_WORK_ROOT=/agent/work/character-db-batches
WORLD_DATABASE_ROOT=/agent/data/world-databases
SPECIAL_OBJECT_DATABASE_ROOT=/agent/data/special-object-databases
SPECIAL_OBJECT_DATABASE_WORK_ROOT=/agent/work/special-object-db-batches
INTERACTIVE_PROJECTS_ROOT=/agent/data/interactive-fiction
```

- `init_novel_project.py` peut lire `NOVEL_PROJECTS_ROOT` ou accepter un `--root` explicite.
- `SPECIAL_OBJECT_DATABASE_ROOT` contient la base d’objets spéciaux faisant autorité à `graphify-out/graph.json` ; `SPECIAL_OBJECT_DATABASE_WORK_ROOT` contient les lots JSON et paquets de transmission et ne peut remplacer la copie faisant autorité.
- `WORLD_DATABASE_ROOT` contient la base d’univers faisant autorité à `graphify-out/graph.json` ; `WORLD_DATABASE_WORK_ROOT` contient les lots JSON d’univers et paquets de transmission et ne peut remplacer la copie faisant autorité.
- Les autres racines sont des paramètres du routeur/adaptateur du framework. Remplacez les paramètres `<..._ROOT>` des Skills concernés par de vrais chemins persistants.
- Tous les fichiers d’un roman doivent résider sous la même racine de projet relisible ; ne conservez pas uniquement le dernier chapitre dans le contexte temporaire du chat.

## C. Procédure de déploiement requise

1. Extrayez le paquet et exécutez d’abord :

   ```bash
   # Vérifier d’abord Python, les empreintes et le test de bon fonctionnement complet :
   python3 scripts/install_novel_os.py --target "$SKILLS_ROOT" --smoke-test
   ```

2. Enregistrez **17** Skills (coordinateur + 16 spécialisés). `novel-reality-state-engine` doit fournir JSON événement/état, Reality Card et Reality Gate exécutable. `novel-model-capability-compatibility` doit fournir les sondes texte/JSON/outils/état du point de terminaison réel, les niveaux de capacité et le repli. `novel-sensory-sound-prose` doit conserver son contrat de prose sonore/des cinq sens. Préservez les chemins relatifs entre voisins.
3. Reliez `project_id` aux racines persistantes ci-dessus et autorisez l’agent à lire et écrire les fichiers de ce projet.
4. Exécutez l’initialiseur d’un nouveau projet et confirmez la création de Markdown/JSON/`graphify-out/graph.json`.
5. Fermez puis lancez une nouvelle exécution de l’agent et demandez-lui de lire l’état avant de poursuivre, afin de vérifier son indépendance du contexte temporaire.
6. Faites commiter deux workers simultanément sur la même empreinte d’état source : un seul doit réussir, l’autre doit recevoir stale-hash/conflict. Vérifiez ensuite l’empreinte actuelle par rejeu des événements.
7. Créez deux mémoires épisodiques et vérifiez que la réflexion cite au moins deux identifiants de preuves existants. Compilez une tâche de rendu L1 et confirmez que le paquet ne contient aucune vérité cachée et porte `may_commit_state=false`.
8. Reconstruisez la projection Graphify interactive depuis les événements. Sa suppression et sa reconstruction doivent produire la même empreinte source.
9. Conservez au moins un jeu d’historique de référence. Son rejeu avec un nouveau runtime doit produire l’empreinte d’état attendue, et les contrats de transition inconnus doivent être rejetés.
10. Créez une activité de modèle et vérifiez la récupération après expiration du bail, le marquage des anciens résultats comme périmés après avancement de l’état, et le blocage de la console auteur tant qu’une activité est en attente.
11. Créez un jeu de storylets avec états inaccessibles, cibles cassées et blocages logiques ; confirmez leur détection par le solveur et l’affichage explicite de profondeur maximale/nombre maximal d’états.
12. Après compactage des événements, supprimez l’index et altérez l’archive. Le contrôle d’intégrité du manifeste doit la rejeter avant reconstruction de l’index.
13. Vérifiez qu’une nouvelle branche utilise `off` par défaut, sans tirage ni écriture d’audit. Après activation de `on-suggestion` par l’utilisateur, utilisez une graine fixe à une limite de scène pour obtenir la même suggestion/absence d’événement, et confirmez que le journal canonique, State, Graph, Knowledge et la prose sont inchangés.
14. Soumettez des demandes pour une entrée méta, une conséquence directe en attente, une situation de forte pression sans pause naturelle, une conséquence déterministe existante et une menace sans annonce préalable ; toutes doivent être supprimées. Adopter une suggestion ne peut créer qu’une transmission de planification et doit lister les Gates Reality/Knowledge/Agency/Behavior/World/Canon.
15. Vérifiez empreinte/octets/nombre du manifeste du segment actif : après suppression de l’index d’événements, altérer le journal actif doit déclencher un blocage de sécurité. L’attribution d’activité renvoie un jeton de verrouillage ; la finalisation doit être rejetée avec un ancien jeton, sans jeton ou avec un bail expiré. Tous les identifiants utilisés dans les chemins doivent refuser la traversée de répertoires. Réessayer le même `request_id` d’événement aléatoire ne doit pas effectuer un nouveau tirage ni créer une deuxième entrée d’audit. Une chaîne d’empreintes d’audit altérée ne doit pas être rejouée, et des suggestions expirées ne doivent pas produire de transmission d’adoption.

## D. Adaptateurs d’outils facultatifs

### Recherche web

Si l’hôte fournit navigateur/recherche, le routeur doit enregistrer résultats, URL, éditeurs, dates et courtes citations dans les champs de preuves recherche/graphe. Sans navigateur, il ne peut traiter que les ressources fournies par l’utilisateur, doit utiliser `【待定】` (« indéterminé »)/`【提案】` (« proposition ») et ne doit pas prétendre avoir vérifié les sources.

### Revue par deuxième modèle/sous-agent

`long-form-novel-writer/scripts/independent_review.py` appelle actuellement `minis-model-use` de Minis. Les autres frameworks doivent choisir :

1. Écrire un adaptateur acceptant `role`, `prompt` et `max_tokens`, appelant un autre modèle/sous-agent et enregistrant le texte brut et le JSON analysé sous `reviews/` ; ou
2. Désactiver la revue indépendante, utiliser les contrôles locaux/listes manuelles et indiquer « deuxième modèle non exécuté » dans la transmission.

Dans les deux cas, préservez ces règles de sortie : `machine_suggestion` ne peut être promue directement en `[CANON]` ; les problèmes sans deux preuves à l’appui vont uniquement dans `questions` ; les échecs doivent produire une pièce `unavailable` et ne jamais être comptés silencieusement comme réussites.

### Graphes et gestion de versions

- `networkx` : permet les fonctions path, affected, GraphML et connexes.
- `graphifyy` + `networkx` : permet les exports HTML Graphify, l’analyse de communautés et Cypher.
- Git : uniquement pour commits/branches ; les instantanés de fichiers restent disponibles sans Git.

Ce sont des enrichissements, pas des prérequis au démarrage d’un roman.

## E. Logique minimale du routeur

```text
si la demande concerne créer/modifier/interroger/comparer/exporter une base d’objets spéciaux :
    charger special-object-database-builder
    ajouter novel-worldbuilding-architect + knowledge-relationship-graph
    ajouter character-db + behavior si opérateur/machine autonome/personnalité importe
    ajouter long-form si lié à un projet de roman ou à un état de chapitre
sinon si la demande concerne créer/modifier/interroger/exporter une base d’univers :
    charger novel-world-database-builder
    ajouter novel-worldbuilding-architect + knowledge-relationship-graph
    ajouter long-form si lié à un projet de roman ou à un état de chapitre
sinon si la demande concerne l’écriture entre chapitres/la continuation/la révision du plan :
    charger long-form + behavior
    ajouter world/style/graph seulement si l’état narratif le nécessite
sinon si la demande concerne la recherche sur un personnage :
    charger character-deep-digger
    ajouter behavior + character-db/graph si des preuves ou la persistance sont nécessaires
sinon si la demande concerne une révision de voix humaine/chinois traditionnel de Taïwan/voix de personnage :
    charger human-voice-editor après les contrôles de contenu/continuité/style
sinon si la demande concerne l’achèvement d’un roman abandonné/inachevé, l’intention de l’auteur original ou une autre fin :
    charger unfinished-novel-completion
    ajouter long-form + outils de preuves/sources + world/behavior/style/graph selon les besoins
sinon si la demande concerne une fiction interactive à saisie libre :
    charger immersive-interactive-fiction
    ajouter world/behavior/style/graph selon la complexité de la scène
```

Le coordinateur doit d’abord prendre en charge ce routage. Ne placez pas aveuglément tous les Skills dans le contexte du modèle à chaque tour.

## F. Ce que le paquet ne peut pas faire automatiquement

- Installer des Skills, configurer des clés d’API, activer des permissions d’outils ou créer des bases dans des comptes cloud non autorisés.
- Donner à un modèle de chat seul un shell, un système de fichiers, une mémoire permanente ou des capacités multi-modèles.
- Déroger aux politiques de contenu, limites de jetons, règles de confidentialité ou restrictions réseau du modèle/de la plateforme cible.

Si des prérequis manquent, utilisez les modes de repli B/C/D de [platform-compatibility.fr.md](platform-compatibility.fr.md) et listez chaque fonction désactivée dans le rapport de déploiement.
