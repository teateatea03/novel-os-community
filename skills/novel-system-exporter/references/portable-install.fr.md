# Importer et déployer Novel OS

<!-- language-navigation -->

[繁體中文](portable-install.md) | [English](portable-install.en.md) | [日本語](portable-install.ja.md) | [한국어](portable-install.ko.md) | [Español](portable-install.es.md) | **Français** | [Deutsch](portable-install.de.md) | [Português](portable-install.pt.md)

## Commencer par un inventaire des capacités : choisir le bon mode de déploiement

Avant la livraison, demandez à l’environnement cible de répondre :

```text
1. Peut-il installer plusieurs Skills/commandes ? Où se trouve le répertoire ou la configuration du point d’entrée ?
2. L’agent peut-il lire et écrire des fichiers persistants, lister des répertoires et exécuter des commandes Python/shell ?
3. Quelle version de Python est disponible ? L’installation de networkx, graphifyy et Git est-elle autorisée ?
4. Des outils web/navigateur, un deuxième modèle ou des sous-agents sont-ils disponibles, et comment les invoquer via les outils ?
5. Où résident les fichiers du projet entre nouvelles conversations, nouveaux workers et redémarrages ?
```

Choisissez selon les réponses : **A : installation complète** (Skills + shell + stockage), **B : intégration par adaptateur** (outils d’agent personnalisés), **C : mode fichiers de connaissances**, ou **D : mode manuel à prompt unique**. Consultez [platform-compatibility.fr.md](platform-compatibility.fr.md) pour l’évaluation complète, les paquets et les exigences d’adaptation de chaque framework. Sans les prérequis de A/B, ne déclarez pas le « déploiement automatique » terminé.

## Plateformes d’IA avec répertoires de compétences personnalisés (A : mode complet)

1. Extrayez le ZIP.
2. Depuis la racine extraite, exécutez :

   ```bash
   python3 scripts/install_novel_os.py --target /path/to/agent/skills --smoke-test
   ```

3. Faites réanalyser les compétences par la plateforme, ou redémarrez son index de compétences.
4. Testez avec « Créer un projet de roman long ». Cela doit déclencher `novel-operating-system`, créer la structure du projet, déterminer les besoins en recherche/construction d’univers/comportement/style/graphes, puis terminer la planification et les contrôles avant la rédaction.

**Mises à niveau :** ajoutez `--upgrade`. L’installateur déplace les compétences existantes de même nom dans `<target>/backups/novel-os-<timestamp>-<unique>/` avant remplacement ; il restaure les fichiers d’origine en cas d’échec.

### Licence et mentions tierces

Le ZIP complet doit conserver les huit versions linguistiques de `LICENSE`, `THIRD_PARTY.md` et `docs/COMMERCIAL_TERMS.md`, soit 24 documents, ainsi que les licences tierces d’origine de chaque compétence. La licence anglaise est `LICENSE` ; les autres sont `docs/i18n/<lang>/LICENSE.md`. Les documents anglais `THIRD_PARTY.md` et `docs/COMMERCIAL_TERMS.md` n’ont pas de suffixe linguistique ; les autres utilisent `.<lang>.md`, avec `lang` parmi `zh-TW`, `ja`, `ko`, `es`, `fr`, `de`, `pt`. L’installateur stocke ces mentions sous `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`, en conservant les chemins relatifs d’origine pour que les liens de licence restent fonctionnels. Les mentions amont à l’intérieur des compétences restent aussi à leur emplacement d’origine. Il n’écrase pas le `LICENSE` ou le `docs/` racine de l’hôte. Les mentions antérieures à une mise à niveau sont sauvegardées avec les compétences d’origine dans la sauvegarde de cette mise à niveau.

`novel-operating-system/INSTALLATION.json` enregistre les chemins source/installé, SHA-256 et nombre d’octets de chaque mention. Après installation, exécutez ce contrôle en lecture seule depuis le ZIP extrait :

```bash
python3 scripts/install_novel_os.py --target /path/to/agent/skills --verify-installed-notices
```

Les fichiers absents ou modifiés entraînent un échec. C’est une vérification d’intégrité locale, pas un substitut à une source de publication fiable. Consultez l’inventaire explicite dans [bundle-contract.fr.md](bundle-contract.fr.md). Les brouillons de discussion ne constituent pas des licences en vigueur et ne sont pas exportés comme conditions officielles.

