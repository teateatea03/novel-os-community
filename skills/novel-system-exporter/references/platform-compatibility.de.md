# Novel OS: Plattformkompatibilität und Abhängigkeitsmatrix

<!-- language-navigation -->

[繁體中文](platform-compatibility.md) | [English](platform-compatibility.en.md) | [日本語](platform-compatibility.ja.md) | [한국어](platform-compatibility.ko.md) | [Español](platform-compatibility.es.md) | [Français](platform-compatibility.fr.md) | **Deutsch** | [Português](platform-compatibility.pt.md)

Dieses Dokument muss mit der ZIP-Datei ausgeliefert werden. Novel OS ist eine Sammlung aus **Skill-Anweisungen + lokalen Vorlagen/Python-Validatoren**, kein eigenständiges Modell, keine Chatplattform, Vektordatenbank oder kein Clouddienst. Ob „automatische Bereitstellung“ möglich ist, hängt davon ab, ob das Ziel-KI-Framework mehrteilige Skills lesen, Dateien schreiben, Befehle ausführen und optional Modelle aufrufen/auf das Netzwerk zugreifen darf.

```text
- 1 Koordinator + 16 mitwirkende Skills, insgesamt 17 Laufzeit-Skills (die Quellen enthalten zusätzlich den Exporter)
- Modellfähigkeitskompatibilität: novel-model-capability-compatibility, zuständig für Proben am tatsächlichen Endpunkt, L0–L5, Adapter, Rückfallmodi und Regression nach Modellwechsel
- Realitätszustand: novel-reality-state-engine, Prüfkette Ereignis → Zustand → Fähigkeit → Verhalten → Prosa
- Weltdatenbanken: novel-world-database-builder
- Spezialobjektdatenbanken: special-object-database-builder, maßgebliche Wurzel SPECIAL_OBJECT_DATABASE_ROOT
- Vollendung aufgegebener Werke: unfinished-novel-completion
```

## 1. Kernkomponenten und ihre Abhängigkeiten

| Komponente/Funktion | Verwendetes System/Format | Mindestabhängigkeiten | Optionale Abhängigkeiten | Rückfall bei Nichtverfügbarkeit |
|---|---|---|---|---|
| Skill-Zuordnung | `SKILL.md` mit YAML-Kopf + Markdown; `novel-operating-system` | KI/Agent, der mehrere Textdateien laden kann | Skills-Laufzeit, die anhand von Beschreibungen automatisch auslöst | Koordinator als Systemprompt/Projektanweisung nutzen und andere Skills manuell beifügen |
| Projektpersistenz | Markdown, JSON, gewöhnliche Ordner | UTF-8-Dateien lesen/schreiben | Git | Gleichnamige Dateien in Chat/Canvas/Clouddokumenten pflegen; ausdrücklich auf fehlende Persistenzgarantie zwischen Runden hinweisen |
| Langforminitialisierung und lokale Gates | Python-CLI, Standardbibliothek | **Python 3.10+**, Shell, beschreibbarer Datenträger | Git | Vorlagen und Checklisten manuell kopieren; keine ausgeführten Gates/Snapshots behaupten |
| Maßgeblicher Beziehungsgraph | Graphify-kompatibles Knoten-Kanten-JSON | Python 3.10+ (Initialisierung, JSON-Validierung) | `networkx`: path/affected; `graphifyy` + `networkx`: HTML, Community-Analyse, Cypher-Export | graph.json speichern/lesen; Beziehungen manuell abfragen, ohne erzeugte Visualisierungen oder kürzeste Pfade zu behaupten |
| Weltdatenbank | Graphify-kompatibles JSON; Welt-/Ort-/Fraktion-/Ressourcen-/Regel-/Ereignis-/Behauptungsknoten, Quellenbelege und inkrementelle Stapel | Python 3.10+, dauerhafte UTF-8-Dateien | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | graph.json und Markdown-Register speichern; Versions-/Wissensprüfungen manuell durchführen, ohne fertige Visualisierungsexporte zu behaupten |
| Spezialobjektdatenbank | Graphify-kompatibles JSON; Objekt-/Versions-/Varianten-/Modul-/Fähigkeits-/Spezifikations-/Energie-/Beschränkungs-/Besitz-/Betriebs-/Lebenszyklusknoten und Quellenbelege | Python 3.10+, dauerhafte UTF-8-Dateien | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | graph.json und Objektregister speichern; Versions-/Spezifikationskonflikte manuell prüfen, ohne fertige Visualisierungsexporte zu behaupten |
| Interaktive Fiktion | JSON-kompatibler Zustand, Markdown-Rundenprotokoll | Dateien lesen/schreiben; Python 3.10+ für Validierung/Checkpoints | Langzeitgedächtnis/Datenbank | Jede Runde den eingefügten Zustand prüfen; Erhalt nach erneutem Öffnen ist nicht garantiert |
| Quellenrecherche und Validierung zur Vollendung | Unvollendete Werke | `unfinished-novel-completion`; Recherche-/Anhangswerkzeuge optional | `source_ingest.py` erfasst Hashes, Versionen, Vollständigkeit und Rechtsstatus; `completion_gate.py` prüft überzogene Aussagen über Intention und Veröffentlichungsgrenzen | |
| Unabhängige Modellprüfung | Modellaufruf-CLI/API des Hosts | Keine; nicht erforderlich | Fähigkeit, zweites Modell oder Unteragent aufzurufen | Manuelle/mit demselben Modell ausgeführte Checkliste verwenden; nicht „durch unabhängiges Modell geprüft“ behaupten |

