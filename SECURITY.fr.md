# Politique de sécurité et de confidentialité

<!-- language-navigation -->

[繁體中文](SECURITY.zh-TW.md) | [English](SECURITY.md) | [日本語](SECURITY.ja.md) | [한국어](SECURITY.ko.md) | [Español](SECURITY.es.md) | **Français** | [Deutsch](SECURITY.de.md) | [Português](SECURITY.pt.md)

## Versions prises en charge

Les correctifs de sécurité et de confidentialité ciblent la branche `main` actuelle.

## Signalement

Ne créez pas d’issues publiques contenant des données personnelles, identifiants d’accès, manuscrits privés, journaux de session, éléments narratifs inédits ou dossiers de recherche. Utilisez le signalement privé de vulnérabilités lorsqu’il est activé. Si aucun contact privé n’est disponible, ouvrez une issue demandant au mainteneur un canal de signalement privé, sans détails sensibles.

## Périmètre des contributions

Les contributeurs ne doivent soumettre que des éléments qu’ils sont en droit de partager. Ne commitez jamais :

- de clés d’API, mots de passe, jetons d’accès, clés SSH, cookies, fichiers d’environnement ou chemins d’appareils ;
- de conversations privées, mémoires d’agents, journaux, sauvegardes ou exports ;
- de fictions inédites, états de sessions interactives ou données personnelles de recherche ;
- de données sur des personnes réelles qui ne conviennent pas à une redistribution publique.

## Avant de publier une modification

1. Examinez `git diff --cached --name-only`.
2. Exécutez `python3 scripts/privacy_scan.py .`.
3. Examinez manuellement chaque résultat ; n’en écartez aucun sans justification écrite.
4. Confirmez que chaque fichier inclus appartient au système réutilisable, et non à un projet actif ou à un jeu de données privé.

## Procédure de divulgation

Si des éléments privés sont commités ou exposés, interrompez toute nouvelle distribution, rendez le dépôt privé si nécessaire, révoquez les identifiants d’accès concernés, conservez les preuves pour examen et supprimez ces éléments des objets Git actuels et historiques avant de rouvrir l’accès.
