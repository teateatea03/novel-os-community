# Contrato del paquete portátil de Novel OS

<!-- language-navigation -->

[繁體中文](bundle-contract.md) | [English](bundle-contract.en.md) | [日本語](bundle-contract.ja.md) | [한국어](bundle-contract.ko.md) | **Español** | [Français](bundle-contract.fr.md) | [Deutsch](bundle-contract.de.md) | [Português](bundle-contract.pt.md)

En la estructura del paquete `novel-os-portable-v<version>/`, `skills/` contiene un coordinador y 16 skills especializadas. `public-web-research/` proporciona adquisición segura y reanudable de HTTP(S) público y preparación de candidatos para Evidence Run. `novel-model-capability-compatibility/` mantiene los contratos de pruebas de capacidad del modelo/L0–L5/alternativas. `novel-reality-state-engine/` mantiene las herramientas de validación evento → estado → capacidad → comportamiento → prosa. `novel-world-database-builder/` mantiene esquemas de bases de datos de mundos, plantillas de lotes, paquetes de entrega y especificaciones de consulta. `special-object-database-builder/` mantiene esquemas de versiones, capacidades, especificaciones y ciclos de vida de objetos/armaduras/mecas/dispositivos.

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
│   ├── novel-operating-system/      # punto de entrada único obligatorio
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

`MANIFEST.json` contiene: esquema/versión del paquete, lista de paquetes, versiones de las skills de origen, un resumen SHA-256 y un número de bytes para cada archivo del contenido, un inventario separado `distribution_notices`, fecha de creación, exclusiones y declaraciones de dependencias de ejecución. El contenido también incluye una copia portátil de la **guía de compatibilidad de plataformas**. No contiene secretos, rutas absolutas locales, proyectos narrativos, configuraciones de cuentas ni bases de datos de mundos.

## Conservación de licencias y avisos