### Quellenrecherche und Werkzeuge für unvollendete Werke

Die Basiswerkzeuge in `unfinished-novel-completion` verwenden nur die Python-Standardbibliothek: `init_completion_project.py`, `source_ingest.py`, `compare_source_versions.py`, `branch_diff.py`, `feasibility_report.py`, `sync_graph.py`, `completion_gate.py`, `provenance_report.py` und `run_regression.py`. Netzwerkzugriff, OCR, PDF-Werkzeuge, Browser und zweites Modell sind optional. Ohne sie lassen sich Nutzerdateien weiter verarbeiten, aber Quellenumfang und Unbekanntes müssen benannt werden; eine Prüfung darf nicht vorgetäuscht werden.

### Minimale „vollautomatisierte“ Umgebung

- **Python 3.10 oder neuer:** Kernskripte verwenden die Typvereinigungssyntax `X | None`; Python 3.11+ wird empfohlen.
- **POSIX-Shell oder gleichwertiger Prozessstarter:** zum Ausführen der Python-CLI.
- **Beschreibbares dauerhaftes Dateisystem:** zum Installieren von Skills und Speichern von Romanprojekten; mindestens ein beschreibbares Skill- und Projektverzeichnis sind erforderlich.
- **UTF-8-Dateiunterstützung:** Geschichten, Vorlagen, JSON und traditionelles Chinesisch verwenden UTF-8.
- **ZIP-Entpacken:** nur bei ZIP-Verteilung nötig; alternativ sind Git/Ordnerupload möglich.
- **Lokale Standardbibliothek:** Kernskripte für Initialisierung, Register, Gates, Zustand und Pakete benötigen nur die Python-Standardbibliothek; der Basis-Funktionstest braucht kein `pip install`.

Diese Funktionen benötigen weder API-Schlüssel, Datenbank, Node.js noch Netzwerkzugriff.

### Optionale Abhängigkeiten (Erweiterungen, kein Basisablauf)

```bash
# Graphpfade, Kaskadenabfragen, GraphML
python -m pip install networkx

# Graphify-HTML-/Community-/Cypher-Exporte; das Ursprungspaket heißt graphifyy
python -m pip install graphifyy networkx

# Git-Versionssnapshots und Gate-geschützte Commits
git --version
```

- `relationship_graph.py init/validate/search/neighbors/timeline/add/import/snapshot` kann allein die Standardbibliothek verwenden; `path`/einige Zyklusprüfungen benötigen `networkx`.
- `relationship_graph.py export` benötigt **`networkx` + `graphifyy`**. Ohne sie `graph.json` erhalten und keine erzeugten HTML-/GraphML-/Cypher-Ausgaben behaupten.
- `independent_review.py` ist derzeit ein **Minis-spezifischer Adapter**, der `minis-model-use` aufruft. Ersetzen Sie ihn in anderen Frameworks durch deren Zweitmodell-/Unteragenten-/API-Adapter oder deaktivieren Sie diese optionale Prüfung.
- `novel_git.py` ist eine optionale Versionsverwaltungsschicht. Ohne Git kann `snapshot_project.py` weiterhin Datei-Snapshots anlegen.

