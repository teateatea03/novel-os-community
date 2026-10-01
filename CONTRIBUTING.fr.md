# Contribuer à Novel OS

<!-- language-navigation -->

[繁體中文](CONTRIBUTING.zh-TW.md) | [English](CONTRIBUTING.md) | [日本語](CONTRIBUTING.ja.md) | [한국어](CONTRIBUTING.ko.md) | [Español](CONTRIBUTING.es.md) | **Français** | [Deutsch](CONTRIBUTING.de.md) | [Português](CONTRIBUTING.pt.md)

[Modèle de demande de fusion](.github/PULL_REQUEST_TEMPLATE/fr.md)

Merci de contribuer à l’amélioration de Novel OS. Les contributions doivent préserver les conditions commerciales de code source accessible du projet et son périmètre de confidentialité.

## La confidentialité et les droits conditionnent la publication

Ne contribuez que des éléments réutilisables du système que vous êtes en droit de partager. Ne soumettez **pas** :

- de manuscrits, brouillons de chapitres, sessions interactives, états narratifs, retours d’auteur ou données de test de projets privés ;
- de bases de personnages, d’univers ou de recherche, ni de dossiers sur des personnes réelles ;
- de mémoires de conversation, journaux locaux, sauvegardes générées, identifiants d’accès, cookies, chemins d’appareils ou points de terminaison privés ;
- de textes sources protégés, ressources divulguées sans autorisation, copies derrière un péage ou code tiers sans licence compatible ni attribution.

Utilisez des données de test fictives, minimales et clairement synthétiques. Ne vous contentez pas de renommer des données privées réelles.

Construisez les paquets et créez les projets narratifs hors de la copie de travail des sources. Un environnement virtuel à la racine est permis pour le développement local, mais ne doit pas être commité.

## Avant d’ouvrir une pull request

```sh
python3 scripts/privacy_scan.py .
python3 -m compileall -q skills scripts
python3 scripts/validate_json.py .
python3 scripts/run_tests.py
```

Le scanner et le validateur JSON examinent les fichiers de la copie de travail, y compris ceux qui ne sont pas suivis ou sont ignorés par Git. Ils excluent les métadonnées Git, les caches Python/de test générés et les environnements virtuels confirmés à la racine ; les fichiers suivis restent inclus. Ils rejettent les liens symboliques, fichiers illisibles et sources non UTF-8. Examinez séparément le diff de l’index : un contrôle réussi de la copie de travail n’est pas une analyse de l’index, de l’historique Git ou des objets conservés par GitHub.

Inspectez également :

```sh
git diff --cached --name-only
git diff --cached
```

Expliquez dans la pull request toute nouvelle dépendance, source externe, production générée ou particularité de plateforme.

## Attentes relatives aux modifications

- Gardez le code et la documentation portables ; les valeurs par défaut des plateformes doivent pouvoir être remplacées
- Ajoutez ou mettez à jour les tests pour les changements de comportement
- Préservez l’autorité du canon/de l’auteur et les contrats de sécurité qui bloquent en cas d’incertitude
- Gardez les exemples publics synthétiques et exempts de données permettant d’identifier une personne
- N’affaiblissez pas silencieusement les contrôles de confidentialité, de provenance ou de validation

## Modèle de commit et de revue

Utilisez des commits ciblés avec un résumé à l’impératif. Les pull requests doivent être examinées par le mainteneur. Les correctifs de sécurité ou de confidentialité doivent passer par un signalement privé plutôt que par une issue publique.

## Licence

Ne contribuez que des éléments que vous êtes en droit de distribuer sous la [licence](LICENSE.fr.md). Identifiez les modifications, conservez la même licence pour les changements dérivés du projet et préservez toutes les mentions tierces requises. Cela ne transfère pas votre droit d’auteur au mainteneur. Les pull requests publiques ne doivent contenir ni rapports financiers, ni détails de paiement, ni créations privées.
