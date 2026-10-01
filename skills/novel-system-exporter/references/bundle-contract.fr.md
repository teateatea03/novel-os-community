# Contrat du paquet portable Novel OS

<!-- language-navigation -->

[繁體中文](bundle-contract.md) | [English](bundle-contract.en.md) | [日本語](bundle-contract.ja.md) | [한국어](bundle-contract.ko.md) | [Español](bundle-contract.es.md) | **Français** | [Deutsch](bundle-contract.de.md) | [Português](bundle-contract.pt.md)

Dans l’arborescence `novel-os-portable-v<version>/`, `skills/` contient un coordinateur et 16 compétences spécialisées. `public-web-research/` assure l’acquisition HTTP(S) publique sûre et reprenable ainsi que la préparation de candidats Evidence Run. `novel-model-capability-compatibility/` maintient les contrats de sondes de capacité des modèles/L0–L5/repli. `novel-reality-state-engine/` maintient les outils de validation événement → état → capacité → comportement → prose. `novel-world-database-builder/` maintient les schémas de bases d’univers, modèles de lots, paquets de transmission et spécifications de requête. `special-object-database-builder/` maintient les schémas de versions, capacités, spécifications et cycles de vie des accessoires/armures/mechas/appareils.

```text
novel-os-portable-v<version>/
├── MANIFEST.json
├── LICENSE
├── THIRD_PARTY.md
├── docs/
│   ├── COMMERCIAL_TERMS.md
│   └── i18n/
│       ├── zh-TW/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── ja/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── ko/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── es/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── fr/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── de/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       └── pt/
│           ├── LICENSE.md
│           ├── THIRD_PARTY.md
│           └── COMMERCIAL_TERMS.md
├── references/
│   ├── portable-install.md
│   ├── portable-install.en.md
│   ├── portable-install.ja.md
│   ├── portable-install.ko.md
│   ├── portable-install.es.md
│   ├── portable-install.fr.md
│   ├── portable-install.de.md
│   ├── portable-install.pt.md
│   ├── platform-compatibility.md
│   ├── platform-compatibility.en.md
│   ├── platform-compatibility.ja.md
│   ├── platform-compatibility.ko.md
│   ├── platform-compatibility.es.md
│   ├── platform-compatibility.fr.md
│   ├── platform-compatibility.de.md
│   ├── platform-compatibility.pt.md
│   ├── host-adapter-contract.md
│   ├── host-adapter-contract.en.md
│   ├── host-adapter-contract.ja.md
│   ├── host-adapter-contract.ko.md
│   ├── host-adapter-contract.es.md
│   ├── host-adapter-contract.fr.md
│   ├── host-adapter-contract.de.md
│   ├── host-adapter-contract.pt.md
│   ├── bundle-contract.md
│   ├── bundle-contract.en.md
│   ├── bundle-contract.ja.md
│   ├── bundle-contract.ko.md
│   ├── bundle-contract.es.md
│   ├── bundle-contract.fr.md
│   ├── bundle-contract.de.md
│   └── bundle-contract.pt.md
├── skills/
│   ├── novel-operating-system/      # point d’entrée unique obligatoire
│   ├── long-form-novel-writer/
│   ├── novel-character-deep-digger/
│   ├── human-behavior-personality-consultant/
│   ├── novel-worldbuilding-architect/
│   ├── novel-style-craft-director/
│   ├── novel-human-voice-editor/
│   ├── knowledge-relationship-graph/
│   ├── character-database-builder/
│   ├── immersive-interactive-fiction/
│   ├── unfinished-novel-completion/
│   ├── novel-world-database-builder/
│   ├── special-object-database-builder/
│   ├── novel-reality-state-engine/
│   ├── novel-model-capability-compatibility/
│   ├── novel-sensory-sound-prose/
│   └── public-web-research/
└── scripts/
    ├── install_novel_os.py
    ├── verify_novel_os.py
    └── build_novel_os_bundle.py
```