## 3.2 Host-Anbindungspunkte und erforderliche Ersetzungen

Die Kerndatenformate des Pakets sind portabel, doch der Integrator muss folgende **Host-/Framework-Anbindungspunkte** bearbeiten:

| Anbindungspunkt | Aktuelle Minis-Nutzung | Aufgabe anderer KI-Frameworks |
|---|---|---|
| Standard-Romanwurzel | `<NOVEL_PROJECTS_ROOT>` | `NOVEL_PROJECTS_ROOT` setzen oder jedem Initialisierer `--root <persistent-projects-root>` übergeben; Existenz von `<MINIS_ROOT>` nicht voraussetzen |
| Figurendatenbankwurzel | `<CHARACTER_DATABASE_ROOT>` | `<CHARACTER_DATABASE_ROOT>` zuordnen und Stapelvorbereitung auf `<CHARACTER_DATABASE_WORK_ROOT>` abbilden; beide müssen demselben Projekt/Agent zugänglich sein |
| Spezialobjektdatenbankwurzel | `<SPECIAL_OBJECT_DATABASE_ROOT>` | `<SPECIAL_OBJECT_DATABASE_ROOT>` zuordnen und Stapelvorbereitung auf `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>` abbilden; beide müssen demselben Projekt/Agent zugänglich sein |
| Zustandswurzel interaktiver Fiktion | `<INTERACTIVE_PROJECTS_ROOT>` | `<INTERACTIVE_PROJECTS_ROOT>` zuordnen und laufübergreifendes Lesen von Zustand/Checkpoints/Protokollen sicherstellen |
| Unabhängige Prüfung | `minis-model-use run` | Befehlsadapter in `independent_review.py` umschreiben oder gleichwertigen Unteragenten bauen; JSON-Schema, Fehlerartefakte und Verbot automatischer Kanonübernahme erhalten |
| Skill-Erkennung | Minis-Skill-Register + benachbarte Verzeichnisse | **17** Beschreibungen registrieren (Koordinator + sechzehn spezialisierte Skills) oder Intent-Router bauen; bedarfsweises Lesen benachbarter Ressourcen erlauben |
| Langzeitzustand | Gemeinsames Minis-Verzeichnis | Dauerhaftes Volume, Datenbank, Artefaktspeicher oder Framework-Checkpointer zuordnen; Abruf über Projekt-ID |
| Recherchewerkzeuge | Minis-Browser/Shell | Browser-/Such-/Dateiwerkzeuge zuordnen; sonst Recherche auf Nutzermaterial beschränken |

- `init_novel_project.py` unterstützt bereits `NOVEL_PROJECTS_ROOT`; ausdrückliches `--root` hat Vorrang. `<..._ROOT>`-Platzhalter für Figuren-/Welt-/Spezialobjektdatenbanken und interaktive Fiktion müssen durch Router-/Bereitstellungskonfiguration ersetzt werden. Jedes `<MINIS_ROOT>/...` in der ursprünglichen Dokumentation ist außerhalb von Minis ein **Beispiel-Standardpfad**, keine feste Systemvoraussetzung.

## 4. Fähigkeitsstufen von KI-Frameworks

### A | Native Skills + Shell + Dateisystem (Vollmodus)

Für Frameworks mit Skill-Laufzeit, Agentenwerkzeugen und Sandbox/Terminal. Installieren Sie das gesamte Paket direkt:

```bash
python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test
```

**Das Framework muss:**

1. `<SKILLS_DIR>/novel-operating-system/SKILL.md` als primär auslösbaren Skill registrieren.
2. Alle **17** Skill-Ordner (Koordinator + sechzehn Mitwirkende) als Nachbarn erhalten; nicht nur die Einstiegsdatei hochladen.
3. Dem Agenten das Lesen benachbarter `SKILL.md`, Vorlagen, Referenzen und Skripte erlauben.
4. Ein sicheres Befehlswerkzeug oder einen Prozessstarter für `python3` bereitstellen.
5. Nach Neuindexierung/Neustart des Skill-Registers die Funktionstestergebnisse zur Abnahme verwenden.

