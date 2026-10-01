# Compatibilidad de plataformas y matriz de dependencias de Novel OS

<!-- language-navigation --> [繁體中文](platform-compatibility.md) | [English](platform-compatibility.en.md) | [日本語](platform-compatibility.ja.md) | [한국어](platform-compatibility.ko.md) | **Español** | [Français](platform-compatibility.fr.md) | [Deutsch](platform-compatibility.de.md) | [Português](platform-compatibility.pt.md)

Este documento debe entregarse con el ZIP. Novel OS es una colección de **instrucciones de skills + plantillas locales/validadores Python**, no un modelo independiente, una plataforma de chat, una base de datos vectorial ni un servicio en la nube. Que pueda «desplegarse automáticamente» depende de si el framework de IA de destino permite leer skills de varios archivos, escribir archivos, ejecutar comandos y, opcionalmente, llamar a modelos/acceder a la red.

```text
- 1 coordinador + 16 skills colaboradoras, un total de 17 Skills de runtime (el código fuente también incluye el exportador)
- Compatibilidad de capacidades del modelo: `novel-model-capability-compatibility`, responsable de pruebas del endpoint real, L0–L5, adaptadores, alternativas y regresiones tras el cambio
- Estado de realidad: `novel-reality-state-engine`, que proporciona una cadena de validación evento → estado → capacidad → comportamiento → prosa
- Bases de datos de mundos: `novel-world-database-builder`
- Bases de datos de objetos especiales: `special-object-database-builder`, con la raíz autoritativa en `SPECIAL_OBJECT_DATABASE_ROOT`
- Finalización de obras abandonadas: unfinished-novel-completion
```

## 1. Componentes principales y sus dependencias

| Componente/función | Sistema/formato utilizado | Dependencias mínimas | Dependencias opcionales | Alternativa si no está disponible |
|---|---|---|---|---|
| Despacho de skills | Metadatos YAML de `SKILL.md` + Markdown; `novel-operating-system` | Una IA/agente que pueda cargar varios archivos de texto | Un runtime de Skills que las active automáticamente por su descripción | Usar el coordinador como prompt de sistema/instrucciones del proyecto y adjuntar manualmente las demás skills |
| Persistencia del proyecto | Markdown, JSON, carpetas ordinarias | Lectura/escritura de archivos UTF-8 | Git | Mantener archivos con los mismos nombres en chat/Canvas/documentos en la nube; indicar expresamente que no se garantiza la persistencia entre turnos |
| Inicialización de narrativa larga y controles locales | CLI de Python, biblioteca estándar | **Python 3.10+**, shell, disco con permiso de escritura | Git | Copiar manualmente plantillas y listas de comprobación; no afirmar que se ejecutaron los controles/instantáneas |
| Grafo autoritativo de relaciones | JSON de nodos y enlaces compatible con Graphify | Python 3.10+ (inicialización, validación JSON) | `networkx`: path/affected; `graphifyy` + `networkx`: HTML, análisis de comunidades, exportación Cypher | Guardar/leer graph.json; consultar relaciones manualmente, sin afirmar que se generaron visualizaciones o rutas más cortas |
| Base de datos de mundos | JSON compatible con Graphify; nodos de mundo/ubicación/facción/recurso/regla/evento/afirmación, pruebas de fuentes y lotes incrementales | Python 3.10+, archivos UTF-8 persistentes | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | Guardar graph.json y registros Markdown; realizar manualmente las comprobaciones de versiones/conocimiento, sin afirmar que las exportaciones visuales están completas |
| Base de datos de objetos especiales | JSON compatible con Graphify; nodos de objeto/versión/variante/módulo/capacidad/especificación/energía/restricción/posesión/operación/ciclo de vida y pruebas de fuentes | Python 3.10+, archivos UTF-8 persistentes | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | Guardar graph.json y registros de objetos; comprobar manualmente conflictos de versiones/especificaciones, sin afirmar que las exportaciones visuales están completas |
| Ficción interactiva | Estado compatible con JSON, registro de turnos en Markdown | Lectura/escritura de archivos; Python 3.10+ permite validación/puntos de control | Memoria a largo plazo/base de datos | Revisar en cada turno el estado pegado en el chat; no se garantiza su conservación tras reabrir una conversación |
| Investigación y validación de fuentes para completar obras | Obras inacabadas | `unfinished-novel-completion`; las herramientas de investigación/adjuntos son opcionales | `source_ingest.py` registra hashes, versiones, grado de completitud y situación de derechos; `completion_gate.py` comprueba afirmaciones excesivas sobre la intención y los límites de publicación | |
| Revisión independiente por modelo | CLI/API de llamada a modelos del host | Ninguna; no es obligatoria | Capacidad para llamar a un segundo modelo o subagente | Usar una lista manual/del mismo modelo; no afirmar «revisado por un modelo independiente» |

