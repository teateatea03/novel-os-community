# Vertrag für das portable Novel-OS-Paket

<!-- language-navigation -->

[繁體中文](bundle-contract.md) | [English](bundle-contract.en.md) | [日本語](bundle-contract.ja.md) | [한국어](bundle-contract.ko.md) | [Español](bundle-contract.es.md) | [Français](bundle-contract.fr.md) | **Deutsch** | [Português](bundle-contract.pt.md)

Im Paketlayout `novel-os-portable-v<version>/` enthält `skills/` einen Koordinator und 16 spezialisierte Skills. `public-web-research/` bietet sichere, fortsetzbare öffentliche HTTP(S)-Beschaffung und die Vorbereitung von Evidence-Run-Kandidaten. `novel-model-capability-compatibility/` verwaltet die Verträge für Modellfähigkeitsproben/L0–L5/Rückfallmodi. `novel-reality-state-engine/` verwaltet die Prüfwerkzeuge für Ereignis → Zustand → Fähigkeit → Verhalten → Prosa. `novel-world-database-builder/` verwaltet Weltdatenbankschemata, Stapelvorlagen, Übergabepakete und Abfragespezifikationen. `special-object-database-builder/` verwaltet Versions-, Fähigkeits-, Spezifikations- und Lebenszyklusschemata für Requisiten/Rüstungen/Mechas/Geräte.

