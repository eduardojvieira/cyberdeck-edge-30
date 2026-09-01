# Reglas del repositorio

## Alcance

Este proyecto porta Droidian con Plasma Mobile 6 al Motorola Edge 30 Ultra (`eqs`). Plasma Mobile 6 es la interfaz objetivo; compositor, paquetes y detalles de integración se deciden con evidencia del port. No introducir otra interfaz o compositor sin aprobación explícita.

## Forma de trabajo

- No usar SDD salvo que Eduardo lo pida explícitamente.
- Hacer el cambio incremental más chico que produzca evidencia útil.
- Preferir fuentes oficiales y upstream; registrar commit, versión y origen de firmware cuando se usen.
- No crear repositorios, capas, scripts o abstracciones antes de necesitarlos.
- Mantener `README.md` y su checklist alineados con el estado real.

## Hardware y seguridad

- Separar siempre evidencia de host/simulador de evidencia en dispositivo o HIL.
- No afirmar que algo arranca, carga, suspende, enfría, recupera o funciona por USB sin haberlo probado físicamente.
- Preparar recuperación antes de cualquier flash.
- No flashear, desbloquear, relockear, depurar contra el teléfono ni actuar sobre hardware sin autorización explícita de Eduardo.
- Nunca flashear a través de un hub USB-C.
- No guardar secretos, claves, tokens ni datos personales en el repositorio o imágenes de desarrollo.
