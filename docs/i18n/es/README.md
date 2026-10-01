# Novel OS

<!-- language-navigation -->

[繁體中文](../zh-TW/README.md) | [English](../../../README.md) | [日本語](../ja/README.md) | [한국어](../ko/README.md) | **Español** | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md)

Novel OS es una colección reutilizable de habilidades para agentes de IA y herramientas locales de Python para narrativa extensa, ficción interactiva, continuidad, investigación de personajes y mundos, coherencia del comportamiento, grafos con información de procedencia y validación narrativa.

> **Licencia:** código fuente disponible bajo la [licencia de participación en beneficios comerciales de Novel OS](LICENSE.md), copyright teateatea03. El uso no comercial es gratuito; el uso comercial debe aportar el 0.5% del beneficio neto positivo anual relacionado. Las modificaciones y la redistribución conservan las mismas condiciones y avisos. No es MIT, GPL ni una licencia de código abierto de la OSI.

Para los detalles del uso comercial y del pago con dos tokens, consulte la [información de participación en beneficios y pagos](COMMERCIAL_TERMS.md). Los derechos sobre las novelas y otros resultados de los usuarios no se transfieren al propietario del sistema.

## Cobertura de idiomas

La documentación pública está disponible en chino tradicional, inglés, japonés, coreano, español, francés, alemán y portugués. Las habilidades de ejecución, las plantillas y sus referencias técnicas conservan actualmente su idioma original. Esta versión de documentación en ocho idiomas no traduce el entorno de ejecución.

## Límite de privacidad

Este repositorio de código fuente excluye deliberadamente:

- manuscritos, borradores de capítulos, sesiones de juego interactivo, estado narrativo y conjuntos de datos de comentarios del autor;
- bases de datos de investigación de personajes, mundos, objetos especiales y personas reales;
- memorias de chat, estado local de dispositivos, copias de seguridad, exportaciones, credenciales, puntos de acceso privados y archivos de entorno.

Los ejemplos públicos y los datos de prueba deben ser sintéticos. Antes de cada envío o publicación, ejecute el analizador de privacidad y revise el manifiesto de los archivos preparados.

## Estructura del repositorio

- `skills/`: paquetes de habilidades reutilizables, scripts, plantillas y datos de prueba sintéticos
- `scripts/`: utilidades de privacidad, validación y pruebas
- `docs/`: documentación de gobernanza del proyecto y límites de publicación

El árbol de fuentes tiene 18 directorios de habilidades: 17 habilidades de ejecución instalables (un coordinador y 16 colaboradores), más el exportador del paquete. El exportador es una herramienta de empaquetado y no se instala como habilidad de ejecución.

## Requisitos

- Python 3.10+
- Almacenamiento persistente UTF-8
- Las funciones principales solo necesitan la biblioteca estándar
- Funciones opcionales: véanse `requirements-optional.txt` y `THIRD_PARTY.es.md`

Instale las dependencias opcionales de Python en un entorno aislado:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

La integración con Graphify es opcional y se instala por separado según su documentación original.

## Primera ejecución local (sin modelo ni red)

Desde la raíz del repositorio, utilice Python 3.10+ y Git. Las comprobaciones principales y la demostración sintética no requieren paquetes opcionales, claves de API ni manuscritos privados:

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 scripts/run_tests.py

# Mantenga el estado de proyecto generado fuera del repositorio de fuentes.
DEMO_ROOT="$(mktemp -d)"
python3 skills/long-form-novel-writer/scripts/init_novel_project.py \
  --title "Synthetic Demo" --slug synthetic-demo --root "$DEMO_ROOT"
python3 skills/knowledge-relationship-graph/scripts/relationship_graph.py \
  validate --root "$DEMO_ROOT/synthetic-demo"
```

El inicializador crea una estructura vacía de planificación y estado; no genera una novela ni llama a un modelo. Guarde sus propias historias en otro directorio privado. El inicializador se niega a sobrescribir un proyecto existente.

Para un anfitrión de agentes, conserve las habilidades de ejecución como directorios hermanos y registre `novel-operating-system` como punto de entrada. Los anfitriones sin archivos persistentes ni ejecutor de procesos Python solo admiten el modo documental/manual. Consulte la [guía de compilación e instalación local probada](GETTING_STARTED.md) para los comandos del paquete, las pruebas básicas, las integraciones opcionales y los límites de las plataformas.

## Verificación

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

La batería Novel Judge debe ejecutarse mediante `scripts/run_tests.py`; no se admite invocar uno a uno sus archivos de prueba relativos al paquete.

Las comprobaciones de privacidad y JSON inspeccionan los archivos fuente, incluidos los no rastreados y los ignorados por Git. Excluyen los metadatos de Git, las cachés generadas de Python/pruebas y los entornos virtuales confirmados en la raíz; los archivos rastreados se siguen comprobando. Los enlaces simbólicos, los archivos ilegibles y el texto que no sea UTF-8 provocan el rechazo seguro. Mantenga los paquetes generados y el estado narrativo fuera de esta copia de trabajo. El analizador informa de nombres de archivo y categorías de hallazgos, nunca del contenido coincidente; es una comprobación heurística, no una prueba de privacidad ni un análisis del historial.

## Rutas de plataforma

La documentación utiliza marcadores como `<SKILLS_ROOT>`, `<WORKSPACE_ROOT>` y `<NOVEL_PROJECTS_ROOT>`. Configúrelos para la plataforma anfitriona. Los inicializadores ejecutables utilizan por defecto `~/.novel-os/novels`, salvo que se proporcione `NOVEL_PROJECTS_ROOT` o un `--root` explícito.

## Seguridad y ámbito de investigación

Las habilidades de investigación están diseñadas para material legal y públicamente accesible; no deben eludir barreras de inicio de sesión, CAPTCHA, muros de pago, controles de robots/acceso ni restricciones de plataforma. La investigación de personas reales exige procedencia de las fuentes y no debe convertir material no verificado o sensible en afirmaciones fácticas.

## Gobernanza

Lea:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [THIRD_PARTY.md](THIRD_PARTY.md)

## Licencia y contribuciones

Lea [LICENSE](LICENSE.md) y los [detalles de pago comercial](COMMERCIAL_TERMS.md) antes del uso comercial. Solo se incluye el beneficio neto anual positivo de productos, servicios y novelas relacionados; se excluyen las actividades no relacionadas. La declaración la realiza el usuario, sin telemetría oculta ni cobro automático. Los componentes de terceros conservan sus propias licencias y avisos.

Los usuarios comerciales aceptan expresamente la versión de licencia antes del uso. Empiece con una incidencia de GitHub sin datos privados ni financieros para acordar un canal privado de declaración; no publique estados financieros ni registros de pagos. Las reglas de contribución y redistribución figuran en [CONTRIBUTING.md](CONTRIBUTING.md).

## Límites de verificación

Se proporcionan pruebas principales en Linux y comprobaciones de instalación sintéticas. No se certifican los servicios opcionales Graphify/MCP/Instagram, los modelos en vivo, las integraciones de agentes nativos ni una matriz de plataformas/versiones de Python. Los informes de modelos de ejemplo son ilustraciones sintéticas, no pruebas de rendimiento medido de proveedores o modelos.