```text
novel-os-portable-v<version>/
├── MANIFEST.json
├── LICENSE
├── LICENSE.zh-TW.md
├── LICENSE.ja.md
├── LICENSE.ko.md
├── LICENSE.es.md
├── LICENSE.fr.md
├── LICENSE.de.md
├── LICENSE.pt.md
├── THIRD_PARTY.md
├── THIRD_PARTY.zh-TW.md
├── THIRD_PARTY.ja.md
├── THIRD_PARTY.ko.md
├── THIRD_PARTY.es.md
├── THIRD_PARTY.fr.md
├── THIRD_PARTY.de.md
├── THIRD_PARTY.pt.md
├── docs/
│   ├── COMMERCIAL_TERMS.md
│   ├── COMMERCIAL_TERMS.zh-TW.md
│   ├── COMMERCIAL_TERMS.ja.md
│   ├── COMMERCIAL_TERMS.ko.md
│   ├── COMMERCIAL_TERMS.es.md
│   ├── COMMERCIAL_TERMS.fr.md
│   ├── COMMERCIAL_TERMS.de.md
│   └── COMMERCIAL_TERMS.pt.md
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
│   ├── novel-operating-system/      # obligatorischer einziger Einstiegspunkt
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

`MANIFEST.json` enthält Paketschema/-version, Paketliste, Versionen der Quell-Skills, SHA-256-Hash und Bytezahl jeder Paketdatei, ein eigenes `distribution_notices`-Inventar, Build-Zeit, Ausschlüsse und Laufzeitabhängigkeiten. Die Nutzdaten enthalten auch eine portable Kopie des **Plattformkompatibilitätsleitfadens**. Sie enthalten keine Geheimnisse, lokalen absoluten Pfade, Geschichtenprojekte, Kontokonfigurationen oder Weltdatenbanken.

## Aufbewahrung von Lizenzen und Hinweisen

- `--source-root` bezeichnet das Quellverzeichnis `skills/`. Sein Repository-Elternverzeichnis muss die acht Fassungen von `LICENSE`, `THIRD_PARTY.md` und `docs/COMMERCIAL_TERMS.md` enthalten, also die oben ausdrücklich aufgeführten 24 Dokumente. Refresh verweigert fehlende erforderliche Dokumente, Nichtdateien oder symbolische Links, bevor der Paketinhalt geändert wird. Dies sind vom Eigentümer gewählte Projektbedingungen; Ursprungshinweise behalten ihren eigenen Geltungsbereich.
- Die zusätzliche ausdrückliche Erlaubnisliste umfasst `LICENSE.md`, `LICENSE.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt` und `docs/COMMERCIAL_LICENSE.md`. Vorhandene Dateien werden bytegenau kopiert. Andere Dateien aus dem Stamm-`docs/` werden nicht exportiert. Insbesondere ist `docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md` ein unwirksamer Diskussionsentwurf und wird nicht als Lizenz oder kommerzielle Bedingung exportiert.
- Skill-lokale Dateien `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, `COPYING.md`, `COPYING.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt`, `THIRD_PARTY.md` sowie alle Dateien unter `THIRD_PARTY_LICENSES/` bleiben im Skill erhalten und werden in `distribution_notices` erfasst. Refresh gleicht ihre Bytes mit der Quelle ab; Build und Installation verwerfen fehlende Deklarationen, fehlende Dateien, veränderte Bytes, unsichere Pfade oder fehlende Hash-Einträge.
- Das vorhandene angepasste Humanizer-zh-Material benötigt ausdrücklich `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`. Solange dieses Material verteilt wird, darf die Datei weder aus der Quelle noch aus dem Manifest entfernt werden.
- Neue rechtlich erforderliche Dateinamen müssen vor der Veröffentlichung in diesen ausdrücklichen Vertrag aufgenommen werden. Verlassen Sie sich nicht auf Links zu nicht mitgelieferten Dokumenten. Refresh entfernt veraltete optionale Stammhinweis-Kopien aus bestehenden Nutzdaten.
- Das ZIP erhält dieselbe stammrelative Struktur. Bei der Installation liegen sämtliche Hinweisdokumente unter `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`; Pfade wie `docs/COMMERCIAL_TERMS.md` und `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt` bleiben erhalten, damit relative Lizenzlinks funktionieren. Skill-lokale Ursprungshinweise bleiben auch in ihren ursprünglichen Verzeichnissen. Der Installer schreibt niemals `<target>/LICENSE`, `<target>/THIRD_PARTY.md` oder `<target>/docs/`.
- `novel-operating-system/INSTALLATION.json` erfasst ursprünglichen Pfad, Installationspfad, Dokumentkopiepfad, SHA-256 und Bytezahl jedes installierten Hinweises. Vorbereitung und abschließende Installation prüfen gegebenenfalls beide Kopien. Upgrades übernehmen den vorherigen Koordinator samt Hinweisen in die normale Skill-Sicherung und stellen ihn bei Fehlern wieder her. `DISTRIBUTION_NOTICES/` im Koordinator ist für installerverwaltete Dokumente reserviert.
- Zur Nachprüfung einer Installation führen Sie aus dem entpackten Paket `python3 scripts/install_novel_os.py --target <SKILLS_ROOT> --verify-installed-notices` aus. Dieser Nur-Lese-Modus prüft Stamm- und Ursprungshinweise gegen den Installationseintrag. Hashwerte belegen lokale Integrität, nicht Authentizität gegenüber einem Angreifer, der sowohl Dateien als auch Einträge ersetzen kann; bewahren Sie eine vertrauenswürdige Veröffentlichung separat auf.

## Angabe der Laufzeitabhängigkeiten

Jede Veröffentlichung muss alle 32 ausdrücklich erlaubten Portabilitätsreferenzen liefern: die vier Familien `portable-install`, `platform-compatibility`, `host-adapter-contract` und `bundle-contract`, jeweils in den oben unter `references/` aufgeführten acht Sprachfassungen. Traditionelles Chinesisch hat keinen Suffix; Englisch verwendet `.en.md`, die sechs weiteren Sprachen `.ja.md`, `.ko.md`, `.es.md`, `.fr.md`, `.de.md`, `.pt.md`. Beschreiben Sie diese Stufen wahrheitsgemäß:

