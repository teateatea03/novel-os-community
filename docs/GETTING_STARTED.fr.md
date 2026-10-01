# Configuration locale et installation portable

<!-- language-navigation -->

[繁體中文](GETTING_STARTED.zh-TW.md) | [English](GETTING_STARTED.md) | [日本語](GETTING_STARTED.ja.md) | [한국어](GETTING_STARTED.ko.md) | [Español](GETTING_STARTED.es.md) | **Français** | [Deutsch](GETTING_STARTED.de.md) | [Português](GETTING_STARTED.pt.md)

Ce guide couvre l’environnement local et le paquet portable. L’utilisation et la redistribution sont régies par la [licence](../LICENSE.fr.md) ; les modalités de déclaration et de paiement commerciaux figurent dans [COMMERCIAL_TERMS.fr.md](COMMERCIAL_TERMS.fr.md).

## Langues couvertes

La documentation publique est disponible en huit langues. Les compétences d’exécution, les modèles de fichiers et leurs références techniques conservent actuellement leur langue d’origine. Cette publication de documentation en huit langues ne traduit pas l’environnement d’exécution.

## Choisir un mode

- **Outils locaux :** Python 3.10+ et fichiers UTF-8 persistants. La validation de base, la création de structures de projets et les tests utilisent la bibliothèque standard
- **Environnement d’agent :** les prérequis ci-dessus, plus un hôte capable de charger des paquets `SKILL.md` voisins, de lire/écrire les fichiers du projet et d’exécuter Python. Enregistrez `novel-operating-system` comme point d’entrée
- **Mode documentaire/manuel :** un hôte sans shell ou fichiers persistants peut suivre les modèles, mais ne peut affirmer que les contrôles CLI, l’installation ou l’état durable ont été exécutés

Novel OS n’inclut ni modèle, ni compte d’API, ni service web, ni manuscrit privé. Les sources comportent 18 répertoires de compétences : 17 compétences d’exécution installables (un coordinateur et 16 collaborateurs), plus l’exportateur.

## Vérifier une nouvelle copie de travail

Exécutez ces commandes depuis la racine du dépôt dans un shell POSIX :

```sh
python3 --version
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Utilisez un répertoire de projet privé distinct pour le travail réel. Ne copiez pas de manuscrits ou bases existants dans cette copie de travail. Pour un premier projet synthétique, utilisez l’exemple `mktemp` du README racine. Un `--root` explicite prime sur `NOVEL_PROJECTS_ROOT` ; sans l’un ni l’autre, les initialiseurs utilisent `~/.novel-os/novels`.

## Construire et tester un paquet local

Ces commandes utilisent uniquement les fichiers du dépôt et des répertoires temporaires. Elles n’impliquent aucun téléversement, modèle réel, clé d’API ou recherche externe. Les sorties de construction doivent rester hors de la copie de travail afin d’éviter de commiter accidentellement des contenus générés.

```sh
BUNDLE_WORK="$(mktemp -d)"
INSTALL_WORK="$(mktemp -d)"
EXPORTER="skills/novel-system-exporter/scripts"

python3 "$EXPORTER/build_novel_os_bundle.py" refresh \
  --source-root skills --bundle-root "$BUNDLE_WORK"
python3 "$EXPORTER/build_novel_os_bundle.py" verify \
  --bundle-root "$BUNDLE_WORK/payload"
python3 scripts/privacy_scan.py "$BUNDLE_WORK/payload"
python3 "$EXPORTER/verify_novel_os.py" --profile full \
  --bundle-root "$BUNDLE_WORK/payload" --output "$BUNDLE_WORK/verification.json"
python3 "$EXPORTER/install_novel_os.py" \
  --bundle-root "$BUNDLE_WORK/payload" --target "$INSTALL_WORK" --smoke-test
```

Le profil de vérification complet exécute un pilote synthétique de fiction longue de plus de 100 000 caractères ainsi que les suites locales de non-régression. Il s’agit d’un contrôle local de bon fonctionnement, pas d’une certification de qualité de modèles réels ou multiplateforme. L’installateur refuse d’écraser les compétences existantes sans `--upgrade` explicite ; les mises à niveau créent des sauvegardes locales. Pour votre premier test, ne ciblez pas un répertoire de compétences en service.

Pour créer une archive après la réussite des contrôles :

```sh
python3 "$EXPORTER/build_novel_os_bundle.py" build \
  --bundle-root "$BUNDLE_WORK/payload" \
  --output "$BUNDLE_WORK/novel-os-review.zip"
```

Le manifeste répertorie et calcule l’empreinte de tous les fichiers empaquetés, y compris les versions linguistiques de la licence du projet, des conditions commerciales et du guide des tiers, ainsi que la mention Humanizer-zh inchangée dans la compétence adaptée. Conservez ces mentions avec l’archive et l’installation. L’installateur conserve les mentions du projet dans `novel-operating-system/DISTRIBUTION_NOTICES/` au lieu d’écraser la licence racine de l’hôte.

## Fonctions facultatives

N’installez que ce dont votre hôte a besoin, dans un environnement isolé :

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

Le fichier indique des plages de compatibilité, pas un verrouillage reproductible. Si vous activez une intégration facultative, choisissez et testez sa version exacte et examinez ses conditions amont. Aucune dépendance facultative n’est nécessaire au parcours de base ci-dessus.

- NetworkX active les algorithmes de graphes/GraphML facultatifs ; Graphify s’installe séparément pour ses exportateurs supplémentaires
- PyYAML permet les entrées YAML de projection des PNJ ; MCP et son serveur Instagram externe sont des intégrations facultatives
- La revue indépendante par modèle exige un remplacement propre à l’hôte de `minis-model-use` hors de son hôte d’origine. En son absence, indiquez qu’elle n’a pas été exécutée
- `lieflat-less-ai-tone` n’est pas inclus. Sa source/licence doit être vérifiée séparément ; sans lui, utilisez le flux intégré de voix humaine et indiquez que la passe supplémentaire n’a pas été exécutée

Consultez [THIRD_PARTY.fr.md](../THIRD_PARTY.fr.md), la [compatibilité des plateformes](../skills/novel-system-exporter/references/platform-compatibility.fr.md) et le [contrat d’adaptateur hôte](../skills/novel-system-exporter/references/host-adapter-contract.fr.md). Les tests Windows/d’hôte natif et de services facultatifs constituent des travaux d’acceptation distincts ; un test de bon fonctionnement Linux ne les vérifie pas.
