# Novel OS importieren und bereitstellen

<!-- language-navigation -->

[繁體中文](portable-install.md) | [English](portable-install.en.md) | [日本語](portable-install.ja.md) | [한국어](portable-install.ko.md) | [Español](portable-install.es.md) | [Français](portable-install.fr.md) | **Deutsch** | [Português](portable-install.pt.md)

## Zuerst Fähigkeiten erfassen: den richtigen Bereitstellungsmodus wählen

Lassen Sie vor der Übergabe die Zielumgebung folgende Fragen beantworten:

```text
1. Kann sie mehrere Skills/Befehle installieren? Wo liegt das Einstiegsverzeichnis oder die Konfiguration?
2. Kann der Agent dauerhafte Dateien lesen und schreiben, Verzeichnisse auflisten und Python-/Shell-Befehle ausführen?
3. Welche Python-Version ist verfügbar? Sind Installationen von networkx, graphifyy und Git erlaubt?
4. Gibt es Web-/Browserwerkzeuge, ein zweites Modell oder Unteragenten, und wie werden sie über Werkzeuge aufgerufen?
5. Wo liegen Projektdateien über neue Gespräche, neue Worker und Neustarts hinweg?
```

Wählen Sie anhand der Antworten: **A: vollständige Installation** (Skills + Shell + Speicher), **B: Adapterintegration** (eigene Agentenwerkzeuge), **C: Wissensdateimodus** oder **D: manueller Modus mit einem Prompt**. Die vollständige Bewertung, Pakete und Adapteranforderungen der Frameworks stehen in [platform-compatibility.de.md](platform-compatibility.de.md). Ohne die Voraussetzungen für A/B darf „automatische Bereitstellung“ nicht als abgeschlossen gelten.

## KI-Plattformen mit eigenen Skill-Verzeichnissen (A: Vollmodus)

1. Entpacken Sie die ZIP-Datei.
2. Führen Sie im entpackten Stammverzeichnis aus:

   ```bash
   python3 scripts/install_novel_os.py --target /path/to/agent/skills --smoke-test
   ```

3. Lassen Sie die Plattform ihre Skills neu einlesen oder starten Sie ihren Skill-Index neu.
4. Testen Sie mit „Erstelle ein Projekt für einen langen Roman“. Dies sollte `novel-operating-system` auslösen, das Projektgerüst erstellen, den Bedarf an Recherche/Weltenbau/Verhalten/Stil/Graphen ermitteln und Planung sowie Prüfschranken vor dem Schreiben abschließen.

**Upgrades:** Ergänzen Sie `--upgrade`. Der Installer verschiebt vorhandene gleichnamige Skills vor dem Ersetzen nach `<target>/backups/novel-os-<timestamp>-<unique>/`; bei Fehlern stellt er die Originaldateien wieder her.

### Lizenzierung und Hinweise Dritter

Die vollständige ZIP-Datei muss die acht Sprachfassungen von `LICENSE`, `THIRD_PARTY.md` und `docs/COMMERCIAL_TERMS.md`, insgesamt 24 Dokumente, sowie die ursprünglichen Drittanbieter-Lizenzdateien jedes Skills erhalten. Die englische Lizenz heißt `LICENSE`, die anderen `docs/i18n/<lang>/LICENSE.md`. Englische `THIRD_PARTY.md` und `docs/COMMERCIAL_TERMS.md` haben keinen Sprachsuffix; die anderen verwenden `.<lang>.md`, wobei `lang` für `zh-TW`, `ja`, `ko`, `es`, `fr`, `de`, `pt` steht. Der Installer speichert diese Hinweise unter `<target>/novel-operating-system/DISTRIBUTION_NOTICES/` und bewahrt ihre ursprünglichen relativen Pfade, damit Lizenzlinks weiterhin funktionieren. Ursprüngliche Hinweise innerhalb der Skills bleiben ebenfalls an ihrem ursprünglichen Ort. Der Installer überschreibt weder `LICENSE` noch `docs/` im Stamm des Hosts. Hinweise vor einem Upgrade werden zusammen mit den ursprünglichen Skills in dessen Sicherung gespeichert.

`novel-operating-system/INSTALLATION.json` erfasst Quell-/Installationspfade, SHA-256 und Bytezahl jedes Hinweises. Führen Sie nach der Installation aus der entpackten ZIP-Datei diese schreibgeschützte Prüfung aus:

```bash
python3 scripts/install_novel_os.py --target /path/to/agent/skills --verify-installed-notices
```

Fehlende oder geänderte Dateien führen zum Fehler. Dies ist eine lokale Integritätsprüfung und ersetzt keine vertrauenswürdige Veröffentlichungsquelle. Siehe das ausdrückliche Dokumentinventar in [bundle-contract.de.md](bundle-contract.de.md). Diskussionsentwürfe sind keine wirksamen Lizenzen und werden nicht als formelle Bedingungen exportiert.

Auch die manuellen Übertragungsmodi B/C/D müssen Projektlizenz/kommerzielle Bedingungen und sämtliche Ursprungshinweise gemeinsam liefern. Kopieren Sie nicht nur `skills/` und lassen dabei die Lizenzdokumente weg.