- **Grundlegender Dokumentablauf:** ein LLM, das die Skill-Dateien lesen kann; keine Codeausführung erforderlich.
- **Automatisierter lokaler Ablauf (v2.7):** Python 3.10+ (3.11+ empfohlen), Shell/Prozessstarter, dauerhafte UTF-8-Dateien, Erkennung mehrerer Skills oder gleichwertiger Router, Branch-Sperre, einzige Produktionsautorität `ProjectRuntimeAdapter.commit()`, sieben Gates, typisierte semantische Ereignisse, Projektbereitschaft/Projektionsaktualität, Autorenfeedback-Quality-Eval und Entpackfunktion bei ZIP-Verteilung. Weltdatenbanken benötigen zusätzlich beschreibbare `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`; Spezialobjektdatenbanken beschreibbare `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT`.
- **Grapherweiterung:** `networkx` für Graphdurchläufe; `graphifyy` und `networkx` für Graphify-HTML-/Community-/Cypher-Exporte. Das Graph-JSON bleibt ohne beide Pakete verwendbar.
- **Optionale Integrationen:** Git für Commits, Web-/Browserwerkzeuge für Quellenrecherche und ein hostspezifischer Zweitmodell-/Unteragentenadapter für unabhängige Prüfung. `independent_review.py` bleibt bis zum Ersatz Minis-spezifisch.

Für die lokale Basis sind weder Node.js noch Datenbankserver, API-Schlüssel oder Internetverbindung erforderlich. Ein Framework ohne Datei-/Prozesszugriff ist als Dokument-/manueller Modus und nicht als vollständige automatische Installation zu beschreiben.

## Build-Richtlinie

- Die Nutzdaten müssen **17** zugelassene Skill-Verzeichnisse (ein Koordinator + 16 spezialisierte Skills), Portabilitätsreferenzen, Installations-/Build-Skripte und gewöhnliche Text-/Quell-/Testdaten-/Vorlagendateien enthalten.
- Auszuschließen sind `.git`, `.DS_Store`, `__pycache__`, `*.pyc`, `.env*`, `node_modules`, `dist`, `build`, sämtliche Romanprojekte, Datenbanken, Archive und systemspezifische Dateien.
- Symbolische Links im Quell-Skill-Pfad oder einem paketierten Skill sind vor Änderungen abzulehnen; ein Skill-Link darf niemals zu fremden Hostdateien verfolgt werden. Vorhandene nicht genehmigte Paketdokumente lassen Refresh ebenfalls scheitern, statt stillschweigend in ein neues Manifest aufgenommen zu werden.
- Ausführungsbits für `scripts/*.py` erhalten, soweit die Quelle sie hat.
- Nur den lokalen Quell-Skill-Baum und die ausdrückliche Repository-Hinweisliste lesen. Der Build ist außer `built_at` deterministisch.
- Das Paket ist eigenständig: Laufzeithelfer verwenden die Python-Standardbibliothek und finden Abhängigkeiten relativ zu ihrem Installationsort.

## Prüfrichtlinie

`verify` muss fehlende, geänderte, unerwartete oder nicht zum Hash passende Paketdateien ablehnen und danach jede Python-Datei kompilieren. Der Installer-Funktionstest muss zusätzlich:

1. ein temporäres Romanprojekt unter aktiver Produktionsautorität initialisieren;
2. sicherstellen, dass direkte kanonische FileStore-Änderungen gesperrt sind;
3. die vollständige Novel-Judge-Suite ausführen, einschließlich Gate-Autorität, Bereitschaft, Befehlsausführung, Quality Eval v2, typisierten semantischen Ereignissen und traditioneller Langformproduktion;
4. Graphvalidierer und Langform-/Reality-/Fähigkeitsregressionen ausführen;
5. die enthaltene Skill-Menge und Abweichungen von der Quellmenge prüfen;
6. für eine vollständige Veröffentlichung die isolierte Vertragsprobe eines zweiten Projekts sowie den traditionellen Langform-/Wissensumkehr-/Kaskaden-Pilotlauf mit mehr als 100.000 Zeichen ausführen.

Eine Plattform ohne Python-Ausführung wird nur auf Ablauf-/Dokumentebene unterstützt; weisen Sie bei der Übergabe auf diese Einschränkung hin.