- `--source-root` identifica el directorio de origen `skills/`. Su repositorio padre debe contener los 24 documentos de proyecto para ocho idiomas: `LICENSE`, `LICENSE.zh-TW.md`, `LICENSE.ja.md`, `LICENSE.ko.md`, `LICENSE.es.md`, `LICENSE.fr.md`, `LICENSE.de.md`, `LICENSE.pt.md`; `THIRD_PARTY.md`, `THIRD_PARTY.zh-TW.md`, `THIRD_PARTY.ja.md`, `THIRD_PARTY.ko.md`, `THIRD_PARTY.es.md`, `THIRD_PARTY.fr.md`, `THIRD_PARTY.de.md`, `THIRD_PARTY.pt.md`; y `docs/COMMERCIAL_TERMS.md`, `docs/COMMERCIAL_TERMS.zh-TW.md`, `docs/COMMERCIAL_TERMS.ja.md`, `docs/COMMERCIAL_TERMS.ko.md`, `docs/COMMERCIAL_TERMS.es.md`, `docs/COMMERCIAL_TERMS.fr.md`, `docs/COMMERCIAL_TERMS.de.md`, `docs/COMMERCIAL_TERMS.pt.md`. La actualización del contenido rechaza cualquier documento obligatorio ausente, que no sea un archivo o que sea un enlace simbólico antes de modificar el contenido. Son condiciones del proyecto elegidas por su propietario; los avisos de los proyectos originales conservan su propio alcance.
- La lista explícita adicional de archivos permitidos es `LICENSE.md`, `LICENSE.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt` y `docs/COMMERCIAL_LICENSE.md`. Si existen, se copian byte por byte. No se exportan otros archivos raíz de `docs/`. En particular, `docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md` es un borrador de discusión sin efecto y no se exporta como licencia ni como condiciones comerciales.
- Los archivos locales de cada skill `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, `COPYING.md`, `COPYING.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt`, `THIRD_PARTY.md` y todos los archivos dentro de `THIRD_PARTY_LICENSES/` se conservan con la skill y se declaran en `distribution_notices`. La actualización comprueba sus bytes frente al origen; la construcción y la instalación rechazan declaraciones ausentes, archivos faltantes, bytes alterados, rutas inseguras o entradas de resumen ausentes.
- El material adaptado existente de Humanizer-zh exige específicamente `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`. No se puede eliminar del origen ni del manifiesto mientras se distribuya ese material.
- Los nuevos nombres de archivo legalmente obligatorios deben añadirse a este contrato explícito antes de publicar una versión. No dependa de un enlace a un documento que no esté incluido. La actualización elimina del contenido existente las copias obsoletas de avisos raíz opcionales.
- El ZIP conserva la misma estructura relativa a la raíz. La instalación guarda todos los documentos de avisos en `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`, conservando rutas como `docs/COMMERCIAL_TERMS.md` y `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`, para que los enlaces relativos de licencia sigan funcionando. Los avisos de los proyectos originales locales a las skills también permanecen en sus directorios originales. El instalador nunca escribe en `<target>/LICENSE`, `<target>/THIRD_PARTY.md` ni `<target>/docs/`.
- `novel-operating-system/INSTALLATION.json` registra la ruta original, la ruta instalada, la ruta de la copia documental, el SHA-256 y el número de bytes de cada aviso instalado. La preparación y la instalación final verifican ambas copias cuando corresponde. La actualización lleva el coordinador anterior y sus avisos a la copia de seguridad habitual de skills y los restaura si la instalación falla. `DISTRIBUTION_NOTICES/` dentro del coordinador está reservado para los documentos gestionados por el instalador.
- Para volver a comprobar una instalación, ejecute `python3 scripts/install_novel_os.py --target <SKILLS_ROOT> --verify-installed-notices` desde el paquete extraído. Este modo de solo lectura comprueba los archivos de avisos raíz y de los proyectos originales frente al registro de instalación. Los resúmenes establecen integridad local, no autenticidad frente a un atacante que pueda sustituir tanto los archivos como los registros; conserve por separado una versión de confianza.

## Declaración de dependencias de ejecución

Cada versión debe incluir las 32 referencias de portabilidad permitidas explícitamente: las cuatro guías `portable-install`, `platform-compatibility`, `host-adapter-contract` y `bundle-contract` dentro de `references/`, cada una en ocho idiomas. El chino tradicional usa el nombre original sin sufijo (`.md`); el inglés usa `.en.md`; japonés, coreano, español, francés, alemán y portugués usan `.ja.md`, `.ko.md`, `.es.md`, `.fr.md`, `.de.md` y `.pt.md`. Declare estos niveles con veracidad:

- **Flujo documental básico**: un LLM que pueda leer los archivos Skill; no requiere ejecutar código.
- **Flujo local automatizado (v2.7)**: Python 3.10+ (se recomienda 3.11+), un shell/ejecutor de procesos, archivos UTF-8 persistentes, descubrimiento de múltiples skills o un enrutador equivalente, un bloqueo de rama, una autoridad de producción única `ProjectRuntimeAdapter.commit()`, siete controles, eventos semánticos tipados, preparación del proyecto/vigencia de las proyecciones, Quality Eval de comentarios del autor y capacidad de extracción si se distribuye como ZIP. Las bases de datos de mundos requieren además `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT` con permiso de escritura; las de objetos especiales requieren además `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` con permiso de escritura.
- **Mejoras de grafos**: `networkx` para recorrer grafos; `graphifyy` más `networkx` para exportaciones HTML/comunidades/Cypher de Graphify. El JSON del grafo sigue siendo utilizable sin ninguno de esos paquetes.
- **Integraciones opcionales**: Git para commits, herramientas web/navegador para investigar fuentes y un adaptador de segundo modelo/subagente específico del host para la revisión independiente. `independent_review.py` es específico de Minis hasta que se sustituya.

El funcionamiento local básico no requiere Node.js, un servidor de bases de datos, una clave API ni conexión a internet. Un framework sin acceso a archivos/procesos debe describirse como modo documental/manual, no como instalación automática completa.

## Política de construcción

- El contenido debe incluir **17** directorios de skills permitidos (un coordinador + 16 skills especializadas), referencias de portabilidad, scripts de instalación/construcción y archivos ordinarios de texto/código/fixtures/plantillas.
- Excluya `.git`, `.DS_Store`, `__pycache__`, `*.pyc`, `.env*`, `node_modules`, `dist`, `build`, todos los proyectos de novelas, bases de datos, archivos comprimidos y archivos específicos del sistema.
- Rechace enlaces simbólicos en la ruta de las skills de origen o en cualquier skill empaquetada antes de modificar el contenido; nunca siga un enlace de skill hacia archivos ajenos del host. Los documentos existentes no autorizados del contenido también deben hacer fallar la actualización en vez de entrar silenciosamente en un manifiesto nuevo.
- Conserve los bits de ejecución de `scripts/*.py` cuando estén presentes en el origen.
- Lea únicamente el árbol local de skills de origen y la lista explícita de avisos permitidos a nivel de repositorio. La construcción es determinista salvo por `built_at`.
- El paquete es autocontenido: los auxiliares de ejecución utilizan la biblioteca estándar de Python y descubren las dependencias en relación con su ubicación instalada.

## Política de verificación

`verify` debe rechazar archivos del contenido ausentes, alterados, inesperados o con hashes distintos; después, debe compilar todos los archivos Python. La prueba básica del instalador debe, además:

1. inicializar un proyecto de novela temporal bajo autoridad de producción activa;
2. verificar que la modificación canónica directa mediante FileStore está bloqueada;
3. ejecutar la suite completa de Novel Judge, incluida la autoridad de los controles, preparación, ejecutor de comandos, Quality Eval v2, eventos semánticos tipados y producción tradicional de narrativa larga;
4. ejecutar el validador de grafos y las regresiones de narrativa larga/Reality/capacidades;
5. verificar el conjunto de skills incluido y su divergencia respecto al conjunto de origen; y
6. para una versión completa, ejecutar la prueba de contrato aislada con un segundo proyecto y el piloto de narrativa larga tradicional de 100k+/inversión de conocimiento/cascada.

Una plataforma que no pueda ejecutar Python solo admite el nivel de flujo de trabajo/documentación; señale esa limitación en la entrega.