### Investigación de fuentes y herramientas para obras inacabadas

Las herramientas básicas de `unfinished-novel-completion` usan únicamente la biblioteca estándar de Python: `init_completion_project.py`, `source_ingest.py`, `compare_source_versions.py`, `branch_diff.py`, `feasibility_report.py`, `sync_graph.py`, `completion_gate.py`, `provenance_report.py` y `run_regression.py`. El acceso a la red, OCR, herramientas PDF, navegadores y un segundo modelo son opcionales. Sin ellos, aún se pueden procesar archivos proporcionados por el usuario, pero deben identificarse el alcance de las fuentes y las incógnitas; no finja que se realizó una verificación.

### Entorno mínimo «totalmente automatizado»

- **Python 3.10 o posterior:** los scripts principales actuales usan la sintaxis de unión de tipos `X | None`; se recomienda Python 3.11+.
- **Shell POSIX o ejecutor de procesos equivalente:** para ejecutar la CLI de Python.
- **Sistema de archivos persistente con permiso de escritura:** para instalar skills y guardar proyectos de novelas; se requiere al menos un directorio de skills y uno de proyectos con permiso de escritura.
- **Compatibilidad con archivos UTF-8:** historias, plantillas, JSON y contenido en chino tradicional usan UTF-8.
- **Extracción de ZIP:** necesaria solo para la distribución en ZIP; como alternativa se puede usar Git/subida de carpetas.
- **Biblioteca estándar local:** los scripts principales de inicialización, registros, controles, estado y paquetes dependen únicamente de la biblioteca estándar de Python; la prueba básica no requiere `pip install`.

Estas funciones no requieren una clave API, una base de datos, Node.js ni acceso a la red.

### Dependencias opcionales (mejoras, no el flujo básico)

```bash
# Rutas de grafos, consultas en cascada, GraphML
python -m pip install networkx

# Exportaciones HTML/comunidades/Cypher de Graphify; el paquete original se llama graphifyy
python -m pip install graphifyy networkx

# Instantáneas de versiones de Git y commits protegidos por controles
git --version
```

- `relationship_graph.py init/validate/search/neighbors/timeline/add/import/snapshot` puede usar únicamente la biblioteca estándar de Python; `path`/algunas comprobaciones de ciclos requieren `networkx`.
- `relationship_graph.py export` requiere **`networkx` + `graphifyy`**. Sin ellos, conserve `graph.json` y no afirme falsamente que se generaron salidas HTML/GraphML/Cypher.
- `independent_review.py` es actualmente un **adaptador específico de Minis** que llama a `minis-model-use`. En otro framework, sustitúyalo por el adaptador de segundo modelo/subagente/API de ese framework o desactive este paso de revisión opcional.
- `novel_git.py` es una capa opcional de control de versiones. Sin Git, `snapshot_project.py` todavía puede crear instantáneas de archivos.

## 3.2 Puntos de integración con el host y sustituciones obligatorias

Los formatos de datos principales del paquete son portátiles, pero el integrador debe ocuparse de estos **puntos de integración con el host/framework**:

| Punto de integración | Uso actual en Minis | Qué deben hacer otros frameworks de IA |
|---|---|---|
| Raíz predeterminada de novelas | `<NOVEL_PROJECTS_ROOT>` | Configurar `NOVEL_PROJECTS_ROOT` o pasar `--root <persistent-projects-root>` a cada inicializador; no suponer que existe `<MINIS_ROOT>` |
| Raíz de la base de datos de personajes | `<CHARACTER_DATABASE_ROOT>` | Asignar `<CHARACTER_DATABASE_ROOT>` y la preparación de lotes a `<CHARACTER_DATABASE_WORK_ROOT>`; ambos deben ser accesibles para el mismo proyecto/agente |
| Raíz de la base de datos de objetos especiales | `<SPECIAL_OBJECT_DATABASE_ROOT>` | Asignar `<SPECIAL_OBJECT_DATABASE_ROOT>` y la preparación de lotes a `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>`; ambos deben ser accesibles para el mismo proyecto/agente |
| Raíz del estado de ficción interactiva | `<INTERACTIVE_PROJECTS_ROOT>` | Asignar `<INTERACTIVE_PROJECTS_ROOT>` y garantizar la lectura de estado/puntos de control/registros entre ejecuciones |
| Revisión independiente | `minis-model-use run` | Reescribir el adaptador de comandos de `independent_review.py` o crear una función de subagente equivalente; conservar el esquema JSON, los artefactos de error y la regla contra la promoción automática al canon |
| Descubrimiento de skills | Registro de skills de Minis + directorios hermanos | Registrar **17** descripciones (el coordinador + dieciséis skills especializadas) o construir un enrutador de intenciones; permitir al agente leer archivos de recursos hermanos cuando sea necesario |
| Estado a largo plazo | Directorio compartido de Minis | Conectar un volumen duradero, base de datos, almacén de artefactos o gestor de puntos de control del framework, recuperando el estado por ID de proyecto |
| Herramientas de investigación | Navegador/shell de Minis | Conectar herramientas de navegador/búsqueda/archivos del framework; de lo contrario, limitar la investigación a material proporcionado por el usuario |

