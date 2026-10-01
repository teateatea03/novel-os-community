# Lokale Einrichtung und portable Installation

<!-- language-navigation --> [繁體中文](GETTING_STARTED.zh-TW.md) | [English](GETTING_STARTED.md) | [日本語](GETTING_STARTED.ja.md) | [한국어](GETTING_STARTED.ko.md) | [Español](GETTING_STARTED.es.md) | [Français](GETTING_STARTED.fr.md) | **Deutsch** | [Português](GETTING_STARTED.pt.md)

Dieser Leitfaden beschreibt die lokale Laufzeitumgebung und das portable Paket. Nutzung und Weiterverbreitung unterliegen der [Lizenz](../LICENSE.de.md); Angaben zur kommerziellen Meldung und Zahlung stehen in [COMMERCIAL_TERMS.de.md](COMMERCIAL_TERMS.de.md).

## Sprachumfang

Die öffentliche Dokumentation ist in acht Sprachen verfügbar. Laufzeit-Skills, Vorlagen und ihre technischen Referenzen behalten derzeit ihre ursprüngliche Sprache. Diese Veröffentlichung der Dokumentation in acht Sprachen übersetzt nicht die Laufzeitumgebung.

## Modus auswählen

- **Lokale Werkzeuge:** Python 3.10+ und dauerhafte UTF-8-Dateien. Kernvalidierung, Projektgerüste und Tests nutzen die Standardbibliothek
- **Agentenlaufzeit:** die genannten Voraussetzungen plus ein Host, der benachbarte `SKILL.md`-Pakete laden, Projektdateien lesen/schreiben und Python ausführen kann. Registrieren Sie `novel-operating-system` als Einstiegspunkt
- **Dokument-/manueller Modus:** Ein Host ohne Shell oder dauerhafte Dateien kann den Vorlagen folgen, darf aber nicht behaupten, CLI-Prüfschranken, Installation oder dauerhafter Zustand seien ausgeführt worden

Novel OS enthält kein Modell, API-Konto, keinen Webdienst und kein privates Manuskript. Es gibt 18 Skill-Quellverzeichnisse: 17 installierbare Laufzeit-Skills (ein Koordinator und 16 Mitwirkende) sowie den Exporter.

## Frische Arbeitskopie prüfen

Führen Sie diese Befehle in einer POSIX-Shell vom Repository-Stamm aus aus:

```sh
python3 --version
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Verwenden Sie für echte Arbeit ein separates privates Projektverzeichnis. Kopieren Sie keine vorhandenen Manuskripte oder Datenbanken in diese Arbeitskopie. Für ein synthetisches erstes Projekt verwenden Sie das `mktemp`-Beispiel im Stamm-README. Ein ausdrückliches `--root` hat Vorrang vor `NOVEL_PROJECTS_ROOT`; fehlt beides, verwenden die Projektinitialisierer `~/.novel-os/novels`.

## Lokales Paket bauen und testen

Diese Befehle verwenden nur Repository-Dateien und temporäre Verzeichnisse. Es erfolgen keine Uploads, Aufrufe realer Modelle, API-Schlüsselnutzung oder externen Recherchen. Build-Ausgaben müssen außerhalb der Quellcode-Arbeitskopie bleiben, damit erzeugte Paketinhalte nicht versehentlich committet werden.

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

Das vollständige Prüfprofil führt einen synthetischen Langform-Pilotlauf mit mehr als 100.000 Zeichen sowie lokale Regressionstests aus. Dies ist eine lokale Korrektheitsprüfung, keine Zertifizierung realer Modellqualität oder plattformübergreifender Funktion. Der Installer verweigert das Überschreiben vorhandener Skills ohne ausdrückliches `--upgrade`; Upgrades erstellen lokale Sicherungen. Verwenden Sie beim ersten Test kein produktives Skill-Verzeichnis als Ziel.

Nach erfolgreichen Prüfungen kann ein Archiv erstellt werden:

```sh
python3 "$EXPORTER/build_novel_os_bundle.py" build \
  --bundle-root "$BUNDLE_WORK/payload" \
  --output "$BUNDLE_WORK/novel-os-review.zip"
```

Das Manifest listet alle Paketdateien mit Hashwerten auf, einschließlich der Sprachfassungen von Projektlizenz, kommerziellen Bedingungen und Drittanbieterübersicht sowie des unveränderten Humanizer-zh-Hinweises im angepassten Skill. Bewahren Sie diese Hinweise mit Archiv und Installation auf. Der Installer legt projekweite Hinweise unter `novel-operating-system/DISTRIBUTION_NOTICES/` ab, statt die Stammlizenz des Hosts zu überschreiben.

## Optionale Funktionen

Installieren Sie in einer isolierten Umgebung nur das, was Ihr Host benötigt:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

Die Datei nennt Kompatibilitätsbereiche, keine reproduzierbare Versionssperre. Wenn Sie eine optionale Integration aktivieren, wählen und testen Sie deren genaue Version und prüfen Sie die Ursprungsbedingungen. Für den oben beschriebenen Kernablauf ist keine optionale Abhängigkeit erforderlich.

- NetworkX ermöglicht optionale Graphalgorithmen/GraphML; Graphify wird für zusätzliche Exporter separat installiert
- PyYAML ermöglicht YAML-Eingaben zur NPC-Projektion; MCP und sein externer Instagram-Server sind optionale Integrationen
- Unabhängige Modellprüfung benötigt außerhalb des ursprünglichen Hosts einen hostspezifischen Ersatz für `minis-model-use`. Wenn er fehlt, kennzeichnen Sie die Prüfung als nicht ausgeführt
- `lieflat-less-ai-tone` wird nicht mitgeliefert. Quelle/Lizenz müssen separat geprüft werden; ohne ihn verwenden Sie den eingebauten Ablauf für menschliche Erzählstimme und kennzeichnen den zusätzlichen Durchlauf als nicht ausgeführt

Siehe [THIRD_PARTY.de.md](../THIRD_PARTY.de.md), [Plattformkompatibilität](../skills/novel-system-exporter/references/platform-compatibility.de.md) und den [Hostadapter-Vertrag](../skills/novel-system-exporter/references/host-adapter-contract.de.md). Windows-/native Hosttests und Tests optionaler Dienste sind gesonderte Abnahmeaufgaben; ein Linux-Funktionstest prüft sie nicht.
