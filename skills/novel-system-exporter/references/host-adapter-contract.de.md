# Novel-OS-Hostadapter-Vertrag

<!-- language-navigation -->

[繁體中文](host-adapter-contract.md) | [English](host-adapter-contract.en.md) | [日本語](host-adapter-contract.ja.md) | [한국어](host-adapter-contract.ko.md) | [Español](host-adapter-contract.es.md) | [Français](host-adapter-contract.fr.md) | **Deutsch** | [Português](host-adapter-contract.pt.md)

Dieser Vertrag richtet sich an Integratoren von KI-Frameworks außerhalb von Minis. Novel OS ist kein Plugin, das allein durch Hochladen einer ZIP-Datei Datei- oder Modellzugriff oder ein gesprächsübergreifendes Gedächtnis erhält. Damit eine Bereitstellung als automatisiert gilt, muss der Host die folgenden Fähigkeiten liefern.

## A. Vom Host bereitzustellende Mindestschnittstellen

| Fähigkeit | Mindestoperationen | Verwendung durch Novel OS | Falls nicht verfügbar |
|---|---|---|---|
| Skill-Router | `load_skill(name)`/Ressourcendateien lesen | Der Koordinator lädt sechzehn spezialisierte Skills nach Absicht | Passenden Skill manuell in den Prompt aufnehmen |
| Dauerhafter Speicher | `read(path)`, `write(path)`, `list(path)`, `mkdir(path)` | Projektbibel, Kapitel, Register, Zustand, Graphen und Snapshots | Nur Dokumentmodus; keine garantierte Kontinuität zwischen Läufen |
| Prozessstarter | `run(argv, cwd)` | Python-Initialisierer, Gate-, Zustands- und Graphwerkzeuge ausführen | Vorlagen und Checklisten manuell nutzen; keine ausgeführte Validierung behaupten |
| Projektidentität | Stabile `project_id` → Speicherwurzel | Zustand desselben Romans in neuem Gespräch/Worker lesen | Nutzer stellt Dateien/Zusammenfassungen jedes Mal manuell bereit |
| Branch-Schreibsperre | `lock(project,session,branch)`/Transaktionssperre | Commits für Wiederherstellung, veraltete Hashes, Ereignisse, Zustand und Manifest serialisieren | Nur einen Schreiber erlauben; keine Sicherheit mit mehreren Workern behaupten |
| Modellaufgabenadapter | `minis.model-task.v1` annehmen, Zeitplan zuerst speichern, Worker mit Lease übernehmen lassen und festes Schema zurückgeben | L1/L2-Modelle auf einzelne extract/plan/render/repair-Aufgaben beschränken; Wiederholen/Abbrechen/Veralten/Wiederanlauf unterstützen | Dokumentmodus oder manuelle Formulare; Modelle haben keine Zustandsautorität |
| Laufzeit-/Ereignisversionierung | Runtime-Build, Ereignisschema, Übergangsvertrag, Referenz-Replay-Testdaten | Wiedergabe alter Historie nach Upgrade erzeugt denselben Zustandshash; unbekannte Verträge werden sicher abgelehnt | Alte Laufzeit einfrieren; erst nach manueller Migration aktualisieren |
| Story-Solver | Begrenzte Erkundung von Storylet-Zuständen | Unerreichbare Zustände, defekte Ziele und logische Sackgassen finden und Erkundungsgrenzen offenlegen | Pfade manuell prüfen; keine Prüfung aller Pfade behaupten |
| Steuerung zufälliger Ereignisvorschläge | Branch-bezogenes `off`/`on-suggestion`, semantisches Fenster, Pool mit Startwert, nichtkanonisches Audit | Optionale Richtungskarten nur in zulässigen Fenstern anbieten, Ohne-Ereignis-Ausgänge und reproduzierbare Herkunft erhalten | Fest auf `off` lassen; keine heimlichen Ziehungen über Prompts oder Behandlung als Kanon |
| Gedächtnis-/Graphprojektion | Ereignis → episodisches Gedächtnis; Ereignisse → Graphify-Projektion | Nachvollziehbare Erinnerungen und neu aufbaubare Graphen | Ereignisse bewahren; abgeleitete Indizes als nicht aktualisiert markieren |
| Graphify-Abschlussindex | `sync_graph.py` synchronisiert Quellen, Behauptungen und Zweige in vorhandenes `graph.json` | Abfragbare Quellen, Belege, Versionen und Vollendungshypothesen | Der Graph ist ein abgeleiteter Index und darf Prosa/Kanon nicht rückwärts überschreiben |

