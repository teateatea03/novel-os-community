# Contrato del adaptador de host de Novel OS

<!-- language-navigation -->

[繁體中文](host-adapter-contract.md) | [English](host-adapter-contract.en.md) | [日本語](host-adapter-contract.ja.md) | [한국어](host-adapter-contract.ko.md) | **Español** | [Français](host-adapter-contract.fr.md) | [Deutsch](host-adapter-contract.de.md) | [Português](host-adapter-contract.pt.md)

Este contrato está dirigido a integradores de frameworks de IA distintos de Minis. Novel OS no es un plugin que pueda obtener acceso a archivos, acceso a modelos o memoria entre conversaciones simplemente subiendo un ZIP. Para que el despliegue se considere automatizado, el host debe proporcionar las siguientes capacidades.

## A. Interfaces mínimas que debe proporcionar el host

| Capacidad | Operaciones mínimas | Uso en Novel OS | Si no está disponible |
|---|---|---|---|
| Enrutador de skills | `load_skill(name)`/lectura de archivos de recursos | El coordinador carga dieciséis skills especializadas según la intención | Incluir manualmente la Skill adecuada en el prompt |
| Almacenamiento persistente | `read(path)`, `write(path)`, `list(path)`, `mkdir(path)` | Biblia del proyecto, capítulos, registros, estado, grafos e instantáneas | Modo exclusivamente documental; sin garantía de continuidad entre ejecuciones |
| Ejecutor de procesos | `run(argv, cwd)` | Ejecutar herramientas Python de inicialización, controles, estado y grafos | Usar manualmente plantillas y listas de comprobación; no afirmar que se ejecutó la validación |
| Identidad del proyecto | `project_id` estable → raíz de almacenamiento | Leer el estado de la misma novela en una conversación/trabajador nuevos | El usuario proporciona manualmente archivos/resúmenes cada vez |
| Bloqueo de escritura de rama | `lock(project,session,branch)`/bloqueo de transacciones | Serializar la recuperación, las comprobaciones de hashes obsoletos y los commits de eventos, estado y manifiesto | Permitir un solo escritor; no afirmar que es seguro con varios trabajadores |
| Adaptador de tareas de modelo | Aceptar `minis.model-task.v1`, persistir primero la programación, permitir que los trabajadores reclamen tareas con una concesión temporal y devolver un esquema fijo | Limitar los modelos L1/L2 a tareas individuales de extracción/planificación/renderizado/reparación; admitir reintento/cancelación/resultados obsoletos/recuperación tras reinicio | Modo documental o formularios manuales; los modelos no tienen autoridad sobre el estado |
| Versionado de runtime/eventos | Versión del runtime, esquema de eventos, contrato de transición, fixture de reproducción de referencia | Reproducir el historial antiguo tras una actualización sigue produciendo el mismo hash de estado; los contratos desconocidos se rechazan por seguridad | Congelar el runtime antiguo; actualizar solo después de una migración manual |
| Solucionador narrativo | Exploración acotada de estados de storylets | Encontrar estados inalcanzables, destinos rotos y bloqueos de avance, indicando los límites de exploración | Revisar las rutas manualmente; no afirmar que se validaron todas |
| Control de sugerencias de eventos aleatorios | `off`/`on-suggestion` por rama, ventana semántica, conjunto con semilla, auditoría no canónica | Ofrecer tarjetas de dirección opcionales solo en ventanas elegibles, conservando resultados sin evento y procedencia reproducible | Mantenerlo fijo en `off`; no realizar sorteos ocultos mediante prompts ni tratar las sugerencias como canon |
| Proyector de memoria/grafos | Evento → memoria episódica; eventos → proyección Graphify | Memoria trazable y grafos reconstruibles | Conservar los eventos; marcar los índices derivados como no actualizados |
| Índice Graphify de finalización | `sync_graph.py` sincroniza fuentes, afirmaciones y ramas con el `graph.json` existente | Fuentes, pruebas, versiones e hipótesis de finalización consultables | El grafo es un índice derivado y no debe sobrescribir la prosa/el canon en sentido inverso |

El ejecutor de procesos debe preferir **arrays argv a cadenas de shell concatenadas**, permanecer dentro de los espacios de trabajo del proyecto/las skills y conservar stdout, stderr y el código de salida como artefactos de los controles.

## B. Asignación de rutas

La configuración de despliegue debe proporcionar los siguientes valores. No codifique rutas de Minis de forma fija en otro entorno:

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