**Empfohlene Ergänzungen:** Webrecherche, Zweitmodelladapter, Git, `networkx` und `graphifyy`.

### B | Eigene Agenten-/Tool-Calling-Frameworks (Adapter erforderlich)

Für Frameworks mit Systemprompt, Funktionsaufrufen und Dateiwerkzeugen, die `SKILL.md` nicht verstehen.

**Der Framework-Integrator muss:**

1. `novel-operating-system/SKILL.md` in System-/Entwickleranweisungen aufnehmen; YAML-Beschreibung als Routingregeln erhalten.
2. Die übrigen **sechzehn** Skills als abrufbare Referenzdokumente bereitstellen oder einen Router bauen, der nach Nutzerabsicht die passende `SKILL.md` lädt.
3. Werkzeuge zuordnen:
   - Shell → Python-Skripte;
   - Dateien lesen/schreiben/auflisten → Projektdateien und Zustand;
   - Websuche/Browser → Recherche öffentlicher Quellen;
   - Zweitmodell/Unteragent → Ersatzadapter für `independent_review.py`.
4. Den Minis-spezifischen Aufruf `minis-model-use` durch den eigenen Modellclient des Frameworks ersetzen. Ursprüngliches JSON-Prüfschema, Fehlerartefakte und den Grundsatz „machine_suggestion wird nicht automatisch zu Kanon“ erhalten.
5. Dauerhaften Speicherschlüssel/Arbeitsbereich festlegen, damit Dateien desselben Werks zwischen Gesprächen/Workern erhalten bleiben.
6. Automatische Skill-Auslösung implementieren oder ausdrücklich deaktivieren; **17 Skill-Dokumente** im Kontext rechtfertigen keine Behauptung automatischer Zusammenarbeit.

### C | Chat-KI nur mit Wissensdateiuploads/eigenen Anweisungen (Dokumentmodus)

Schreibkonventionen, Vorlagen, Datenschemata und Checklisten sind portabel, echte Automatisierung ist jedoch nicht verfügbar.

**Erforderlich:** gesamten Unterbaum `skills/` hochladen; Koordinator als Projektanweisung setzen; jede Runde aktuellen Werkzustand, Story-Bibel, Zeitleiste, Figurendateien, Leserregister und Zusammenfassung des vorherigen Kapitels beifügen oder von der KI nachlesen lassen.

**Nicht versprechen:** automatische Ordnererstellung, CLI-Gates, Hashprüfung, Git, Graphify-Export, chatübergreifendes Gedächtnis, Hintergrundaufgaben oder Zweitmodellprüfung.

### D | Modelle nur mit einem Systemprompt (manueller Rückfallmodus)

Fügen Sie einen kompakten Koordinator in den Systemprompt ein und nutzen Sie spezialisierte Skills und Projektvorlagen als Wissensbasis. Nutzer/Integrator müssen die pro Runde erzeugten Zustandsdokumente manuell speichern. Dies erhält den Denkrahmen, entspricht aber nicht dem vollständigen Novel OS.

## 5. Checkliste gängiger Framework-Integrationen

