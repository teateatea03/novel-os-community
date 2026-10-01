# Política de seguridad y privacidad

<!-- language-navigation --> [繁體中文](SECURITY.zh-TW.md) | [English](SECURITY.md) | [日本語](SECURITY.ja.md) | [한국어](SECURITY.ko.md) | **Español** | [Français](SECURITY.fr.md) | [Deutsch](SECURITY.de.md) | [Português](SECURITY.pt.md)

## Versiones compatibles

Las correcciones de seguridad y privacidad se dirigen a la rama `main` actual.

## Comunicación de problemas

No abra incidencias públicas que contengan datos personales, credenciales, manuscritos privados, registros de sesiones, material narrativo inédito ni registros de investigación. Use la comunicación privada de vulnerabilidades cuando esté habilitada. Si no hay un contacto privado disponible, abra una incidencia solicitando al responsable un canal privado, sin incluir detalles sensibles.

## Límite de las contribuciones

Los colaboradores deben enviar únicamente material que tengan derecho a compartir. Nunca incorpore a los commits:

- claves de API, contraseñas, tokens, claves SSH, cookies, archivos de entorno ni rutas de dispositivos;
- conversaciones privadas, memorias de agentes, registros, copias de seguridad ni exportaciones;
- ficción inédita, estado de sesiones interactivas ni datos de investigación personal;
- datos sobre personas reales que no sean adecuados para redistribución pública.

## Antes de publicar un cambio

1. Revise `git diff --cached --name-only`.
2. Ejecute `python3 scripts/privacy_scan.py .`.
3. Inspeccione cada hallazgo manualmente; no suprima un hallazgo sin una justificación escrita.
4. Confirme que cada archivo incluido pertenece al sistema reutilizable, no a un proyecto activo ni a un conjunto de datos privado.

## Proceso de divulgación

Si se incorpora o expone material privado, detenga su distribución, haga privado el repositorio si es necesario, revoque las credenciales afectadas, preserve las pruebas para revisión y elimine el material de los objetos Git actuales e históricos antes de reabrir el acceso.
