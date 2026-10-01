# Sicherheits- und Datenschutzrichtlinie

<!-- language-navigation --> [繁體中文](SECURITY.zh-TW.md) | [English](SECURITY.md) | [日本語](SECURITY.ja.md) | [한국어](SECURITY.ko.md) | [Español](SECURITY.es.md) | [Français](SECURITY.fr.md) | **Deutsch** | [Português](SECURITY.pt.md)

## Unterstützte Versionen

Sicherheits- und Datenschutzkorrekturen beziehen sich auf den aktuellen Branch `main`.

## Meldungen

Erstellen Sie keine öffentlichen Issues mit personenbezogenen Daten, Zugangsdaten, privaten Manuskripten, Sitzungsprotokollen, unveröffentlichtem Erzählmaterial oder Rechercheunterlagen. Nutzen Sie private Schwachstellenmeldungen, sofern aktiviert. Ist kein privater Kontakt verfügbar, bitten Sie in einem Issue um einen privaten Meldekanal des Maintainers, ohne sensible Details anzugeben.

## Beitragsgrenze

Mitwirkende dürfen nur Material einreichen, das sie teilen dürfen. Committen Sie niemals:

- API-Schlüssel, Passwörter, Zugriffstoken, SSH-Schlüssel, Cookies, Umgebungsdateien oder Gerätepfade;
- private Gespräche, Agentenerinnerungen, Protokolle, Sicherungen oder Exporte;
- unveröffentlichte Fiktion, Zustände interaktiver Sitzungen oder persönliche Recherchedaten;
- Daten über reale Personen, die sich nicht für öffentliche Weiterverbreitung eignen.

## Vor der Veröffentlichung einer Änderung

1. Prüfen Sie `git diff --cached --name-only`.
2. Führen Sie `python3 scripts/privacy_scan.py .` aus.
3. Untersuchen Sie jeden Fund manuell; unterdrücken Sie keinen Fund ohne schriftliche Begründung.
4. Bestätigen Sie, dass jede enthaltene Datei zum wiederverwendbaren System gehört und nicht zu einem laufenden Projekt oder privaten Datensatz.

## Vorgehen bei Offenlegung

Wenn privates Material committet oder offengelegt wurde, stoppen Sie die weitere Verbreitung, stellen Sie das Repository nötigenfalls auf privat, widerrufen Sie betroffene Zugangsdaten, bewahren Sie Belege zur Prüfung auf und entfernen Sie das Material aus aktuellen und historischen Git-Objekten, bevor Sie den Zugang wieder öffnen.
