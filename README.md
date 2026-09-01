# Droidian + Plasma Mobile 6 para Motorola Edge 30 Ultra

Port incremental de Droidian con Plasma Mobile 6 para el Motorola Edge 30 Ultra (`eqs`, XT2241-1/XT2241-2), pensado para usar la pantalla interna como una computadora Linux portátil.

## Estado actual

Planificación inicial. No hay imagen, compilación ni prueba sobre el teléfono todavía.

## Base técnica

- Dispositivo: Motorola Edge 30 Ultra `eqs`.
- Arquitectura: arm64.
- Sistema objetivo: Droidian con Plasma Mobile 6.
- Adaptación esperada: Halium API32 sobre el firmware Android 14 exacto de la unidad y región.
- Pantalla: interna; no se trabaja en monitores externos por ahora.
- USB-C: carga y periféricos cuando la adaptación y el hardware lo demuestren.

Wayfire, wlroots-HWC, libhybris y los paquetes concretos son la ruta actual esperada en Droidian, pero son detalles a validar durante el port, no un contrato fijo del proyecto.

## Primer hito útil

Una primera imagen es útil cuando cumple:

- [ ] Droidian arranca en `eqs`.
- [ ] Plasma Mobile 6 inicia en la pantalla interna.
- [ ] Funcionan pantalla y touch.
- [ ] Funciona Wi-Fi.
- [ ] Hay terminal y SSH saliente.
- [ ] Funciona un teclado USB.
- [ ] El equipo reinicia y se recupera sin reflashear todo.

## Después, de a poco

1. Touchpad y mouse.
2. Ethernet, SD y almacenamiento USB.
3. Carga mientras se usan periféricos.
4. Suspensión, teclado virtual, escala y atajos.
5. Cifrado e imagen diaria sin herramientas de depuración.
6. Carcasa y montaje definitivo.

## No ahora

No forman parte del bring-up inicial: monitor externo, Motorola Ready For, telefonía, cámara, NFC, huella, Waydroid, aplicaciones Android, otros entornos gráficos o una carcasa definitiva.

## Límites de seguridad y recuperación

- Registrar el modelo, región y firmware Android 14 exactos antes de modificar el teléfono.
- Preparar recuperación y conservar hashes de los artefactos antes de desbloquear o flashear.
- No flashear, desbloquear, relockear ni probar hardware sin autorización explícita.
- Nunca flashear a través de un hub USB-C.
- No guardar claves, tokens ni datos personales en el repositorio o en imágenes de desarrollo.
- Una afirmación sobre arranque, carga, USB, térmica, suspensión o recuperación requiere evidencia física en el dispositivo.

## Próximos pasos

1. Inventariar la unidad y su firmware stock.
2. Preparar recuperación mediante cable directo y fastboot.
3. Probar en Android stock el hub, carga y periféricos que se quieran usar.
4. Recién entonces congelar fuentes y arrancar el bring-up mínimo.

## Referencias upstream

- [Droidian](https://github.com/droidian-images/droidian)
- [Plasma Mobile Wayfire de Droidian](https://github.com/droidian/plasma-mobile-wf)
- [LineageOS: device tree de eqs](https://github.com/LineageOS/android_device_motorola_eqs)
- [LineageOS: SM8475 common](https://github.com/LineageOS/android_device_motorola_sm8475-common)
- [LineageOS: kernel SM8475](https://github.com/LineageOS/android_kernel_motorola_sm8475)
