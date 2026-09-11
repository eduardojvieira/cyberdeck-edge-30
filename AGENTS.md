# Reglas del repositorio

## Alcance

Este proyecto porta Droidian con Plasma Mobile 6 al Motorola Edge 30 Ultra (`eqs`). Plasma Mobile 6 es la interfaz objetivo; compositor, paquetes y detalles de integración se deciden con evidencia del port. No introducir otra interfaz o compositor sin aprobación explícita.

## Forma de trabajo

- No usar SDD salvo que Eduardo lo pida explícitamente.
- Hacer el cambio incremental más chico que produzca evidencia útil.
- Preferir fuentes oficiales y upstream; registrar commit, versión y origen de firmware cuando se usen.
- No crear repositorios, capas, scripts o abstracciones antes de necesitarlos.
- Mantener `README.md` y su checklist alineados con el estado real.
- `README.md` es la portada de referencia en inglés; `README.es.md` y
  `README.pt-BR.md` son traducciones. Mantener selector, comandos, versiones,
  advertencias y estado de validación sincronizados; no traducir rutas ni flags.
- Eduardo autorizó publicar el repositorio el 11 de septiembre de 2026.
  La publicación cubre código y documentación, no `.work/`, firmware ni datos privados.

## Hardware y seguridad

- Separar siempre evidencia de host/simulador de evidencia en dispositivo o HIL.
- No afirmar que algo arranca, carga, suspende, enfría, recupera o funciona por USB sin haberlo probado físicamente.
- Preparar recuperación antes de cualquier flash.
- No flashear, desbloquear, relockear, depurar contra el teléfono ni actuar sobre hardware sin autorización explícita de Eduardo.
- Nunca flashear a través de un hub USB-C.
- No guardar secretos, claves, tokens ni datos personales en el repositorio o imágenes de desarrollo.

## Imagen y estado consolidado (11 de septiembre de 2026)

- Estado actual y pendientes: `README.md` y `docs/RELEASE-20260910.md`; las
  notas H2–H29 describen evidencia fechada, no el siguiente ensayo obligatorio.
- Imagen actual: `port/build-eqs-rootfs.sh --consolidated NUEVA_RUTA stock|replacement`.
  No usar el builder/flasher histórico para reproducir el teléfono actual.
- La receta fija Plasma `+eqs5`; el ZIP del 10 de septiembre conserva `+eqs4`.
  No confundir la receta actual con una imagen nueva construida/validada.
  Waydroid, paquetes de idioma y herramientas personales están sólo en el teléfono.
- Preservar H29 como input binario fijado; no declarar equivalente un kernel
  recompilado con otro perfil aunque conserve el mismo `uname -r`.
- La calibración 2× pertenece al repuesto táctil de Eduardo; exige perfil
  `replacement`, nunca aplicarla universalmente a todos los Goodix/eqs.
- Nunca exportar la raíz viva, `/home`, credenciales o backups a una imagen.
  Código a Git; binarios, firmware y evidencia privada bajo `.work/`.
- `test-wallpaper-sync.py` y `port/waydroid/check-prepare.py` son nativos del Edge;
  no ejecutar todos los tests indiscriminadamente sobre la PC.