Der Prozessstarter sollte **argv-Arrays statt zusammengesetzter Shell-Zeichenketten** bevorzugen, in Projekt-/Skill-Arbeitsbereichen bleiben und stdout, stderr und Exitcode als Gate-Artefakte aufbewahren.

## B. Pfadzuordnung

Die Bereitstellungskonfiguration sollte folgende Werte liefern. Codieren Sie Minis-Pfade nicht fest in eine andere Umgebung:

```text
SKILLS_ROOT=/agent/skills
NOVEL_PROJECTS_ROOT=/agent/data/novels
CHARACTER_DATABASE_ROOT=/agent/data/character-databases
CHARACTER_DATABASE_WORK_ROOT=/agent/work/character-db-batches
WORLD_DATABASE_ROOT=/agent/data/world-databases
SPECIAL_OBJECT_DATABASE_ROOT=/agent/data/special-object-databases
SPECIAL_OBJECT_DATABASE_WORK_ROOT=/agent/work/special-object-db-batches
INTERACTIVE_PROJECTS_ROOT=/agent/data/interactive-fiction
```

- `init_novel_project.py` liest `NOVEL_PROJECTS_ROOT` oder nimmt ein ausdrückliches `--root` an.
- `SPECIAL_OBJECT_DATABASE_ROOT` enthält die maßgebliche Spezialobjektdatenbank unter `graphify-out/graph.json`; `SPECIAL_OBJECT_DATABASE_WORK_ROOT` enthält Stapel-JSON und Übergabepakete und kann die maßgebliche Kopie nicht ersetzen.
- `WORLD_DATABASE_ROOT` enthält die maßgebliche Weltdatenbank unter `graphify-out/graph.json`; `WORLD_DATABASE_WORK_ROOT` enthält Welt-Stapel-JSON und Übergabepakete und kann die maßgebliche Kopie nicht ersetzen.
- Andere Wurzeln sind Router-/Framework-Adaptereinstellungen. Ersetzen Sie `<..._ROOT>`-Platzhalter der betroffenen Skills durch tatsächliche dauerhafte Pfade.
- Alle Dateien eines Romans müssen unter derselben wieder lesbaren Projektwurzel liegen; halten Sie nicht nur das neueste Kapitel im temporären Chatkontext.

## C. Erforderlicher Bereitstellungsablauf

1. Entpacken Sie das Paket und führen Sie zuerst aus:

   ```bash
   # Zuerst Python, Hashes und den vollständigen Funktionstest sicherstellen:
   python3 scripts/install_novel_os.py --target "$SKILLS_ROOT" --smoke-test
   ```

