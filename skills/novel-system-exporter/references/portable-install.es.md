# Importación y despliegue de Novel OS

<!-- language-navigation --> [繁體中文](portable-install.md) | [English](portable-install.en.md) | [日本語](portable-install.ja.md) | [한국어](portable-install.ko.md) | **Español** | [Français](portable-install.fr.md) | [Deutsch](portable-install.de.md) | [Português](portable-install.pt.md)

## Empezar con un inventario de capacidades: elegir el modo de despliegue adecuado

Antes de la entrega, pida al entorno de destino que responda:

```text
1. ¿Puede instalar varias Skills/comandos? ¿Dónde está el directorio o la configuración del punto de entrada?
2. ¿Puede el agente leer y escribir archivos persistentes, listar directorios y ejecutar comandos de Python/shell?
3. ¿Qué versión de Python está disponible? ¿Se permite instalar networkx, graphifyy y Git?
4. ¿Dispone de herramientas web/navegador, un segundo modelo o subagentes, y cómo se invocan mediante herramientas?
5. ¿Dónde se conservan los archivos del proyecto entre conversaciones nuevas, trabajadores nuevos o reinicios?
```

Elija según las respuestas: **A: instalación completa** (Skills + shell + almacenamiento), **B: integración mediante adaptador** (herramientas de agente personalizadas), **C: modo de archivos de conocimiento** o **D: modo manual con un único prompt**. Consulte [platform-compatibility.es.md](platform-compatibility.es.md) para la evaluación completa, los paquetes y los requisitos de adaptadores de cada framework. Sin los requisitos previos de A/B, no afirme que el «despliegue automático» está completo.

## Plataformas de IA con directorios de skills personalizados (A: modo completo)

1. Extraiga el ZIP.
2. Ejecute lo siguiente desde el directorio raíz extraído:

   ```bash
   python3 scripts/install_novel_os.py --target /path/to/agent/skills --smoke-test
   ```

3. Haga que la plataforma vuelva a explorar sus skills o reinicie su índice de skills.
4. Pruebe con «Crear un proyecto de novela larga». Esto debería activar `novel-operating-system`, crear la estructura del proyecto, determinar si se necesita investigación/construcción de mundos/comportamiento/estilo/grafos y completar la planificación y los controles antes de redactar la prosa.

**Actualizaciones:** añada `--upgrade`. Antes de sustituirlas, el instalador mueve las skills existentes con los mismos nombres a `<target>/backups/novel-os-<timestamp>-<unique>/`; si se produce un fallo, restaura los archivos originales.

### Licencias y avisos de terceros

El ZIP completo debe conservar las ocho versiones lingüísticas de la licencia raíz, la guía de terceros y las condiciones comerciales (24 documentos; los nombres exactos figuran en el contrato del paquete), junto con los archivos originales de licencias de terceros de cada skill. El instalador guarda estos avisos en `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`, conservando sus rutas relativas originales para que los enlaces a licencias de los documentos sigan funcionando. Los avisos de los proyectos originales incluidos en las skills también permanecen en sus ubicaciones originales. No sobrescribe el `LICENSE` ni el directorio `docs/` de la raíz del host. Los avisos anteriores a la actualización se guardan junto con las skills originales en la copia de seguridad de esa actualización.

`novel-operating-system/INSTALLATION.json` registra las rutas de origen/instalación, el SHA-256 y el número de bytes de cada aviso. Tras la instalación, ejecute esta comprobación de solo lectura desde el ZIP extraído:

```bash
python3 scripts/install_novel_os.py --target /path/to/agent/skills --verify-installed-notices
```

Los archivos ausentes o modificados provocan un fallo. Esta es una comprobación de integridad local, no un sustituto de una fuente de versiones de confianza. Consulte el inventario explícito de documentos en [bundle-contract.es.md](bundle-contract.es.md). Los borradores de discusión no constituyen licencias vigentes y no se exportan como condiciones formales.

Los modos de adaptación manual B/C/D también deben entregar conjuntamente la licencia del proyecto/las condiciones comerciales y todos los avisos de los proyectos originales. No copie únicamente `skills/` omitiendo los documentos de licencia.

## Frameworks de agentes personalizados o de llamada a herramientas (B: requiere adaptador)

