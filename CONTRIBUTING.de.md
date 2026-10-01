# Zu Novel OS beitragen

<!-- language-navigation --> [繁體中文](CONTRIBUTING.zh-TW.md) | [English](CONTRIBUTING.md) | [日本語](CONTRIBUTING.ja.md) | [한국어](CONTRIBUTING.ko.md) | [Español](CONTRIBUTING.es.md) | [Français](CONTRIBUTING.fr.md) | **Deutsch** | [Português](CONTRIBUTING.pt.md)

[Vorlage für Pull Requests](.github/PULL_REQUEST_TEMPLATE/de.md)

Danke, dass Sie Novel OS verbessern helfen. Beiträge müssen die kommerziellen Source-available-Bedingungen und die Datenschutzgrenze des Projekts wahren.

## Datenschutz und Rechte sind Veröffentlichungsvoraussetzungen

Tragen Sie nur wiederverwendbares Systemmaterial bei, das Sie weitergeben dürfen. Reichen Sie **nicht** ein:

- Manuskripte, Kapitelentwürfe, interaktive Sitzungen, Erzählzustände, Autorenfeedback oder Testdaten privater Projekte;
- Figuren-, Welten- oder Recherchedatenbanken oder Datensätze über reale Personen;
- Chat-Erinnerungen, lokale Protokolle, erzeugte Sicherungen, Zugangsdaten, Cookies, Gerätepfade oder private Endpunkte;
- geschützte Quelltexte, unbefugt veröffentlichte Materialien, Kopien hinter Bezahlschranken oder Fremdcode ohne passende Lizenz und Urheberangabe.

Nutzen Sie erfundene, minimale und eindeutig synthetische Testdaten. Benennen Sie echte private Daten nicht bloß um.

Erstellen Sie Pakete und Geschichtenprojekte außerhalb der Quellcode-Arbeitskopie. Eine virtuelle Umgebung im Stammverzeichnis ist für lokale Entwicklung erlaubt, darf aber nicht committet werden.

## Vor dem Öffnen eines Pull Requests

```sh
python3 scripts/privacy_scan.py .
python3 -m compileall -q skills scripts
python3 scripts/validate_json.py .
python3 scripts/run_tests.py
```

Scanner und JSON-Validierer prüfen Arbeitskopie-Dateien einschließlich unversionierter und durch Git ignorierter Dateien. Ausgenommen sind Git-Metadaten, erzeugte Python-/Test-Caches und bestätigte virtuelle Umgebungen im Stammverzeichnis; versionierte Dateien bleiben im Prüfbereich. Symbolische Links, unlesbare Dateien und Nicht-UTF-8-Quellen werden abgelehnt. Prüfen Sie den vorgemerkten Diff gesondert: Eine bestandene Arbeitskopie-Prüfung ist keine Prüfung des Git-Index, des Git-Verlaufs oder durch GitHub aufbewahrter Objekte.

Prüfen Sie außerdem:

```sh
git diff --cached --name-only
git diff --cached
```

Erläutern Sie neue Abhängigkeiten, externe Quellen, erzeugte Artefakte oder plattformspezifisches Verhalten im Pull Request.

## Erwartungen an Änderungen

- Code und Dokumentation müssen portabel bleiben; Plattformvorgaben müssen überschreibbar sein
- Ergänzen oder aktualisieren Sie Tests bei Verhaltensänderungen
- Bewahren Sie die Autorität des Kanons/Autors und Sicherheitsverträge, die bei Unklarheit blockieren
- Öffentliche Beispiele müssen synthetisch und frei von personenbezogenen Identifikationsdaten bleiben
- Schwächen Sie Datenschutz-, Herkunfts- oder Validierungsschranken nicht stillschweigend ab

## Commit- und Prüfmodell

Verwenden Sie fokussierte Commits mit einer Zusammenfassung im Imperativ. Pull Requests müssen vom Maintainer geprüft werden. Sicherheits- oder Datenschutzkorrekturen sollten privat statt über ein öffentliches Issue gemeldet werden.

## Lizenzierung

Tragen Sie nur Material bei, das Sie unter der [Lizenz](LICENSE.de.md) verbreiten dürfen. Kennzeichnen Sie Änderungen, behalten Sie dieselbe Lizenz für vom Projekt abgeleitete Änderungen bei und bewahren Sie alle erforderlichen Hinweise Dritter. Ihr Urheberrecht geht dadurch nicht auf den Maintainer über. Öffentliche Pull Requests dürfen keine Finanzberichte, Zahlungsdetails oder privaten kreativen Inhalte enthalten.
