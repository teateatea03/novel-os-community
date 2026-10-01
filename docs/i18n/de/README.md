# Novel OS

<!-- language-navigation -->

[繁體中文](../zh-TW/README.md) | [English](../../../README.md) | [日本語](../ja/README.md) | [한국어](../ko/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | **Deutsch** | [Português](../pt/README.md)

Novel OS ist eine wiederverwendbare Sammlung von KI-Agenten-Skills und lokalen Python-Werkzeugen für lange Romane, interaktive Fiktion, Kontinuität, Figuren- und Weltenrecherche, konsistentes Verhalten, Graphen mit Herkunftsnachweisen und narrative Validierung.

> **Lizenz:** Quellcode verfügbar unter der [kommerziellen Gewinnbeteiligungslizenz von Novel OS](LICENSE.md), Copyright teateatea03. Nichtkommerzielle Nutzung ist kostenlos; bei kommerzieller Nutzung sind 0,5 % des positiven jährlichen Nettogewinns aus den betreffenden Produkten, Diensten und Romanen zu zahlen. Änderungen und Weiterverbreitung behalten dieselben Bedingungen und Hinweise bei. Dies ist keine MIT-, GPL- oder OSI-Open-Source-Lizenz.

Einzelheiten zur kommerziellen Nutzung und Zahlung mit den beiden akzeptierten Token stehen unter [kommerzielle Gewinnbeteiligung und Zahlungsinformationen](COMMERCIAL_TERMS.md). Rechte an Romanen und anderen Ergebnissen der Nutzer gehen nicht auf den Systemeigentümer über.

## Sprachumfang

Die öffentliche Dokumentation ist in acht Sprachen verfügbar. Laufzeit-Skills, Vorlagen und ihre technischen Referenzen behalten derzeit ihre ursprüngliche Sprache. Diese Veröffentlichung der Dokumentation in acht Sprachen übersetzt nicht die Laufzeitumgebung.

## Datenschutzgrenze

Dieses Quellcode-Repository schließt bewusst Folgendes aus:

- Manuskripte, Kapitelentwürfe, interaktive Spielsitzungen, Erzählzustände und Datensätze mit Autorenfeedback;
- Datenbanken zu Figuren, Welten, besonderen Objekten und Recherchen über reale Personen;
- Chat-Erinnerungen, gerätelokale Zustände, Sicherungen, Exporte, Zugangsdaten, private Endpunkte und Umgebungsdateien.

Öffentliche Beispiele und Testdaten müssen synthetisch sein. Vor jedem Push oder jeder Veröffentlichung sind der Datenschutzscanner auszuführen und die zum Commit vorgesehene Dateiliste zu prüfen.

## Repository-Struktur

- `skills/`: wiederverwendbare Skill-Pakete, Skripte, Vorlagen und synthetische Testdaten
- `scripts/`: Werkzeuge für Datenschutz, Validierung und Tests
- `docs/`: Dokumentation zu Projektregeln und Veröffentlichungsgrenzen

Der Quellbaum enthält 18 Skill-Verzeichnisse: 17 installierbare Laufzeit-Skills (ein Koordinator und 16 Mitwirkende) sowie den Paketexporter. Der Exporter ist ein Paketierungswerkzeug und wird nicht als Laufzeit-Skill installiert.

## Voraussetzungen

- Python 3.10+
- Dauerhafter UTF-8-Speicher
- Kernabläufe ausschließlich mit der Standardbibliothek
- Optionale Funktionen: siehe `requirements-optional.txt` und [THIRD_PARTY.md](THIRD_PARTY.md)

Optionale Python-Abhängigkeiten in einer isolierten Umgebung installieren:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

Die Graphify-Integration ist optional und wird gemäß der Dokumentation des Ursprungsprojekts separat installiert.

## Erster lokaler Durchlauf (ohne Modell oder Netzwerk)

Verwenden Sie Python 3.10+ und Git vom Stammverzeichnis des Repositorys aus. Die Kernprüfungen und die synthetische Demo benötigen keine optionalen Pakete, API-Schlüssel oder privaten Manuskripte:

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 scripts/run_tests.py

# Den erzeugten Projektzustand außerhalb des Quellcode-Repositorys halten.
DEMO_ROOT="$(mktemp -d)"
python3 skills/long-form-novel-writer/scripts/init_novel_project.py \
  --title "Synthetic Demo" --slug synthetic-demo --root "$DEMO_ROOT"
python3 skills/knowledge-relationship-graph/scripts/relationship_graph.py \
  validate --root "$DEMO_ROOT/synthetic-demo"
```

Der Initialisierer erstellt ein leeres Planungs- und Zustandsgerüst; er erzeugt keinen Roman und ruft kein Modell auf. Bewahren Sie eigene Geschichten in einem separaten privaten Verzeichnis auf. Der Initialisierer verweigert das Überschreiben eines bestehenden Projekts.

Auf einem Agenten-Host müssen die Laufzeit-Skills in benachbarten Verzeichnissen bleiben und `novel-operating-system` als Einstiegspunkt registriert werden. Hosts ohne dauerhafte Dateien oder Python-Prozessausführung unterstützen nur den Dokument-/manuellen Modus. Der [getestete lokale Build- und Installationsleitfaden](GETTING_STARTED.md) enthält Paketbefehle, Funktionstests, optionale Integrationen und Plattformgrenzen.

## Überprüfung

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Die Novel-Judge-Testsuite muss über `scripts/run_tests.py` ausgeführt werden; das einzelne Aufrufen ihrer Testdateien mit paketrelativen Importen wird nicht unterstützt.

Datenschutz- und JSON-Prüfungen untersuchen Quelldateien einschließlich unversionierter und durch Git ignorierter Dateien. Git-Metadaten, erzeugte Python-/Test-Caches und bestätigte virtuelle Umgebungen im Stammverzeichnis sind ausgenommen; versionierte Dateien werden weiterhin geprüft. Symbolische Links, unlesbare Dateien und Nicht-UTF-8-Text führen zur sicheren Ablehnung. Erzeugte Pakete und Erzählzustände gehören nicht in diese Arbeitskopie. Der Scanner meldet Dateinamen und Fundkategorien, niemals die gefundenen Inhalte; er ist eine heuristische Prüfung, kein Datenschutzbeweis und keine Verlaufsanalyse.

## Plattformpfade

Die Dokumentation verwendet Platzhalter wie `<SKILLS_ROOT>`, `<WORKSPACE_ROOT>` und `<NOVEL_PROJECTS_ROOT>`. Konfigurieren Sie diese für die Hostplattform. Ausführbare Initialisierer verwenden standardmäßig `~/.novel-os/novels`, sofern weder `NOVEL_PROJECTS_ROOT` noch ein ausdrückliches `--root` angegeben ist.

## Sicherheit und Rechercheumfang

Die Recherche-Skills sind für rechtmäßig öffentlich zugängliches Material ausgelegt und dürfen keine Anmeldeschranken, CAPTCHAs, Bezahlschranken, Robots-/Zugriffskontrollen oder Plattformbeschränkungen umgehen. Recherchen über reale Personen benötigen Herkunftsnachweise und dürfen ungeprüfte oder sensible Informationen nicht als Tatsachen darstellen.

## Projektregeln

Lesen Sie:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [THIRD_PARTY.md](THIRD_PARTY.md)

## Lizenz und Beiträge

Lesen Sie vor kommerzieller Nutzung die [Lizenz](LICENSE.md) und [Zahlungsbedingungen](COMMERCIAL_TERMS.md). Einbezogen wird nur der positive jährliche Nettogewinn aus den betreffenden Produkten, Diensten und Romanen; andere Geschäftsbereiche sind ausgeschlossen. Die Meldung erfolgt eigenverantwortlich ohne versteckte Telemetrie oder automatische Einziehung. Drittkomponenten behalten ihre eigenen Lizenzen und Hinweise.

Kommerzielle Nutzer erkennen vor der Nutzung die Lizenzversion ausdrücklich an. Beginnen Sie mit einem GitHub-Issue ohne private oder finanzielle Angaben, um einen privaten Meldekanal zu vereinbaren; veröffentlichen Sie keine Finanzaufstellungen oder Zahlungsbelege. Regeln für Beiträge und Weiterverbreitung stehen in [CONTRIBUTING.md](CONTRIBUTING.md).

## Grenzen der Überprüfung

Kerntests unter Linux und synthetische Installationsprüfungen werden bereitgestellt. Optionale Graphify-/MCP-/Instagram-Dienste, reale Modelle, native Agentenintegrationen und eine plattform- und Python-versionsübergreifende Matrix sind nicht zertifiziert. Beispielberichte über Modelle sind synthetische Veranschaulichungen und kein Nachweis gemessener Anbieter- oder Modellleistung.