Si un framework no tiene un runtime nativo de `SKILL.md`, pero sí ofrece un prompt de sistema, llamadas a funciones y herramientas de archivos/comandos, extraer el ZIP por sí solo no completa el despliegue. El integrador debe:

1. Colocar `novel-operating-system/SKILL.md` en las instrucciones de sistema/desarrollador y utilizar su descripción para crear un enrutador de intenciones.
2. Poner las dieciséis skills especializadas a disposición del enrutador como recursos que pueda leer cuando sea necesario; conservar las relaciones relativas entre carpetas.
3. Para una obra abandonada o inacabada, completar primero la entrega de fuentes/canon/pruebas/intención/viabilidad/ramas/derechos/procedencia de `unfinished-novel-completion` y, después, pasar la rama seleccionada al escritor de narrativa larga.
4. Conectar la lectura/escritura de archivos, el listado de directorios, los procesos de Python, un espacio de trabajo persistente, `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`, `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` y la investigación web con la API de herramientas del framework.
5. Sustituir la llamada a `minis-model-use` de `independent_review.py` por la integración de segundo modelo/subagente/API de la plataforma. Si no existe ninguna, desactivar este paso y registrarlo como no ejecutado.
6. Utilizar la lista de aceptación del despliegue de la documentación para comprobar la persistencia de archivos entre ejecuciones y las actualizaciones de estado posteriores a cada capítulo.

Consulte [platform-compatibility.es.md](platform-compatibility.es.md) para los puntos de integración habituales de LangGraph/CrewAI/AutoGen, MCP, OpenAI/Claude/Gemini y Dify/Flowise/Open WebUI. Todos requieren que el integrador del framework construya un enrutador/adaptador de herramientas; este ZIP no puede hacerlo automáticamente en una cuenta en la nube desconocida.

## Plataformas con un único campo de importación de Skill (C: modo de archivos de conocimiento)

Suba o pegue todo el directorio `skills/novel-operating-system/`, incluidas sus referencias, y mantenga las otras dieciséis carpetas de skills en el mismo nivel como adjuntos/archivos de conocimiento. Indique a la IA:

> Lee primero novel-operating-system/SKILL.md. Todas las skills hermanas son colaboradoras obligatorias de este sistema. Sin shell, crea archivos de proyecto equivalentes en Markdown/JSON y muestra qué controles no pueden ejecutarse. No afirmes falsamente haber creado instantáneas de Git, ejecutado validadores o completado exportaciones de grafos.

## Plataformas solo de chat o de instrucciones personalizadas (D: alternativa manual)

Utilice `novel-operating-system/SKILL.md` como instrucciones principales y el paquete completo `skills/` como documentos de consulta. Este modo permite trasladar flujos de trabajo, plantillas, esquemas, formatos de salida, reglas y listas de comprobación. No puede garantizar la creación automática de archivos, la persistencia entre turnos, la validación por CLI, la instalación del ZIP ni la detección de activadores.

### Comprobaciones de despliegue para completar obras inacabadas

Al entregar una obra abandonada, conserve los archivos habituales del proyecto de novela junto con `completion-brief.md`, `source-manifest.json`, los registros de pruebas/intención/versiones/ramas, `rights-and-publication.md`, `completion-provenance.md`, `completion-state.json` y el control de finalización. Las obras cuyos derechos sean desconocidos o no estén autorizados usan por defecto el modo `private-only`/`research`; no publique directamente su prosa.

No coloque el proyecto directamente dentro del ZIP de skills. Entregue una carpeta de proyecto separada o un ZIP limpio:

1. Compruebe primero si hay información sensible sobre personas reales, fuentes privadas, credenciales, texto de origen no autorizado o borradores que no deban compartirse.
2. Ejecute `snapshot_project.py`, `deep_consistency.py` y `chapter_gate.py` del sistema existente; incluya los resultados en la nota de entrega.
3. Identifique claramente el último capítulo canónico, los capítulos en borrador inacabados, la autoridad del autor para anular decisiones y los riesgos conocidos en `project-brief.md`.
4. Tras importar, el destinatario debe leer la biblia narrativa, el estado actual, la cronología, el registro del lector, los hilos argumentales, el registro de entidades y el resumen más reciente antes de continuar la historia.
