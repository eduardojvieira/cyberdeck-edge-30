# Candidato eqs-halium2: arranque Droidian sobre la rootfs Plasma existente

**Nota de actualización:** este documento describe el bundle histórico Halium2, no la última prueba nativa. El script fuente actual incorpora preflight Motorola y selección/reintentos A, probados con Halium10; eso no actualiza el ZIP antiguo. [Estado vigente](../../docs/BRINGUP-PLAN.md#slots-ab-y-retorno-automático--5-de-septiembre).

**Candidato experimental para el Edge 30 Ultra XT2241-2 RETAR de este proyecto, con Android 14 base `U1SQS34.52-21-1-16`, bootloader abierto y slot A.** No es una instalación completa ni una imagen daily: reutiliza la rootfs Droidian/Plasma que ya está en UFS/LVM. No incluye ni escribe `userdata`.

El kernel, módulos, imágenes de arranque y paquetes se construyeron y verificaron en host. **Este candidato todavía no arrancó físicamente: no está demostrado que aparezca Plasma ni que funcione USB.** La prueba de hardware es el siguiente paso, no algo que la compilación pueda garantizar.

## Contenido

- `candidate/`: `boot.img`, `vendor_boot.img`, `dtbo.img`, `vbmeta.img` coherentes para eqs.
- `packages/`: paquetes del kernel dev2; no instalarlos automáticamente ni ejecutar `flash_all.sh`.
- `rescue/`: boot/vendor_boot/DTBO stock Android 14 -16, vbmeta con verificación desactivada y recovery diagnóstica v14.
- `SOURCE/`: scripts y perfil usados para este candidato; `BUILD-INFO.txt` identifica fuentes y toolchain.
- `SHA256SUMS`: integridad de todos los archivos del paquete.

La recovery v14 y el kernel stock funcionaron previamente. **El procedimiento combinado de rescate incluido todavía no fue ensayado como conjunto**; no se presenta como una restauración completa de Android. Slot B no es un respaldo. La base completa stock se conserva aparte en el workspace.

## Comprobación sin teléfono

Desde la carpeta extraída:

```bash
bash flash-candidate.sh --check
```

Debe terminar con `Bundle integrity OK`. No consulta ningún dispositivo.

## Flashear cuando estés listo para el ensayo

Cable directo conocido, sin hub. Cargá el teléfono antes del ensayo. No hagas factory reset ni wipe. Si la rootfs fue borrada o reemplazada, **este paquete no sirve para instalarla**.

1. Con el teléfono en **AP Fastboot**, identificar su serial con `fastboot devices`. El script exige un serial explícito; nunca elige el primer equipo conectado.
2. Si todavía hay logs de un fallo anterior disponibles en recovery, conservarlos antes del ensayo. No reiniciar repetidamente sólo para buscar USB.
3. Ejecutar, reemplazando `SERIAL` por el del teléfono:

```bash
bash flash-candidate.sh --flash-a SERIAL
```

El script fuente actualizado comprueba producto `eqs`, slot A, `securestate=flashing_unlocked`, AP Fastboot y bootloader -16 exacto antes de escribir. Escribe **solamente** `vbmeta_a`, `dtbo_a`, `vendor_boot_a` y `boot_a`; después selecciona A, restablece sus intentos y verifica el resultado. Se detiene ante el primer error y no reinicia automáticamente. No escribe particiones B, recovery, super, modem ni userdata.

4. Sólo después de que todas las escrituras terminen correctamente:

```bash
fastboot -s SERIAL reboot
```

No saltear los controles si alguno falla. No instalar el ZIP antiguo ni cambiar a slot B para intentar resolverlo.

## Qué observar

El candidato mantiene Plasma Mobile/Wayfire de la rootfs instalada. Se añadió consola Linux y registro systemd a kmsg. No se incluyó otra interfaz.

Las marcas de initramfs contienen `EQS CANDIDATE=eqs-halium2-38e35affce93` y etapas `MOUNTROOT`, `MODULES`, `UDEV`, `UFS`, `VENDOR`, `LVM`, `ROOT`, `BOOTMODE`, `HANDOFF`. `MODULES END` no significa que todos los módulos cargaron: revisar cada `MODULE FAIL`. Las marcas viven en kmsg y `/run/initramfs/eqs.log`; este último es volátil.

Si falla LVM, el candidato se detiene: no repara el PV como ext4 ni redimensiona volúmenes. Un fallo de mount tampoco permite continuar. El initramfs conserva los módulos del candidato para userspace; no los sustituye por módulos stock después del handoff.

- **Si aparece Plasma:** abrir terminal y recoger `uname -a`, `ps -p 1 -o comm=`, `findmnt /`, `cat /run/initramfs/eqs.log` y `journalctl -b`. Encontrar archivos desde recovery no equivale a un arranque nativo.
- **Si aparece el canal USB de emergencia:** el initramfs upstream ofrece telnet en `192.168.2.15:23` sobre RNDIS. En el host asignar `192.168.2.1/24` únicamente a esa interfaz USB, sin gateway ni conexión compartida. No cambiar Ethernet/Wi-Fi del host. Ese canal no garantiza acceso a systemd nativo.
- **Si sólo hay logo o pantalla negra:** no repetir un flash idéntico. Usar el rescate y recuperar pstore.

El canal telnet de emergencia no tiene autenticación; este paquete es sólo para desarrollo por cable directo, sin datos laborales. Se retiraron las identidades Dropbear pre-generadas y su autoarranque genérico. **No hay servidor SSH nativo nuevo**, cifrado daily, ni validación de Wi-Fi/Plasma/suspensión todavía.

## Rescate sin borrar la rootfs

Volver a AP Fastboot si el candidato no permite acceder. El script actualizado admite el rescate explícito de A aunque el bootloader haya seleccionado B por agotar los intentos. Ejecutar:

```bash
bash flash-candidate.sh --rescue-a SERIAL
fastboot -s SERIAL reboot recovery
```

Restaura las cuatro particiones de arranque y `recovery_a` desde `rescue/`. No restaura Android completo ni modifica userdata. Recovery v14 tiene ADB root/permisivo sin autenticación: no usarla como sistema diario. **Nunca relockear.**

Con recovery accesible, antes de más reinicios:

```bash
adb -s SERIAL root
adb -s SERIAL shell 'grep " /sys/fs/pstore " /proc/mounts || mount -t pstore pstore /sys/fs/pstore'
adb -s SERIAL pull /sys/fs/pstore ./pstore-eqs-halium2
adb -s SERIAL shell dmesg > recovery-dmesg.txt
```

El DT del candidato reserva ramoops en `0xae000000`, tamaño `0x60000`, consola `0x40000` y registros `0x20000`. La captura de recovery stock previa confirma ese mismo rango. Esto no garantiza que todos los fallos produzcan logs persistentes: comprobar montaje y contenido, no interpretar un directorio vacío como prueba de que el kernel no ejecutó.

## Reconstrucción en el repositorio

Con las referencias fijadas y el contenedor local de `BUILD-INFO.txt` disponibles, elegir un workspace nuevo:

```bash
export EQS_KERNEL_WORKDIR="$PWD/.work/eqs-halium-rebuild"
port/kernel/build-host-artifacts.sh dt-images-dev
port/kernel/build-host-artifacts.sh modules-dev-functional
port/kernel/build-dev-packages.sh --reuse-gates
```

Los artefactos se ensamblan dos veces y deben ser idénticos. Se comprueban config embebida en el kernel, inventario, vermagic, CRC de símbolos con depmod y contenido de boot/vendor_boot. Eso sigue siendo evidencia host, no una promesa de arranque físico.
