# Primer flash y recuperación de `eqs`

## Estado del artefacto

El ZIP `eqs-dev` anterior se construyó e inspeccionó en host y se flasheó físicamente en A/B. Entró en bootloop antes de que apareciera USB gadget/telnet, por lo que no demuestra arranque Droidian, pantalla, touch, red, carga ni USB. La unidad permanece recuperable desde Fastboot; no es una imagen diaria cifrada.

### Estado posterior comprobado: 4 de septiembre de 2026

- La rootfs Droidian está en `userdata`/LVM y se montó desde recovery. **No hacer wipe, factory reset ni volver a ejecutar el flasher completo para diagnosticar el arranque.**
- El último estado registrado es slot A, `boot_a` stock `-16` y recovery diagnóstica v14 con ADB root. Confirmar el estado al retomar: no se consultó el teléfono durante la revisión documental.
- Recovery v14: `.work/diagnostic-recovery-shell/v14/recovery.img`, SHA-256 `008573eba4ef41699835b39cd2a16c4b3ba066830bf9efb7c55d3a034e40a49e`. Tiene SELinux permisivo y ADB sin autenticación: sólo desarrollo, cable directo y sin secretos; no distribuir como imagen diaria.
- La imagen v14 usa cabecera de formato v4 y no contiene kernel (`kernel_size=0`): depende del kernel de `boot_a`. Si un candidato rompe también recovery, no asumir que basta reflashear su ramdisk. Conservar el conjunto stock compatible; la [arquitectura de boot de Android](https://source.android.com/docs/core/architecture/partitions/generic-boot) explica la composición de estos componentes.
- Slot B tiene un sistema/verificación incoherente y **no es un rollback validado**. Ambos slots comparten `userdata`; restaurar `boot_a` para usar recovery no restaura Android completo.
- Antes de otro reinicio, comprobar el montaje de pstore y copiar los registros. Las capturas anteriores no permiten afirmar que no existieran logs persistentes.

Ver el [análisis y plan vigente](BRINGUP-PLAN.md). Los pasos genéricos de primer flash no son instrucciones para continuar desde este estado.

## Gate NO-GO

**No ejecutar los `flash_all.sh` existentes.** Además de las precondiciones y autorización expresa, debe corregirse y validarse la instalación: la receta versionada usa Fastboot y la variante local experimental usa telnet, mientras la rootfs se cargó físicamente por FastbootD. El bootloader está abierto y debe permanecer abierto: **nunca relockear** con una imagen modificada.

No usar hub USB-C para fastboot, Rescue ni el primer flash. Usar un cable directo conocido entre el teléfono y el host.

## Inventario privado previo

Guardar fuera del repositorio y sin IMEI/serial en archivos versionados:

- variante exacta (`XT2241-1` o `XT2241-2`), canal y región;
- build y fingerprint Android stock exactos;
- slot activo y estado conocido de ambos slots A/B;
- firmware stock recuperable para esa combinación, sus hashes y las imágenes disponibles;
- copia de los datos que se quieran conservar.

La compatibilidad del firmware y de la herramienta de Motorola debe confirmarse sobre la unidad física. No se asume intercambiabilidad entre regiones, variantes ni slots.

La base de fuentes congelada es Android 14 `U1SQS34.52-21-1-10`, mientras la referencia Lineage inspeccionada usa `-15`. La unidad física es `XT2241-2` RETAR y su Android 14 `U1SQS34.52-21-1-16` fue restaurado y arrancó físicamente mediante todos los pasos firmados de `flashfile.xml`; no fue el helper local reducido. `-16` queda aceptado sólo como base experimental de bring-up: no prueba compatibilidad Halium/Droidian.

## Preparación de recuperación

1. Tener `fastboot` conocido y comprobado en el host.
2. Instalar [Motorola Software Fix](https://en-us.support.motorola.com/app/softwarefix/) y probar sólo que reconoce la unidad; no iniciar Rescue durante esa comprobación.
3. Confirmar que la recuperación oficial identifica la unidad y ofrece el firmware correcto. Software Fix/Rescue es para Windows y su proceso borra datos; ver sus [requisitos y descarga](https://en-us.support.motorola.com/app/answers/detail/a_id/158726/) y su [guía destructiva](https://en-us.support.motorola.com/app/answers/detail/a_id/167770/).
4. Conservar una imagen Droidian anterior conocida, si existe, junto con su SHA-256, para rollback rápido.

Motorola advierte que desbloquear el bootloader reduce las protecciones del arranque; mantenerlo abierto es necesario para imágenes modificadas. Véase el [aviso legal de bootloader](https://en-us.support.motorola.com/euf/assets/docs/Bootloader-Legal_Agreement_and_Warning.pdf).

## Próxima instalación completa: pendiente de validar

1. Extraer el ZIP en el host y verificar su SHA-256 contra `SHA256SUMS`/el manifiesto entregado; desde la raíz del repositorio, el manifiesto generado se comprueba con `sha256sum -c .work/eqs-rootfs/SHA256SUMS`.
2. Conectar el teléfono directamente, sin hub, y entrar en fastboot.
3. Revisar el procedimiento corregido contra la combinación ensayada y preparar recuperación antes de ejecutarlo con autorización específica. No usar el script actual ni extrapolar una secuencia genérica de particiones.

El flasher de la receta versionada comprueba el producto `eqs`, escribe imágenes de arranque en **A y B** y reemplaza `userdata` por Fastboot. La variante local no publicada borra `userdata` y espera transferir la rootfs por telnet. Ninguna debe ejecutarse sobre el estado actual: destruiría la rootfs que queremos conservar y no reproduce el procedimiento FastbootD ensayado.

## Rollback

Ante un fallo, priorizar en este orden:

1. fastboot con una imagen Droidian anterior conocida y verificada para la misma unidad;
2. Software Fix/Rescue oficial, sólo después de confirmar que reconoce la unidad y el firmware aplicable.

No se proporciona aquí una secuencia genérica de comandos stock por partición, EDL ni test points. La restauración ensayada corresponde únicamente a esta unidad y al firmware exacto indicado abajo; no extrapolarla a otras revisiones, regiones o estados de slots.

## Recuperación stock Android 14 desde Linux: aprendizaje previo

En el workspace existe el helper experimental `tools/flash-stock-a14-eqs-experimental.sh`, **no incluido en este commit**. Sólo valida el paquete exacto `XT2241-2_EQS_RETAR_14_U1SQS34.52-21-1-16` y opcionalmente lee el estado de Fastboot. Su ejecución de flash está deshabilitada: el intento reducido AP-only produjo bootloop y fue eliminado. No hay un auto-flasher stock completo publicado en este repositorio.

La restauración exacta Android 14 `-16` fue validada en esta unidad: después de un bootloop de bring-up arrancó stock correctamente con la ejecución manual completa de `flashfile.xml` firmado. El helper local es ahora **read-only**; no sustituye esa secuencia ni hay un paquete Android 15 RETAR de recuperación guardado localmente. Motorola Rescue no está disponible en Linux. Cualquier flash futuro sigue requiriendo backup, revisión separada y autorización explícita.