## Eigene Agenten-/Tool-Calling-Frameworks (B: Adapter erforderlich)

Hat ein Framework keine native `SKILL.md`-Laufzeit, aber Systemprompt, Funktionsaufrufe und Datei-/Befehlswerkzeuge, ist das Bereitstellen durch bloßes Entpacken nicht abgeschlossen. Der Integrator muss:

1. `novel-operating-system/SKILL.md` in System-/Entwickleranweisungen aufnehmen und anhand der Beschreibung einen Intent-Router bauen.
2. Die sechzehn spezialisierten Skills als bedarfsgerecht lesbare Ressourcen für den Router verfügbar machen; relative Ordnerbeziehungen erhalten.
3. Bei einem aufgegebenen oder unvollendeten Werk zuerst die Übergabe zu Quellen/Kanon/Belegen/Intention/Machbarkeit/Verzweigungen/Rechten/Herkunft in `unfinished-novel-completion` abschließen und dann den ausgewählten Zweig an den Langform-Autor übergeben.
4. Dateilesen/-schreiben, Verzeichnislisten, Python-Prozesse, dauerhaften Arbeitsbereich, `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`, `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` und Webrecherche an die Werkzeug-API des Frameworks anbinden.
5. Den Aufruf `minis-model-use` in `independent_review.py` durch die Zweitmodell-/Unteragenten-/API-Integration der Plattform ersetzen. Falls keine verfügbar ist, den Schritt deaktivieren und als nicht ausgeführt protokollieren.
6. Mit der Abnahmecheckliste die Dateipersistenz zwischen Läufen und Zustandsaktualisierungen nach Kapiteln testen.

Siehe [platform-compatibility.de.md](platform-compatibility.de.md) für typische Integrationspunkte in LangGraph/CrewAI/AutoGen, MCP, OpenAI/Claude/Gemini und Dify/Flowise/Open WebUI. Alle erfordern einen vom Framework-Integrator gebauten Router/Werkzeugadapter; diese ZIP-Datei kann das in einem unbekannten Cloudkonto nicht automatisch erledigen.

## Plattformen mit nur einem Skill-Importfeld (C: Wissensdateimodus)

Laden oder fügen Sie das vollständige Verzeichnis `skills/novel-operating-system/` einschließlich Referenzen ein und halten Sie die übrigen sechzehn Skill-Ordner auf derselben Ebene als Anhänge/Wissensdateien vor. Geben Sie der KI folgende Anweisung:

> Lies zuerst novel-operating-system/SKILL.md. Alle benachbarten Skills sind erforderliche Mitwirkende dieses Systems. Erstelle ohne Shell gleichwertige Markdown-/JSON-Projektdateien und zeige, welche Prüfschranken nicht ausführbar sind. Behaupte nicht fälschlich, Git-Snapshots erstellt, Validatoren ausgeführt oder Graphexporte abgeschlossen zu haben.

## Reine Chat-/Custom-Instructions-Plattformen (D: manueller Rückfallmodus)

Nutzen Sie `novel-operating-system/SKILL.md` als Hauptanweisung und das vollständige `skills/`-Paket als abrufbare Dokumente. Dieser Modus kann Abläufe, Vorlagen, Schemata, Ausgabeformate, Regeln und Checklisten übertragen. Automatische Dateierstellung, Persistenz zwischen Gesprächsrunden, CLI-Validierung, ZIP-Installation oder Auslösererkennung sind nicht garantiert.

### Bereitstellungsprüfungen zur Vollendung unfertiger Werke

Bewahren Sie bei der Übergabe eines aufgegebenen Werks die üblichen Romanprojektdateien sowie `completion-brief.md`, `source-manifest.json`, Beleg-/Intentions-/Versions-/Verzweigungsregister, `rights-and-publication.md`, `completion-provenance.md`, `completion-state.json` und die Abschluss-Prüfschranke auf. Werke mit unbekannten oder nicht freigegebenen Rechten verwenden standardmäßig `private-only`/`research`; veröffentlichen Sie deren Prosa nicht direkt.

Legen Sie das Projekt nicht direkt in die Skill-ZIP-Datei. Übergeben Sie einen separaten Projektordner oder eine bereinigte ZIP-Datei:

1. Prüfen Sie zuerst auf sensible Informationen über reale Personen, private Quellen, Zugangsdaten, nicht autorisierte Quelltexte oder nicht zur Weitergabe bestimmte Entwürfe.
2. Führen Sie `snapshot_project.py`, `deep_consistency.py` und `chapter_gate.py` des vorhandenen Systems aus und nehmen Sie die Ergebnisse in den Übergabevermerk auf.
3. Benennen Sie in `project-brief.md` klar das letzte kanonische Kapitel, unvollendete Entwurfskapitel, die Übersteuerungsbefugnis des Autors und bekannte Risiken.
4. Nach dem Import sollte der Empfänger vor der Fortsetzung Story-Bibel, aktuellen Zustand, Zeitleiste, Leserregister, Handlungsfäden, Entitätsregister und letzte Zusammenfassung lesen.