Les modes de portage manuel B/C/D doivent également livrer ensemble la licence/les conditions commerciales du projet et toutes les mentions amont. Ne copiez pas uniquement `skills/` en omettant les documents de licence.

## Frameworks d’agents/appels d’outils personnalisés (B : adaptateur requis)

Si un framework ne possède pas d’environnement natif `SKILL.md`, mais propose un prompt système, des appels de fonctions et des outils de fichiers/commandes, extraire le ZIP ne suffit pas au déploiement. L’intégrateur doit :

1. Placer `novel-operating-system/SKILL.md` dans les instructions système/développeur et utiliser sa description pour construire un routeur d’intentions.
2. Rendre les seize compétences spécialisées accessibles comme ressources lisibles à la demande par le routeur ; conserver les relations entre dossiers.
3. Pour une œuvre abandonnée ou inachevée, achever d’abord la transmission source/canon/preuves/intention/faisabilité/branches/droits/provenance dans `unfinished-novel-completion`, puis transmettre la branche choisie au rédacteur de fiction longue.
4. Relier les lectures/écritures de fichiers, listes de répertoires, processus Python, espace persistant, `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`, `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` et recherche web à l’API d’outils du framework.
5. Remplacer l’appel `minis-model-use` dans `independent_review.py` par l’intégration deuxième modèle/sous-agent/API de la plateforme. Si aucune n’existe, désactiver cette étape et la noter comme non exécutée.
6. Utiliser la liste d’acceptation du déploiement pour tester la persistance des fichiers entre exécutions et les mises à jour d’état après chaque chapitre.

Consultez [platform-compatibility.fr.md](platform-compatibility.fr.md) pour les points d’intégration courants de LangGraph/CrewAI/AutoGen, MCP, OpenAI/Claude/Gemini et Dify/Flowise/Open WebUI. Tous exigent que l’intégrateur construise un routeur/adaptateur d’outils ; ce ZIP ne peut pas le faire automatiquement dans un compte cloud inconnu.

## Plateformes avec un seul champ d’import de Skill (C : fichiers de connaissances)

Téléversez ou collez tout le répertoire `skills/novel-operating-system/`, références comprises, et gardez les seize autres dossiers au même niveau sous forme de pièces jointes/fichiers de connaissances. Donnez à l’IA cette instruction :

> Lisez d’abord novel-operating-system/SKILL.md. Toutes les compétences voisines sont des collaborateurs requis dans ce système. Sans shell, créez des fichiers de projet Markdown/JSON équivalents et indiquez quels contrôles ne peuvent pas être exécutés. Ne prétendez pas avoir créé des instantanés Git, exécuté des validateurs ou terminé des exports de graphes.

## Plateformes de chat seul/instructions personnalisées (D : repli manuel)

Utilisez `novel-operating-system/SKILL.md` comme instructions principales et le paquet `skills/` complet comme documents de recherche. Ce mode permet de porter les flux de travail, modèles, schémas, formats de sortie, règles et listes de contrôle. Il ne garantit pas la création automatique de fichiers, la persistance entre tours, la validation CLI, l’installation ZIP ou la détection des déclencheurs.

### Contrôles de déploiement pour achever des œuvres inachevées

Lors de la transmission d’une œuvre abandonnée, conservez les fichiers ordinaires du projet de roman ainsi que `completion-brief.md`, `source-manifest.json`, les registres de preuves/intention/versions/branches, `rights-and-publication.md`, `completion-provenance.md`, `completion-state.json` et le contrôle d’achèvement. Les œuvres dont les droits sont inconnus ou non autorisés utilisent par défaut le mode `private-only`/`research` ; ne publiez pas directement leur prose.

Ne placez pas le projet directement dans le ZIP des compétences. Livrez un dossier de projet distinct ou un ZIP propre :

1. Vérifiez d’abord les informations sensibles sur des personnes réelles, sources privées, identifiants d’accès, textes sources non autorisés ou brouillons qui ne doivent pas être partagés.
2. Exécutez `snapshot_project.py`, `deep_consistency.py` et `chapter_gate.py` du système existant ; joignez les résultats à la note de transmission.
3. Indiquez clairement dans `project-brief.md` le dernier chapitre canonique, les chapitres inachevés, l’autorité de dérogation de l’auteur et les risques connus.
4. Après import, le destinataire doit lire la bible du récit, l’état actuel, la chronologie, le registre du lecteur, les fils d’intrigue, le registre des entités et le dernier résumé avant de poursuivre.
