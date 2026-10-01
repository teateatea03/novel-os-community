# Drittkomponenten und Referenzen

<!-- language-navigation -->

[繁體中文](THIRD_PARTY.zh-TW.md) | [English](THIRD_PARTY.md) | [日本語](THIRD_PARTY.ja.md) | [한국어](THIRD_PARTY.ko.md) | [Español](THIRD_PARTY.es.md) | [Français](THIRD_PARTY.fr.md) | **Deutsch** | [Português](THIRD_PARTY.pt.md)

Novel OS enthält eigenen Projektcode und eigene Dokumentation, die mit Drittprojekten zusammenarbeiten oder sie erläutern. Sofern eine Datei nicht ausdrücklich etwas anderes angibt, werden Drittprojekte **nicht in dieses Repository eingebunden**.

## Laufzeit- oder optionale Abhängigkeiten

| Komponente | Nutzung | Lizenz / Quelle |
|---|---|---|
| Python | Laufzeit (3.10+) | Python Software Foundation License |
| NetworkX | Graphalgorithmen und GraphML-Export | BSD-3-Clause; https://networkx.org/ |
| PyYAML | YAML-Zustandseingabe für das NPC-Projektionswerkzeug | MIT; https://pyyaml.org/ |
| MCP Python SDK | Optionaler lokaler Instagram-MCP-Client | MIT; https://github.com/modelcontextprotocol/python-sdk |
| Graphify (`graphifyy`) | Optionale Zusammenarbeit bei Graphanalyse/-export | Das Ursprungsprojekt nennt Apache-2.0 und enthält MIT-Lizenzmaterial; https://github.com/Graphify-Labs/graphify |

Der anonyme Instagram-MCP-Server und Instaloader sind separate optionale Komponenten und hier nicht enthalten. Betreiber sind für deren Installation und die Einhaltung der Plattformbedingungen, des geltenden Rechts, der Robots-/Zugriffskontrollen und der Projektbeschränkung auf öffentliche Daten verantwortlich.

## Recherchereferenzen

Die Dokumentation verlinkt Artikel, Spezifikationen, Bücher, Werkzeuge und öffentliche Projekte als Recherchequellen. Links und Beschreibungen übernehmen weder deren Code noch deren Text in Novel OS. Wenn ein Beitrag Code oder Text anpasst, statt nur Ideen zu zitieren, muss er die genaue Quelle, Lizenz, Änderungen und erforderliche Urheberangabe benennen.

## In dieser Distribution enthaltenes angepasstes Material

- **Humanizer-zh**, Copyright (c) 2026 歸藏, MIT: [Ursprungsquelle bei Commit f4518a8eab97b8bfebc66a89d34320a89bef6930](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930)
  - Anpassung: `skills/novel-human-voice-editor/references/humanizer-zh-checkpoints.md` übersetzt/kürzt die 31 redaktionellen Prüfpunkte ins traditionelle Chinesisch und ergänzt Regeln zur Erhaltung und Konfliktbehandlung speziell für Fiktion
  - Erhaltener [ursprünglicher MIT-Hinweis](skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt), mit exakt diesem Ursprungs-Commit abgeglichen
  - Der Hinweis begleitet den Skill im Quellcode, im portablen Paket und in der installierten Laufzeit. Er gilt für das ursprüngliche Material, **nicht** für Novel OS insgesamt; projektspezifisches Material unterliegt gesondert der [Lizenz](LICENSE.de.md)

## Hier nicht mitgelieferte externe Hostintegrationen

`lieflat-less-ai-tone` ist ein optionaler, vom Host bereitgestellter redaktioneller Durchlauf und keiner der 17 Laufzeit-Skills. Sein Integrationsdokument nennt eine externe Revision, aber dieses Repository enthält weder eine verifizierte Ursprungs-URL/Lizenz noch seine Implementierung. Laden Sie ihn nicht automatisch, binden Sie ihn nicht ein und behaupten Sie nicht, er sei automatisch ausgeführt worden. Fehlt er, behalten Sie den eingebauten Ablauf zur menschlichen Erzählstimme bei und kennzeichnen Sie diesen zusätzlichen Durchlauf als nicht ausgeführt. Prüfen Sie Herkunft und Lizenz gesondert vor Installation oder Weiterverbreitung.

Der Adapter für unabhängige Prüfung `minis-model-use` benötigt seinen ursprünglichen Host. Andere Hosts müssen einen ausdrücklich konfigurierten Ersatz bereitstellen oder die unabhängige Modellprüfung als nicht ausgeführt kennzeichnen. Lokale Regressionstests nutzen keine realen Modelle, Graphify-, MCP- oder Instagram-Dienste.

## Abhängigkeitsgrenze

Die oben genannten optionalen Pakete werden von der Kerndistribution weder mitgeliefert noch installiert. Ihre Lizenzpflichten verbleiben bei den jeweiligen Distributionen; prüfen Sie die genaue Ursprungsversion, bevor Sie eine Integration aktivieren oder ein kombiniertes Paket weiterverbreiten. Kerntests laufen ohne diese Abhängigkeiten. Diese Übersicht ist eine Prüfhilfe, keine Rechtsberatung.
