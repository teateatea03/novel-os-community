# Contribuir a Novel OS

<!-- language-navigation --> [繁體中文](CONTRIBUTING.zh-TW.md) | [English](CONTRIBUTING.md) | [日本語](CONTRIBUTING.ja.md) | [한국어](CONTRIBUTING.ko.md) | **Español** | [Français](CONTRIBUTING.fr.md) | [Deutsch](CONTRIBUTING.de.md) | [Português](CONTRIBUTING.pt.md)

[Plantilla de solicitud de cambios](.github/PULL_REQUEST_TEMPLATE/es.md)

Gracias por ayudar a mejorar Novel OS. Las contribuciones deben preservar las condiciones comerciales de código fuente disponible del proyecto y el límite de privacidad.

## La privacidad y los derechos bloquean la publicación

Contribuya únicamente con material reutilizable del sistema que tenga derecho a compartir. **No** envíe:

- manuscritos, borradores de capítulos, sesiones interactivas, estado narrativo, comentarios del autor ni datos de prueba de proyectos privados;
- bases de datos de personajes, mundos o investigación ni registros sobre personas reales;
- memorias de chat, registros locales, copias de seguridad generadas, credenciales, cookies, rutas de dispositivos ni puntos de acceso privados;
- textos originales protegidos por derechos de autor, material filtrado, copias tras muros de pago ni código de terceros sin licencias compatibles y atribución.

Use datos de prueba ficticios, mínimos y claramente sintéticos. No se limite a cambiar los nombres de datos privados reales.

Construya los paquetes y cree los proyectos narrativos fuera de la copia de fuentes. Se permite un entorno virtual en la raíz para desarrollo local, pero no debe incorporarse a los commits.

## Antes de abrir una solicitud de cambios

```sh
python3 scripts/privacy_scan.py .
python3 -m compileall -q skills scripts
python3 scripts/validate_json.py .
python3 scripts/run_tests.py
```

El analizador y el validador JSON revisan los archivos del árbol de trabajo, incluidos los no rastreados y los ignorados por Git. Excluyen metadatos de Git, cachés generadas de Python/pruebas y entornos virtuales confirmados en la raíz; los archivos rastreados siguen incluidos. Rechazan enlaces simbólicos, archivos ilegibles y fuentes que no sean UTF-8. Revise por separado las diferencias preparadas: superar una comprobación del árbol de trabajo no equivale a analizar el índice preparado, el historial de Git ni los objetos retenidos por GitHub.

Inspeccione también:

```sh
git diff --cached --name-only
git diff --cached
```

Explique en la solicitud de cambios cualquier dependencia nueva, fuente externa, artefacto generado o comportamiento específico de plataforma.

## Expectativas de los cambios

- Mantenga portables el código y la documentación; los valores predeterminados de plataforma deben poder sustituirse
- Añada o actualice pruebas para los cambios de comportamiento
- Preserve la autoridad del canon y del autor y los contratos de seguridad que rechazan ante incertidumbre
- Mantenga los ejemplos públicos sintéticos y sin información de identificación personal
- No debilite silenciosamente los controles de privacidad, procedencia o validación

## Modelo de commits y revisión

Use commits centrados en un objetivo con un resumen en imperativo. Las solicitudes de cambios requieren revisión del responsable. Las correcciones de seguridad o privacidad deben comunicarse de forma privada y no mediante una incidencia pública.

## Licencias

Contribuya solo con material que tenga derecho a distribuir bajo [LICENSE](LICENSE.es.md). Identifique las modificaciones, conserve la misma licencia para los cambios derivados del proyecto y preserve todos los avisos de terceros exigidos. Esto no transfiere sus derechos de autor al responsable. Las solicitudes de cambios públicas no deben incluir informes financieros, datos de pago ni material creativo privado.