| Typ | Platzierung | Erforderliche Konfiguration | Wichtiger Hinweis |
|---|---|---|---|
| OpenAI-Assistants-/Responses-Stil | Systemanweisungen + Vektor-/Dateisuche + Codeinterpreter/eigene Sandbox | Router, dauerhaften Dateispeicher und Python-Ausführungsadapter bauen | Keine automatische Synchronisierung zwischen Läufen annehmen; Projektdateien ausdrücklich zurückspeichern |
| Claude-Projects-/MCP-Stil | Projektanweisungen + Wissensdateien; MCP-Dateisystem-/Shell-Server | Skills als Ressourcen bereitstellen; MCP zum Lesen/Schreiben/Ausführen/Webzugriff nutzen | Ohne MCP Stufe C, keine Skriptausführung |
| Gemini-Gems-/Vertex-Agent-Stil | Systemanweisung + File Search/Code Execution/Cloud Storage | Dauerhaften Speicher, Funktionsrouter und Python-Starter verbinden | Gem-Anweisungen allein bieten im Allgemeinen keine gesprächsübergreifenden Dateiabläufe |
| LangChain-/LangGraph-/CrewAI-/AutoGen-Stil | Routerknoten + Dateiwerkzeuge + Subprozesswerkzeug + dauerhafter Checkpointer | Skills nach Absicht laden, Projekt-ID erhalten und Prüfagentenadapter bauen | Skill-Erkennung und Zustandscheckpoints müssen implementiert werden; Entpacken allein aktiviert sie nicht |
| Open-WebUI-/AnythingLLM-/Dify-/Flowise-Stil | Wissensbasis + Agentenworkflow-/Werkzeugknoten | Skill-Dateien hochladen, Shell/Python verbinden und dauerhaftes Volume einbinden | Reiner RAG-Chat ist Stufe C; A/B benötigen Workflows |
| Weltdatenbank-Host | `WORLD_DATABASE_ROOT` + `WORLD_DATABASE_WORK_ROOT` | Dauerhaften Weltgraph und Stapelarbeitsbereich einbinden; snapshot/validate/affected/export anbieten | Ohne Prozessstarter nur JSON/Markdown speichern und keine ausgeführte Graphify-CLI behaupten |
| Spezialobjektdatenbank-Host | `SPECIAL_OBJECT_DATABASE_ROOT` + `SPECIAL_OBJECT_DATABASE_WORK_ROOT` | Dauerhaften Spezialobjektgraph und Stapelarbeitsbereich einbinden; snapshot/validate/affected/export anbieten | Ohne Prozessstarter nur JSON/Markdown speichern und keine ausgeführte Objektvalidierung/-exporte behaupten |
| Programmieragenten wie Cursor/Claude Code/Codex CLI | Skills-/Befehlsverzeichnis + Arbeitsbereich | **17** Ordner installieren und Python sowie Arbeitswurzel konfigurieren | Adapter für dialogbasierte Modellprüfung muss für die jeweilige CLI umgeschrieben werden |

Diese Namen veranschaulichen nur Integrationstypen. Produktversionen, Tarife und Berechtigungen variieren; prüfen Sie vor Bereitstellung die aktuelle Dokumentation.

## 6. Abnahmecheckliste für die Bereitstellung

Nach der Integration sollte Host oder Integrator jeden Punkt prüfen:

- [ ] `novel-operating-system` und sechzehn benachbarte spezialisierte Skills sind lesbar.
- [ ] Eine geschriebene Testdatei lässt sich in einem neuen Agentenlauf/Gespräch wieder lesen.
- [ ] `python3 --version` ist ≥ 3.10; falls Graphexporte nötig sind, lassen sich `networkx`/`graphifyy` importieren.
- [ ] `python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test` besteht, oder nicht ausführbare Punkte sind ausdrücklich dokumentiert.
- [ ] Ein neues Roman-Testprojekt besitzt Story-Bibel, Zustand, Zeitleiste, Leserregister und graph.json.
- [ ] Der Agent schreibt einen kurzen Abschnitt, aktualisiert den Zustand und setzt in neuem Lauf fort; Kontinuität beruht damit nicht nur auf Restkontext.
- [ ] Bei aktivierter Recherche können URLs/Quellen/Vertrauensgrad erfasst werden, statt Suchauszüge als Kanon zu behandeln.
- [ ] Bei aktivierter Zweitmodellprüfung erzeugen Adapterfehler nur ein Nichtverfügbarkeitsartefakt, ohne zu blockieren oder Ergebnisse zu erfinden.

## 7. Plattformgrenzen und Verantwortlichkeiten

- Inhaltsrichtlinien, Werkzeugberechtigungen, Tokenlimits, Datenaufbewahrung und Netzwerkregeln des Zielmodells sind von Novel OS unabhängig und können durch diesen Skill nicht außer Kraft gesetzt werden.
- „Automatische Bereitstellung“ bedeutet automatische Installation, Gerüsterstellung und Routerladen innerhalb eines **Agentenframeworks mit Installations-/Datei-/Shell-Berechtigungen**. Es bedeutet nicht, durch Übergabe einer ZIP-Datei an irgendein Chatmodell dauerhaft zu installieren.
- Externe Modelle, Browser und Git sind optionale Erweiterungen. Fehlen sie, den Rückfallmodus ausdrücklich nennen; Abschlussbehauptungen dürfen Fähigkeitslücken nicht verdecken.