- `init_novel_project.py` ya admite `NOVEL_PROJECTS_ROOT`; un `--root` explícito tiene prioridad. Los marcadores `<..._ROOT>` de las bases de datos de personajes/mundos/objetos especiales y de ficción interactiva deben sustituirse mediante el enrutador/la configuración de despliegue del framework. Cada `<MINIS_ROOT>/...` de la documentación original es una **ruta predeterminada de ejemplo** fuera de Minis, no un requisito obligatorio del sistema.

## 4. Niveles de capacidad de los frameworks de IA

### A | Skills nativas + shell + sistema de archivos (modo completo)

Para frameworks con runtime de Skills, herramientas de agente y sandbox/terminal. Instale directamente el paquete completo ejecutando:

```bash
python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test
```

**El framework debe:**

1. Registrar `<SKILLS_DIR>/novel-operating-system/SKILL.md` como skill principal activable.
2. Conservar las **17** carpetas de skills (el coordinador + dieciséis skills colaboradoras) como hermanas; no subir únicamente el archivo de entrada.
3. Permitir al agente leer `SKILL.md`, plantillas, referencias y scripts de las skills hermanas.
4. Proporcionar una herramienta de comandos segura o un ejecutor de procesos para `python3`.
5. Tras reindexar/reiniciar el registro de skills, usar los resultados de la prueba básica para la aceptación.

**Mejoras recomendadas:** herramientas de investigación web, un adaptador de segundo modelo, Git, `networkx` y `graphifyy`.

### B | Frameworks personalizados de agentes/llamada a herramientas (requiere adaptador)

Para frameworks con prompt de sistema, llamadas a funciones y herramientas de archivos, pero que no interpretan `SKILL.md`.

**El integrador del framework debe:**

1. Colocar `novel-operating-system/SKILL.md` en las instrucciones de sistema/desarrollador del agente; conservar la descripción YAML como reglas de enrutamiento.
2. Convertir las otras **dieciséis** skills en documentos de referencia recuperables o construir un enrutador que cargue el `SKILL.md` apropiado según la intención del usuario.
3. Conectar las herramientas:
   - shell → scripts Python;
   - lectura/escritura/listado de archivos → archivos y estado del proyecto;
   - búsqueda web/navegador → investigación de fuentes públicas;
   - segundo modelo/subagente → adaptador sustituto de `independent_review.py`.
4. Sustituir la llamada a `minis-model-use`, específica de Minis, por el cliente de modelos del framework. Conservar el esquema JSON original de revisión, los artefactos de fallo y el principio de que «machine_suggestion no asciende automáticamente a canon».
5. Especificar una clave de almacenamiento/espacio de trabajo duradero para que los archivos de la misma obra se mantengan entre conversaciones/trabajadores.
6. Implementar la activación automática de skills o desactivarla expresamente; poner **17 documentos Skill** en el contexto no justifica afirmar que colaborarán automáticamente.

### C | IA de chat que solo admite subir archivos de conocimiento/instrucciones personalizadas (modo documental)

Las convenciones de escritura, plantillas, esquemas de datos y listas de comprobación son portátiles, pero no hay automatización real.

**Obligatorio:** subir todo el subárbol `skills/`; establecer el coordinador como instrucciones del proyecto; en cada turno, adjuntar o hacer que la IA consulte el estado actual de la obra, la biblia narrativa, la cronología, los archivos de personajes, el registro del lector y el resumen del capítulo anterior.

**No prometa:** creación automática de carpetas, controles CLI, verificación de hashes, Git, exportación Graphify, memoria entre chats, tareas en segundo plano ni revisión por segundo modelo.

### D | Modelos con un único prompt de sistema (alternativa manual)

Pegue un coordinador condensado en el prompt de sistema y use las skills especializadas y las plantillas de proyecto como base de conocimiento. El usuario/integrador debe guardar manualmente los documentos de estado producidos en cada turno. Esto conserva el marco de razonamiento, pero no equivale a Novel OS completo.

## 5. Lista de integración de frameworks habituales

