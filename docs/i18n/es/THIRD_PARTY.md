# Componentes y referencias de terceros

<!-- language-navigation -->

[繁體中文](../zh-TW/THIRD_PARTY.md) | [English](../../../THIRD_PARTY.md) | [日本語](../ja/THIRD_PARTY.md) | [한국어](../ko/THIRD_PARTY.md) | **Español** | [Français](../fr/THIRD_PARTY.md) | [Deutsch](../de/THIRD_PARTY.md) | [Português](../pt/THIRD_PARTY.md)

Novel OS contiene código y documentación originales del proyecto que interoperan con proyectos de terceros o los describen. Salvo indicación explícita en un archivo, los proyectos de terceros **no están incorporados** en este repositorio.

## Dependencias de ejecución u opcionales

| Componente | Uso | Licencia / fuente |
|---|---|---|
| Python | Ejecución (3.10+) | Python Software Foundation License |
| NetworkX | Algoritmos de grafos y exportación GraphML | BSD-3-Clause; https://networkx.org/ |
| PyYAML | Entrada de estado YAML para la utilidad de proyección NPC | MIT; https://pyyaml.org/ |
| MCP Python SDK | Cliente MCP local opcional de Instagram | MIT; https://github.com/modelcontextprotocol/python-sdk |
| Graphify (`graphifyy`) | Interoperabilidad opcional de análisis/exportación de grafos | El proyecto original declara Apache-2.0 e incluye material con licencia MIT; https://github.com/Graphify-Labs/graphify |

El servidor MCP anónimo de Instagram e Instaloader son componentes opcionales separados y no se incluyen aquí. Los operadores son responsables de instalarlos y cumplir las condiciones de la plataforma, la legislación aplicable, los controles de robots/acceso y las restricciones del proyecto que permiten únicamente datos públicos.

## Referencias de investigación

La documentación enlaza a artículos, especificaciones, libros, herramientas y proyectos públicos como citas de investigación. Los enlaces y las descripciones no incorporan el código ni el texto de esas obras a Novel OS. Si una contribución adapta código o texto en vez de limitarse a citar ideas, debe identificar la fuente exacta, la licencia, las modificaciones y la atribución requerida.

## Material adaptado incluido en esta distribución

- **Humanizer-zh**, copyright (c) 2026 歸藏, MIT: [fuente original en el commit f4518a8eab97b8bfebc66a89d34320a89bef6930](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930)
  - Adaptación: `skills/novel-human-voice-editor/references/humanizer-zh-checkpoints.md` traduce y condensa los 31 puntos de revisión editorial al chino tradicional y añade reglas de preservación y conflicto específicas para ficción
  - Se conserva el [aviso MIT original](../../../skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt), verificado con ese commit original exacto
  - El aviso acompaña a la habilidad en las fuentes, el paquete portátil y el entorno instalado. Se aplica al material original de terceros, **no** a Novel OS en su conjunto; el material creado por el proyecto se rige por separado por `LICENSE`

## Integraciones externas del anfitrión no distribuidas aquí

`lieflat-less-ai-tone` es una pasada de edición opcional suministrada por el anfitrión, no una de las 17 habilidades de ejecución. Su documento de integración registra una revisión externa, pero este repositorio no contiene una URL/licencia original verificada ni su implementación. No la descargue, incorpore ni afirme que se ejecutó automáticamente. Si falta, mantenga el flujo integrado de voz humana y registre que esta pasada adicional no se ejecutó. Verifique por separado la procedencia y la licencia antes de instalarla o distribuirla.

El adaptador de revisión independiente `minis-model-use` requiere su anfitrión original. Otros anfitriones deben proporcionar un sustituto configurado expresamente o registrar que no se ejecutó la revisión independiente por modelo. Las pruebas de regresión locales no utilizan modelos en vivo ni los servicios Graphify, MCP o Instagram.

## Límite de dependencias

Los paquetes opcionales anteriores no se empaquetan ni se instalan con la distribución principal. Sus obligaciones de licencia siguen correspondiendo a sus respectivas distribuciones; revise la versión original exacta antes de habilitar una integración o redistribuir un paquete combinado. Las pruebas principales se ejecutan sin estas dependencias. Este inventario ayuda a la revisión y no constituye asesoramiento jurídico.