- `init_novel_project.py` puede leer `NOVEL_PROJECTS_ROOT` o aceptar un `--root` explícito.
- `SPECIAL_OBJECT_DATABASE_ROOT` guarda la base de datos autoritativa de objetos especiales en `graphify-out/graph.json`; `SPECIAL_OBJECT_DATABASE_WORK_ROOT` guarda JSON de lotes y paquetes de entrega, y no puede sustituir la copia autoritativa.
- `WORLD_DATABASE_ROOT` guarda la base de datos autoritativa de mundos en `graphify-out/graph.json`; `WORLD_DATABASE_WORK_ROOT` guarda JSON de lotes de mundos y paquetes de entrega, y no puede sustituir la copia autoritativa.
- Las demás raíces son ajustes del enrutador/adaptador del framework. Sustituya los marcadores `<..._ROOT>` de las Skills pertinentes por rutas persistentes reales.
- Todos los archivos de una novela deben estar bajo la misma raíz de proyecto, que debe poder volver a leerse; no conserve únicamente el capítulo más reciente en el contexto temporal del chat.

## C. Procedimiento de despliegue obligatorio

1. Extraiga el paquete y ejecute primero lo siguiente:

   ```bash
   # Confirme primero que dispone de Python, hashes y la prueba básica completa:
   python3 scripts/install_novel_os.py --target "$SKILLS_ROOT" --smoke-test
   ```

2. Registre **17** Skills (el coordinador + 16 Skills especializadas). `novel-reality-state-engine` debe proporcionar JSON de eventos/estado, una Reality Card y un Reality Gate ejecutable. `novel-model-capability-compatibility` debe proporcionar pruebas de texto/JSON/herramientas/estado del endpoint real, niveles de capacidad y alternativas. `novel-sensory-sound-prose` debe conservar su contrato de prosa de sonido/cinco sentidos. Mantenga las rutas relativas entre directorios hermanos.
3. Asigne `project_id` a las raíces persistentes anteriores y autorice al agente a leer y escribir los archivos de ese proyecto.
4. Ejecute el inicializador para un proyecto nuevo y confirme que Markdown/JSON/`graphify-out/graph.json` se crean correctamente.
5. Cierre e inicie una nueva ejecución del agente, pidiéndole que lea el estado antes de continuar la historia para verificar que no depende de contexto temporal.
6. Haga que dos trabajadores intenten commits simultáneos sobre el mismo hash de estado de origen: exactamente uno debe tener éxito y el otro debe recibir stale-hash/conflicto. Después, verifique el hash del estado actual mediante reproducción de eventos.
7. Cree dos memorias episódicas y verifique que la reflexión cite al menos dos ID de pruebas existentes. Compile una tarea de renderizado L1 y confirme que el paquete no contiene verdad oculta y que tiene `may_commit_state=false`.
8. Reconstruya la proyección interactiva de Graphify a partir de los eventos. Eliminarla y reconstruirla debe producir el mismo hash de origen.
9. Conserve al menos un fixture de historial de referencia. Reproducirlo con un runtime nuevo debe producir el hash de estado esperado, y los contratos de transición desconocidos deben rechazarse.
10. Cree una actividad de modelo y verifique la recuperación tras vencer la concesión temporal, que los resultados antiguos se marquen como obsoletos cuando avance el estado y que la consola del autor se bloquee mientras haya una actividad pendiente.
11. Cree un fixture de storylets con estados inalcanzables, destinos rotos y bloqueos de avance; confirme que el solucionador los detecte todos e indique expresamente la profundidad máxima y el máximo de estados.
12. Tras compactar los eventos, elimine el índice y altere el archivo histórico. El control de integridad del manifiesto debe rechazarlo antes de reconstruir el índice.
13. Verifique que una rama nueva tenga `off` por defecto, sin sorteos ni escrituras de auditoría. Después de que el usuario active `on-suggestion`, use una semilla fija en un límite de escena para obtener el mismo resultado de sugerencia/sin evento, y confirme que el registro de eventos canónicos, State, Graph, Knowledge y la prosa permanezcan sin cambios.
14. Envíe solicitudes de entrada meta, una consecuencia directa pendiente, situaciones de alta presión sin una pausa natural, una consecuencia determinista existente y una amenaza no anticipada; todas deben suprimirse. Adoptar una sugerencia solo puede crear una entrega de planificación y debe enumerar los controles Reality/Knowledge/Agency/Behavior/World/Canon.
15. Verifique el hash/bytes/recuento del manifiesto del segmento activo: después de eliminar el índice de eventos, alterar el registro activo debe provocar un rechazo seguro. Las reclamaciones de actividad devuelven un token de exclusión; la finalización debe rechazarse con tokens antiguos, tokens ausentes o concesiones vencidas. Todos los ID basados en archivos deben rechazar el recorrido de directorios. Reintentar el mismo `request_id` de evento aleatorio no debe repetir el sorteo ni crear una segunda entrada de auditoría. Una cadena de hashes de auditoría alterada no debe reproducirse, y las sugerencias vencidas no deben crear entregas de adopción.

