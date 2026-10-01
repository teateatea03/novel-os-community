# Configuración local e instalación portátil

<!-- language-navigation -->

[繁體中文](GETTING_STARTED.zh-TW.md) | [English](GETTING_STARTED.md) | [日本語](GETTING_STARTED.ja.md) | [한국어](GETTING_STARTED.ko.md) | **Español** | [Français](GETTING_STARTED.fr.md) | [Deutsch](GETTING_STARTED.de.md) | [Português](GETTING_STARTED.pt.md)

Esta guía trata el entorno de ejecución local y el paquete portátil. El uso y la redistribución se rigen por [LICENSE](../LICENSE.es.md); los detalles de declaración comercial y pago están en [COMMERCIAL_TERMS.es.md](COMMERCIAL_TERMS.es.md).

## Cobertura de idiomas

La documentación pública está disponible en chino tradicional, inglés, japonés, coreano, español, francés, alemán y portugués. Las habilidades de ejecución, las plantillas y sus referencias técnicas conservan actualmente su idioma original. Esta versión de documentación en ocho idiomas no traduce el entorno de ejecución.

## Elegir un modo

- **Herramientas locales:** Python 3.10+ y archivos UTF-8 persistentes. La validación principal, la creación de estructuras de proyecto y las pruebas utilizan la biblioteca estándar
- **Ejecución de agentes:** lo anterior más un anfitrión que cargue paquetes `SKILL.md` hermanos, lea/escriba archivos de proyecto y ejecute Python. Registre `novel-operating-system` como punto de entrada
- **Modo documental/manual:** un anfitrión sin shell ni archivos persistentes puede seguir las plantillas, pero no puede afirmar que se hayan ejecutado controles CLI, instalación ni estado duradero

Novel OS no incluye un modelo, una cuenta de API, un servicio web ni un manuscrito privado. Hay 18 directorios fuente de habilidades: 17 habilidades de ejecución instalables (un coordinador y 16 colaboradores) y el exportador.

## Comprobar una copia nueva

Ejecute estos comandos desde la raíz del repositorio en un shell POSIX:

```sh
python3 --version
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Utilice un directorio de proyecto privado separado para el trabajo real. No copie manuscritos ni bases de datos existentes en esta copia. Para un primer proyecto sintético, utilice el ejemplo `mktemp` del README raíz. Un `--root` explícito tiene prioridad sobre `NOVEL_PROJECTS_ROOT`; sin ninguno de ellos, los inicializadores usan `~/.novel-os/novels`.

## Construir y probar un paquete local

Estos comandos utilizan únicamente archivos del repositorio y directorios temporales. No implican cargas, modelos en vivo, claves de API ni investigación externa. La salida de construcción debe quedar fuera de la copia de fuentes para evitar incluir accidentalmente contenido generado en commits.

```sh
BUNDLE_WORK="$(mktemp -d)"
INSTALL_WORK="$(mktemp -d)"
EXPORTER="skills/novel-system-exporter/scripts"

python3 "$EXPORTER/build_novel_os_bundle.py" refresh \
  --source-root skills --bundle-root "$BUNDLE_WORK"
python3 "$EXPORTER/build_novel_os_bundle.py" verify \
  --bundle-root "$BUNDLE_WORK/payload"
python3 scripts/privacy_scan.py "$BUNDLE_WORK/payload"
python3 "$EXPORTER/verify_novel_os.py" --profile full \
  --bundle-root "$BUNDLE_WORK/payload" --output "$BUNDLE_WORK/verification.json"
python3 "$EXPORTER/install_novel_os.py" \
  --bundle-root "$BUNDLE_WORK/payload" --target "$INSTALL_WORK" --smoke-test
```

El perfil de verificación completo ejecuta un piloto sintético de narrativa extensa de más de 100 mil caracteres y baterías de regresión locales. Es una comprobación de corrección local, no una certificación de calidad de modelos en vivo ni de múltiples plataformas. El instalador se niega a sobrescribir habilidades existentes salvo que se proporcione `--upgrade` explícitamente; las actualizaciones crean copias de seguridad locales. No utilice un directorio de habilidades activo en su primera prueba.

Para crear un archivo después de superar las comprobaciones:

```sh
python3 "$EXPORTER/build_novel_os_bundle.py" build \
  --bundle-root "$BUNDLE_WORK/payload" \
  --output "$BUNDLE_WORK/novel-os-review.zip"
```

El manifiesto enumera y calcula hashes de todos los archivos empaquetados, incluidas las ocho versiones lingüísticas de la licencia del proyecto, las condiciones comerciales y la guía de terceros, además del aviso Humanizer-zh sin cambios dentro de su habilidad adaptada. Conserve esos avisos con el archivo y la instalación. El instalador guarda los avisos del proyecto en `novel-operating-system/DISTRIBUTION_NOTICES/` en vez de sobrescribir la licencia raíz del anfitrión.

## Funciones opcionales

Instale solo lo que necesite su anfitrión, en un entorno aislado:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

El archivo enumera intervalos de compatibilidad, no un bloqueo reproducible de versiones. Si habilita una integración opcional, elija/pruebe su versión exacta y revise sus condiciones originales. Ninguna dependencia opcional es necesaria para el recorrido principal anterior.

- NetworkX habilita algoritmos de grafos/GraphML opcionales; Graphify se instala por separado para sus exportadores adicionales
- PyYAML habilita entrada YAML de proyección NPC; MCP y su servidor externo de Instagram son integraciones opcionales
- La revisión independiente por modelo necesita un sustituto específico del anfitrión para `minis-model-use` fuera de su anfitrión original. Si no está disponible, registre que no se ejecutó
- `lieflat-less-ai-tone` no está incluido. Su fuente/licencia debe verificarse por separado; sin él, utilice el flujo integrado de voz humana y registre que no se ejecutó la pasada adicional

Véanse [THIRD_PARTY.es.md](../THIRD_PARTY.es.md), la [compatibilidad de plataformas](../skills/novel-system-exporter/references/platform-compatibility.es.md) y el [contrato del adaptador de anfitrión](../skills/novel-system-exporter/references/host-adapter-contract.es.md). Las pruebas de Windows/anfitrión nativo y servicios opcionales son tareas de aceptación separadas; una prueba básica en Linux no las verifica.