| Tipo | Dónde se integra | Configuración obligatoria | Precaución principal |
|---|---|---|---|
| Estilo OpenAI Assistants/Responses | Instrucciones de sistema + búsqueda vectorial/de archivos + intérprete de código/sandbox personalizado | Construir un enrutador, un almacén persistente de archivos y un adaptador de ejecución Python | No suponer que los archivos se sincronizan automáticamente entre ejecuciones; deben guardarse explícitamente los archivos del proyecto |
| Estilo Claude Projects/MCP | Instrucciones del proyecto + archivos de conocimiento; servidor MCP de sistema de archivos/shell | Exponer las skills como recursos; usar MCP para lectura/escritura/ejecutor/web | Sin MCP, es nivel C y no puede ejecutar scripts |
| Estilo Gemini Gems/Vertex Agent | Instrucción de sistema + File Search/Code Execution/Cloud Storage | Conectar almacenamiento duradero, un enrutador de funciones y un ejecutor Python | Por sí solas, las instrucciones de Gem generalmente no proporcionan flujos de archivos entre conversaciones |
| Estilo LangChain/LangGraph/CrewAI/AutoGen | Nodo enrutador + herramientas de archivos + herramienta de subprocesos + gestor duradero de puntos de control | Cargar skills por intención, conservar el ID de proyecto y construir un adaptador de agente revisor | Deben implementarse el descubrimiento de skills y los puntos de control de estado; extraer el paquete no los activa por sí solo |
| Estilo Open WebUI/AnythingLLM/Dify/Flowise | Base de conocimiento + flujo de agente/nodos de herramientas | Subir archivos de skills, conectar herramientas shell/Python y montar un volumen persistente | El chat RAG puro es nivel C; se requieren flujos de trabajo para alcanzar A/B |
| Host de base de datos de mundos | `WORLD_DATABASE_ROOT` + `WORLD_DATABASE_WORK_ROOT` | Montar un grafo de mundo persistente y un espacio de trabajo de lotes; proporcionar snapshot/validate/affected/export | Sin ejecutor de procesos, guardar solo JSON/Markdown y no afirmar que se ejecutó la CLI de Graphify |
| Host de base de datos de objetos especiales | `SPECIAL_OBJECT_DATABASE_ROOT` + `SPECIAL_OBJECT_DATABASE_WORK_ROOT` | Montar un grafo persistente de objetos especiales y un espacio de trabajo de lotes; proporcionar snapshot/validate/affected/export | Sin ejecutor de procesos, guardar solo JSON/Markdown y no afirmar que se ejecutó la validación o exportación de objetos especiales |
| Agentes de programación como Cursor/Claude Code/Codex CLI | Directorio de skills/comandos + espacio de trabajo | Instalar **17** carpetas y configurar Python y la raíz del espacio de trabajo | El adaptador de revisión conversacional por modelo debe reescribirse para la CLI correspondiente |

Estos nombres solo ilustran tipos de integración. Las versiones, los planes y los permisos de los productos varían; consulte su documentación más reciente antes del despliegue.

## 6. Lista de aceptación del despliegue

Después de la integración, el host o integrador debe verificar cada punto:

- [ ] Se pueden leer `novel-operating-system` y las dieciséis skills especializadas vecinas.
- [ ] Tras escribir un archivo de prueba, una nueva ejecución/conversación del agente puede volver a leerlo.
- [ ] `python3 --version` es ≥ 3.10; si se necesitan exportadores de grafos, se pueden importar `networkx`/`graphifyy`.
- [ ] `python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test` pasa o se documentan expresamente los elementos que no pueden ejecutarse.
- [ ] Un proyecto de novela de prueba nuevo tiene creados su biblia narrativa, estado, cronología, registro del lector y graph.json.
- [ ] El agente escribe un pasaje corto, actualiza el estado y continúa en una nueva ejecución, demostrando que la continuidad no depende solo del contexto restante.
- [ ] Si la investigación está habilitada, puede registrar URL/fuentes/confianza en vez de tratar fragmentos de búsqueda como canon.
- [ ] Si la revisión por segundo modelo está habilitada, los fallos del adaptador producen únicamente un artefacto de no disponibilidad, sin bloquear ni inventar resultados.

## 7. Limitaciones de plataforma y límites de responsabilidad

- Las políticas de contenido, permisos de herramientas, límites de tokens, retención de datos y reglas de red del modelo de destino son independientes de Novel OS y esta Skill no puede anularlos.
- «Despliegue automático» significa instalación, creación de estructuras y carga del enrutador automáticas dentro de un **framework de agentes con permisos de instalación/archivos/shell**. No significa instalar permanentemente el ZIP por dárselo a cualquier modelo de chat.
- Los modelos externos, navegadores y Git son mejoras opcionales. Cuando falten, indique expresamente el modo alternativo; no oculte carencias de capacidad afirmando que el trabajo está completo.