## D. Adaptadores de herramientas opcionales

### Investigación web

Si el host ofrece herramientas de navegador/búsqueda, el enrutador debe registrar resultados de búsqueda, URL, editores, fechas y citas breves en los campos de pruebas de investigación/grafos. Sin navegador, solo puede procesar material proporcionado por el usuario, debe usar `【待定】` («sin determinar»)/`【提案】` («propuesta») y no debe fingir haber verificado las fuentes.

### Revisión por segundo modelo/subagente

`long-form-novel-writer/scripts/independent_review.py` llama actualmente a `minis-model-use` de Minis. Los frameworks distintos de Minis deben hacer una de estas dos cosas:

1. Escribir un adaptador de framework que acepte `role`, `prompt` y `max_tokens`, llame a otro modelo/subagente y guarde el texto original y el JSON analizado en `reviews/`; o
2. Desactivar la revisión independiente, usar en su lugar controles locales/listas manuales y marcar «segundo modelo no ejecutado» en la entrega.

En ambos casos, conserve estas reglas de salida: `machine_suggestion` no puede ascender directamente a `[CANON]`; los problemas sin dos pruebas de apoyo solo se incluyen en `questions`; los fallos deben producir un artefacto `unavailable` y nunca contabilizarse silenciosamente como aprobados.

### Grafos y control de versiones

- `networkx`: habilita path, affected, GraphML y funciones relacionadas.
- `graphifyy` + `networkx`: habilita HTML de Graphify, análisis de comunidades y exportaciones Cypher.
- Git: se usa solo para commits/ramas; las instantáneas de archivos siguen disponibles sin Git.

Son mejoras, no requisitos previos para empezar una novela.

## E. Lógica mínima del enrutador

```text
if la solicitud es crear/actualizar/consultar/comparar/exportar una base de datos de objetos especiales:
    cargar special-object-database-builder
    añadir novel-worldbuilding-architect + knowledge-relationship-graph
    añadir character-db + behavior cuando importe el operador/la máquina autónoma/la personalidad
    añadir long-form cuando esté vinculada a un proyecto de novela o al estado de un capítulo
elif la solicitud es crear/actualizar/consultar/exportar una base de datos de mundos:
    cargar novel-world-database-builder
    añadir novel-worldbuilding-architect + knowledge-relationship-graph
    añadir long-form cuando esté vinculada a un proyecto de novela o al estado de un capítulo
elif la solicitud es escritura entre capítulos/continuación/revisión del esquema:
    cargar long-form + behavior
    añadir world/style/graph solo cuando el estado de la historia lo requiera
elif la solicitud es investigación de personajes:
    cargar character-deep-digger
    añadir behavior + character-db/graph cuando se necesiten pruebas o persistencia
elif la solicitud es una revisión de voz humana/chino tradicional de Taiwán/voz del personaje:
    cargar human-voice-editor después de comprobar contenido/continuidad/estilo
elif la solicitud es completar una novela abandonada/inacabada, la intención del autor original o un final alternativo:
    cargar unfinished-novel-completion
    añadir long-form + herramientas de pruebas/fuentes + world/behavior/style/graph según sea necesario
elif la solicitud es ficción interactiva de entrada libre:
    cargar immersive-interactive-fiction
    añadir world/behavior/style/graph según la complejidad de la escena
```

El coordinador debe ocuparse primero de este enrutador. No coloque indiscriminadamente todas las Skills en el contexto del modelo en cada turno.

## F. Lo que el paquete no puede hacer automáticamente

- Instalar Skills, configurar claves API, habilitar permisos de herramientas o crear bases de datos en cuentas en la nube no autorizadas.
- Dar a un modelo solo de chat un shell, un sistema de archivos, memoria permanente o capacidades de múltiples modelos.
- Anular las políticas de contenido, límites de tokens, reglas de privacidad o restricciones de red del modelo/plataforma de destino.

Si falta algún requisito previo, use los modos alternativos B/C/D de [platform-compatibility.es.md](platform-compatibility.es.md) y enumere cada función desactivada en el informe de despliegue.
