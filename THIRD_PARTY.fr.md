# Composants tiers et références

<!-- language-navigation -->

[繁體中文](THIRD_PARTY.zh-TW.md) | [English](THIRD_PARTY.md) | [日本語](THIRD_PARTY.ja.md) | [한국어](THIRD_PARTY.ko.md) | [Español](THIRD_PARTY.es.md) | **Français** | [Deutsch](THIRD_PARTY.de.md) | [Português](THIRD_PARTY.pt.md)

Novel OS contient du code et de la documentation originaux du projet qui interagissent avec des projets tiers ou les décrivent. Sauf mention explicite contraire dans un fichier, les projets tiers **ne sont pas incorporés** à ce dépôt.

## Dépendances d’exécution ou facultatives

| Composant | Utilisation | Licence / source |
|---|---|---|
| Python | Exécution (3.10+) | Python Software Foundation License |
| NetworkX | Algorithmes de graphes et export GraphML | BSD-3-Clause ; https://networkx.org/ |
| PyYAML | Entrée d’état YAML pour l’utilitaire de projection des PNJ | MIT ; https://pyyaml.org/ |
| MCP Python SDK | Client MCP Instagram local facultatif | MIT ; https://github.com/modelcontextprotocol/python-sdk |
| Graphify (`graphifyy`) | Interopérabilité facultative d’analyse et d’export de graphes | Le projet amont indique Apache-2.0 et inclut des éléments sous licence MIT ; https://github.com/Graphify-Labs/graphify |

Le serveur MCP Instagram anonyme et Instaloader sont des composants facultatifs distincts et ne sont pas inclus ici. Les exploitants doivent les installer et respecter les conditions des plateformes, le droit applicable, les contrôles robots/d’accès et les contraintes du projet limitant les données aux seules données publiques.

## Références de recherche

La documentation cite des articles, spécifications, livres, outils et projets publics comme références de recherche. Les liens et descriptions n’incorporent ni le code ni le texte de ces œuvres dans Novel OS. Si une contribution adapte du code ou du texte au lieu de simplement citer des idées, elle doit identifier la source exacte, la licence, les modifications et l’attribution requise.

## Éléments adaptés inclus dans cette distribution

- **Humanizer-zh**, copyright (c) 2026 歸藏, MIT : [source amont au commit f4518a8eab97b8bfebc66a89d34320a89bef6930](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930)
  - Adaptation : `skills/novel-human-voice-editor/references/humanizer-zh-checkpoints.md` traduit et condense les 31 points de contrôle éditoriaux en chinois traditionnel et ajoute des règles de préservation et de conflit propres à la fiction
  - [Mention MIT amont conservée](skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt), vérifiée par rapport à ce commit amont exact
  - La mention accompagne la compétence dans les sources, le paquet portable et l’environnement installé. Elle s’applique aux éléments amont, **pas** à l’ensemble de Novel OS ; les éléments rédigés pour le projet sont régis séparément par la [licence](LICENSE.fr.md)

## Intégrations externes d’hôte non distribuées ici

`lieflat-less-ai-tone` est une passe éditoriale facultative fournie par l’hôte, et non l’une des 17 compétences d’exécution. Son document d’intégration indique une révision externe, mais ce dépôt ne contient ni URL/licence amont vérifiée, ni son implémentation. Ne la récupérez pas, ne l’incorporez pas et ne prétendez pas qu’elle s’est exécutée automatiquement. Si elle est absente, conservez le flux intégré de révision de la voix humaine et indiquez que cette passe supplémentaire n’a pas été exécutée. Vérifiez séparément sa provenance et sa licence avant de l’installer ou de la distribuer.

L’adaptateur de revue indépendante `minis-model-use` exige son hôte d’origine. Les autres hôtes doivent fournir un remplacement explicitement configuré ou indiquer que la revue indépendante par modèle n’a pas été exécutée. Les tests de non-régression locaux n’utilisent pas de modèles réels ni de services Graphify, MCP ou Instagram.

## Périmètre des dépendances

Les paquets facultatifs ci-dessus ne sont ni inclus ni installés par la distribution de base. Leurs obligations de licence restent rattachées à leurs distributions respectives ; examinez la version amont exacte avant d’activer une intégration ou de redistribuer un paquet combiné. Les tests de base s’exécutent sans ces dépendances. Cet inventaire aide à l’examen et ne constitue pas un conseil juridique.