2. Registrieren Sie **17** Skills (Koordinator + 16 spezialisierte Skills). `novel-reality-state-engine` muss Ereignis-/Zustands-JSON, eine Reality Card und ein ausführbares Reality Gate bereitstellen. `novel-model-capability-compatibility` muss Text-/JSON-/Werkzeug-/Zustandsproben des tatsächlichen Endpunkts, Fähigkeitsstufen und Rückfallmodi bereitstellen. `novel-sensory-sound-prose` muss seinen Klang-/Fünfsinne-Prosa-Vertrag erhalten. Benachbarte relative Pfade beibehalten.
3. Ordnen Sie `project_id` den obigen dauerhaften Wurzeln zu und berechtigen Sie den Agenten zum Lesen und Schreiben der Projektdateien.
4. Führen Sie den Initialisierer für ein neues Projekt aus und bestätigen Sie die erfolgreiche Erstellung von Markdown/JSON/`graphify-out/graph.json`.
5. Beenden und starten Sie einen neuen Agentenlauf und lassen Sie vor der Fortsetzung den Zustand lesen, um Unabhängigkeit vom temporären Kontext zu prüfen.
6. Lassen Sie zwei Worker gleichzeitig gegen denselben Quellzustandshash committen: Genau einer muss erfolgreich sein, der andere muss stale-hash/conflict erhalten. Prüfen Sie danach den aktuellen Zustandshash durch Ereigniswiedergabe.
7. Erstellen Sie zwei episodische Erinnerungen und prüfen Sie, dass die Reflexion mindestens zwei vorhandene Beleg-IDs zitiert. Kompilieren Sie eine L1-Renderaufgabe und bestätigen Sie, dass das Paket keine verborgene Wahrheit enthält und `may_commit_state=false` aufweist.
8. Bauen Sie die interaktive Graphify-Projektion aus Ereignissen neu auf. Löschen und Wiederaufbauen müssen denselben Quellhash erzeugen.
9. Bewahren Sie mindestens einen Referenz-Historien-Testfall auf. Die Wiedergabe mit neuer Laufzeit muss den erwarteten Zustandshash erzeugen; unbekannte Übergangsverträge müssen abgelehnt werden.
10. Erstellen Sie eine Modellaktivität und prüfen Sie Wiederherstellung nach Lease-Ablauf, Markierung alter Ergebnisse als veraltet nach Zustandsfortschritt und Sperrung der Autorenkonsole bei ausstehender Aktivität.
11. Erstellen Sie einen Storylet-Testfall mit unerreichbaren Zuständen, defekten Zielen und logischen Sackgassen; der Solver muss alle erkennen und maximale Tiefe/Zustandszahl ausdrücklich angeben.
12. Löschen Sie nach Ereigniskompaktierung den Index und manipulieren Sie das Archiv. Das Manifest-Integritätsgate muss es vor dem Indexneuaufbau ablehnen.
13. Prüfen Sie, dass ein neuer Branch standardmäßig `off` verwendet, ohne Ziehungen oder Audit-Schreibvorgänge. Nachdem der Nutzer `on-suggestion` aktiviert, muss ein fester Startwert an einer Szenengrenze denselben Vorschlag/Ohne-Ereignis-Ausgang liefern; kanonisches Ereignisprotokoll, State, Graph, Knowledge und Prosa müssen unverändert bleiben.
14. Stellen Sie Anfragen zu Metaeingaben, ausstehenden direkten Folgen, Hochdrucksituationen ohne natürliche Pause, bereits bestimmten Folgen und nicht vorbereiteten Bedrohungen; alle müssen unterdrückt werden. Die Annahme eines Vorschlags darf nur eine Planungsübergabe erzeugen und muss die Reality/Knowledge/Agency/Behavior/World/Canon-Gates aufführen.
15. Prüfen Sie Hash/Bytes/Anzahl des Manifests des aktiven Segments: Nach Löschen des Ereignisindex muss Manipulation des aktiven Protokolls sicher abgelehnt werden. Aktivitätsübernahmen geben ein Fencing-Token zurück; Abschlüsse mit alten oder fehlenden Tokens oder abgelaufenen Leases müssen abgelehnt werden. Alle dateibasierten IDs müssen Pfadtraversierung ablehnen. Das Wiederholen derselben Zufallsereignis-`request_id` darf weder erneut ziehen noch einen zweiten Audit-Eintrag erzeugen. Eine manipulierte Audit-Hashkette darf nicht wiedergegeben werden, und abgelaufene Vorschläge dürfen keine Annahmeübergaben erzeugen.

## D. Optionale Werkzeugadapter

### Webrecherche

Wenn der Host Browser-/Suchwerkzeuge bereitstellt, muss der Router Suchergebnisse, URLs, Herausgeber, Daten und kurze Zitate in Recherche-/Graph-Belegfeldern erfassen. Ohne Browser darf er nur Nutzermaterial verarbeiten, muss `【待定】` („unbestimmt“)/`【提案】` („Vorschlag“) verwenden und darf keine Quellenprüfung vortäuschen.

### Zweitmodell-/Unteragentenprüfung

`long-form-novel-writer/scripts/independent_review.py` ruft derzeit Minis’ `minis-model-use` auf. Andere Frameworks müssen eine der folgenden Möglichkeiten wählen:

1. Einen Framework-Adapter schreiben, der `role`, `prompt` und `max_tokens` annimmt, ein anderes Modell/einen Unteragenten aufruft und Rohtext sowie geparstes JSON unter `reviews/` speichert; oder
2. Unabhängige Prüfung deaktivieren, lokale Gates/manuelle Checklisten nutzen und in der Übergabe „zweites Modell nicht ausgeführt“ vermerken.

In beiden Fällen gelten die Ausgaberegeln weiter: `machine_suggestion` darf nicht direkt zu `[CANON]` werden; Probleme ohne zwei stützende Belege gehören nur in `questions`; Fehler müssen ein `unavailable`-Artefakt erzeugen und dürfen nie stillschweigend als bestanden zählen.

### Graphen und Versionsverwaltung

- `networkx`: aktiviert path, affected, GraphML und verwandte Funktionen.
- `graphifyy` + `networkx`: aktiviert Graphify-HTML, Community-Analyse und Cypher-Exporte.
- Git: nur für Commits/Branches; Datei-Snapshots bleiben ohne Git verfügbar.

Dies sind Erweiterungen und keine Voraussetzungen zum Beginnen eines Romans.

## E. Minimale Routerlogik

```text
wenn die Anfrage Erstellen/Aktualisieren/Abfragen/Vergleichen/Exportieren einer Spezialobjektdatenbank betrifft:
    special-object-database-builder laden
    novel-worldbuilding-architect + knowledge-relationship-graph ergänzen
    character-db + behavior ergänzen, wenn Bediener/autonome Maschine/Persönlichkeit relevant sind
    long-form ergänzen, wenn mit Romanprojekt oder Kapitelzustand verknüpft
sonst wenn die Anfrage Erstellen/Aktualisieren/Abfragen/Exportieren einer Weltdatenbank betrifft:
    novel-world-database-builder laden
    novel-worldbuilding-architect + knowledge-relationship-graph ergänzen
    long-form ergänzen, wenn mit Romanprojekt oder Kapitelzustand verknüpft
sonst wenn die Anfrage kapitelübergreifendes Schreiben/Fortsetzen/Gliederungsänderung betrifft:
    long-form + behavior laden
    world/style/graph nur ergänzen, wenn der Erzählzustand sie benötigt
sonst wenn die Anfrage Figurenrecherche betrifft:
    character-deep-digger laden
    behavior + character-db/graph bei Bedarf an Belegen oder Persistenz ergänzen
sonst wenn die Anfrage menschliche Erzählstimme/traditionelles Chinesisch aus Taiwan/Figurenstimme betrifft:
    human-voice-editor nach Inhalts-/Kontinuitäts-/Stilprüfungen laden
sonst wenn die Anfrage die Vollendung eines aufgegebenen/unfertigen Romans, ursprüngliche Autorenabsicht oder ein alternatives Ende betrifft:
    unfinished-novel-completion laden
    long-form + Beleg-/Quellenwerkzeuge + world/behavior/style/graph nach Bedarf ergänzen
sonst wenn die Anfrage interaktive Fiktion mit freier Eingabe betrifft:
    immersive-interactive-fiction laden
    world/behavior/style/graph nach Szenenkomplexität ergänzen
```

Der Koordinator sollte diesen Router zuerst bearbeiten. Nehmen Sie nicht in jeder Runde blind alle Skills in den Modellkontext auf.

## F. Was das Paket nicht automatisch erledigen kann

- Skills installieren, API-Schlüssel konfigurieren, Werkzeugberechtigungen aktivieren oder Datenbanken in nicht autorisierten Cloudkonten anlegen.
- Einem reinen Chatmodell Shell, Dateisystem, dauerhaftes Gedächtnis oder Mehrmodellfähigkeiten geben.
- Inhaltsrichtlinien, Tokenlimits, Datenschutzregeln oder Netzwerkbeschränkungen des Zielmodells/der Zielplattform außer Kraft setzen.

Fehlen Voraussetzungen, verwenden Sie die Rückfallmodi B/C/D in [platform-compatibility.de.md](platform-compatibility.de.md) und führen Sie jede deaktivierte Funktion im Bereitstellungsbericht auf.