`MANIFEST.json` contient : schéma/version du paquet, liste des paquets, versions des compétences sources, empreinte SHA-256 et nombre d’octets de chaque fichier, inventaire distinct `distribution_notices`, date de construction, exclusions et déclarations de dépendances d’exécution. Le contenu inclut aussi une copie portable du **guide de compatibilité des plateformes**. Il ne contient aucun secret, chemin local absolu, projet narratif, configuration de compte ou base d’univers.

## Conservation des licences et mentions

- `--source-root` désigne le répertoire source `skills/`. Son parent de dépôt doit contenir les huit versions de `LICENSE`, `THIRD_PARTY.md` et `docs/COMMERCIAL_TERMS.md`, soit les 24 documents explicitement énumérés ci-dessus. Refresh refuse tout document requis absent, non régulier ou lié symboliquement avant de modifier le contenu. Ces conditions du projet sont choisies par le propriétaire ; les mentions amont conservent leur propre portée.
- La liste d’autorisation explicite supplémentaire est `LICENSE.md`, `LICENSE.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt` et `docs/COMMERCIAL_LICENSE.md`. Chaque fichier présent est copié octet pour octet. Aucun autre fichier de `docs/` racine n’est exporté. En particulier, `docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md` est un brouillon de discussion sans effet juridique et n’est pas exporté comme licence ou conditions commerciales.
- Les fichiers de compétence `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, `COPYING.md`, `COPYING.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt`, `THIRD_PARTY.md` et tous les fichiers sous `THIRD_PARTY_LICENSES/` sont conservés et déclarés dans `distribution_notices`. Refresh compare leurs octets aux sources ; la construction et l’installation refusent les déclarations absentes, fichiers manquants, octets modifiés, chemins dangereux ou entrées d’empreinte manquantes.
- L’adaptation Humanizer-zh existante exige spécifiquement `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`. Il ne peut être retiré des sources ou du manifeste tant que cette adaptation est distribuée.
- Tout nouveau nom de fichier légalement requis doit être ajouté à ce contrat explicite avant publication. Ne vous reposez pas sur un lien vers un document absent du paquet. Refresh supprime les anciennes copies facultatives de mentions racine devenues obsolètes.
- Le ZIP conserve la même arborescence relative à la racine. L’installation stocke toutes les mentions sous `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`, en préservant les chemins tels que `docs/COMMERCIAL_TERMS.md` et `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`, afin de conserver les liens relatifs. Les mentions amont locales aux compétences restent également dans leur dossier d’origine. L’installateur n’écrit jamais `<target>/LICENSE`, `<target>/THIRD_PARTY.md` ou `<target>/docs/`.
- `novel-operating-system/INSTALLATION.json` enregistre pour chaque mention installée le chemin d’origine, le chemin installé, le chemin de copie documentaire, le SHA-256 et le nombre d’octets. La préparation et l’installation finale vérifient les deux copies le cas échéant. Une mise à niveau place le coordinateur précédent et ses mentions dans la sauvegarde normale des compétences et les restaure en cas d’échec. `DISTRIBUTION_NOTICES/` dans le coordinateur est réservé aux documents gérés par l’installateur.
- Pour revérifier une installation, exécutez `python3 scripts/install_novel_os.py --target <SKILLS_ROOT> --verify-installed-notices` depuis le paquet extrait. Ce mode en lecture seule compare les mentions racine et amont au registre d’installation. Les empreintes établissent l’intégrité locale, pas l’authenticité face à un attaquant capable de remplacer à la fois les fichiers et les registres ; conservez séparément une publication fiable.

## Déclaration des dépendances d’exécution

Chaque publication doit fournir les 32 références de portabilité explicitement autorisées : les quatre familles `portable-install`, `platform-compatibility`, `host-adapter-contract` et `bundle-contract`, chacune dans les huit versions linguistiques énumérées ci-dessus sous `references/`. Le chinois traditionnel n’a pas de suffixe ; l’anglais utilise `.en.md`, et les six autres langues `.ja.md`, `.ko.md`, `.es.md`, `.fr.md`, `.de.md`, `.pt.md`. Déclarez honnêtement les niveaux suivants :

- **Flux documentaire de base :** un LLM capable de lire les fichiers Skill ; aucune exécution de code requise.
- **Flux local automatisé (v2.7) :** Python 3.10+ (3.11+ recommandé), shell/lanceur de processus, fichiers UTF-8 persistants, découverte de plusieurs compétences ou routeur équivalent, verrou de branche, autorité de production unique `ProjectRuntimeAdapter.commit()`, sept Gates, événements sémantiques typés, préparation du projet/fraîcheur des projections, Quality Eval des retours d’auteur et extraction si distribution ZIP. Les bases d’univers exigent aussi `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT` inscriptibles ; les bases d’objets spéciaux exigent `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` inscriptibles.
- **Enrichissement des graphes :** `networkx` pour le parcours ; `graphifyy` et `networkx` pour les exports Graphify HTML/communautés/Cypher. Le JSON du graphe reste utilisable sans ces paquets.
- **Intégrations facultatives :** Git pour les commits, outils web/navigateur pour la recherche de sources et adaptateur deuxième modèle/sous-agent propre à l’hôte pour la revue indépendante. `independent_review.py` reste spécifique à Minis tant qu’il n’est pas remplacé.

Aucun Node.js, serveur de base de données, clé d’API ou accès Internet n’est requis pour la base locale. Un framework sans accès aux fichiers/processus doit être décrit comme mode documentaire/manuel, pas comme installation automatique complète.

## Politique de construction

- Le contenu doit comporter **17** répertoires de compétences autorisés (un coordinateur + 16 compétences spécialisées), références de portabilité, scripts d’installation/construction et fichiers ordinaires de texte/source/test/modèle.
- Exclure `.git`, `.DS_Store`, `__pycache__`, `*.pyc`, `.env*`, `node_modules`, `dist`, `build`, tous les projets de romans, bases de données, archives et fichiers propres au système.
- Rejeter les liens symboliques dans le chemin des compétences sources ou dans toute compétence empaquetée avant modification ; ne jamais suivre un lien vers des fichiers hôte sans rapport. Les documents de contenu existants non approuvés font également échouer Refresh, au lieu d’entrer silencieusement dans un nouveau manifeste.
- Conserver les bits exécutables de `scripts/*.py` lorsque les sources les possèdent.
- Lire uniquement l’arbre local de compétences sources et la liste explicite des mentions au niveau du dépôt. La construction est déterministe, à l’exception de `built_at`.
- Le paquet est autonome : les assistants d’exécution utilisent la bibliothèque standard Python et découvrent les dépendances relativement à leur emplacement installé.

## Politique de vérification

`verify` doit rejeter les fichiers absents, modifiés, inattendus ou d’empreinte incorrecte, puis compiler chaque fichier Python. Le test de bon fonctionnement de l’installateur doit en plus :

1. initialiser un projet temporaire de roman sous une autorité de production active ;
2. vérifier que la mutation canonique directe de FileStore est bloquée ;
3. exécuter toute la suite Novel Judge, notamment l’autorité des Gates, la préparation, l’exécuteur de commandes, Quality Eval v2, les événements sémantiques typés et la production traditionnelle longue ;
4. exécuter le validateur de graphe et les régressions de fiction longue/Reality/capacité ;
5. vérifier l’ensemble des compétences du paquet et les écarts de l’ensemble source ;
6. pour une publication complète, exécuter la sonde isolée de contrat d’un deuxième projet et le pilote traditionnel long de plus de 100 000 caractères/inversion de connaissances/cascade.

Une plateforme ne pouvant pas exécuter Python n’est prise en charge qu’au niveau des flux/documents ; signalez cette limite lors de la transmission.
