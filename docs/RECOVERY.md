# Primer flash y recuperación de `eqs`

## Ampliación del filesystem, 9 de septiembre

**Completada en el teléfono; H29 restaurado y Droidian/Plasma accesible por SSH.**
Ext4 pasó de 4194304 a **58856448 bloques de 4096 bytes**: 224,5195 GiB dentro del
LV existente de 241076011008 bytes. No hubo reparticionado, cambios de PV/LV ni
reinstalación. `df -h / /home` muestra **221G totales, 11G usados y 200G disponibles**
en el mismo filesystem. La diferencia con el tamaño bruto incluye metadata y,
para el espacio disponible, la reserva ext4 del 5 %, que no se modificó.

El preflight nativo había detectado `clean with errors`, ocho errores registrados y último
`EFSCORRUPTED` en `ext4_mb_generate_buddy` el 7 de septiembre. La ausencia de líneas
en el journal actual no prueba integridad. [Linux 5.10.209 prohíbe crecer online
con ese estado](https://github.com/gregkh/linux/blob/v5.10.209/fs/ext4/resize.c#L72-L80);
no forzarlo ni borrar el indicador para saltar el control.

- Se instalaron sólo `e2fsprogs` y `libss2` 1.47.2-3+b3, sin upgrades. Sus nuevas
  unidades automáticas `e2scrub_all.timer`/`e2scrub_reap.service` quedaron deshabilitadas.
- Ensayo **host/QEMU** con esas herramientas ARM64 y una copia **antigua** limpia:
  crecimiento a 224,52 GiB y `e2fsck -fn` antes/después aprobados, con el mismo
  recuento de 245793 archivos.
  No es un respaldo actual ni prueba de integridad del teléfono.
- Evidencia privada: `.work/eqs-grow.sconUf/`; metadatos y copia de ensayo fuera del
  repositorio en `~/.local/share/eqs-backups/full-root-20260909.FBNtKz/`.

**Acceso offline:** el primer intento, a las 13:23 ART, con conexión confirmada por Eduardo,
`systemctl reboot --reboot-argument=recovery` reinició correctamente, pero H29
volvió a arrancar Droidian/Wayfire sobre la misma raíz RW de 16 GiB. Bootconfig
confirma `androidboot.mode=recovery` y slot A; ese argumento no basta para entrar
en la recovery Android con este conjunto. SSH se recuperó sin reparar ni ampliar.
Después, con autorización específica, se cargó el rescate A ya probado mediante
USB directo y se obtuvo ADB root. Evidencia del primer intento:
`.work/eqs-grow.sconUf/recovery-reboot-native.txt`.

Eduardo dispensó expresamente la **nueva copia completa** para esta operación;
los metadatos actuales y los respaldos antiguos no son una copia actual de sus
archivos. Esto no elimina los controles offline ni autoriza reparaciones ciegas.
Se conservaron los archivos undo de reparación y crecimiento fuera del repositorio;
**no sustituyen un respaldo completo ni permiten recuperar un corte de energía**.
No aplicarlos a ciegas sobre una raíz que ya siguió cambiando.

### Resultado y comprobaciones

- Raíz desmontada, LV con cero aperturas y journal cerrado: `e2fsck -fn` devolvió 4,
  con inodos borrados sin fecha de eliminación y discrepancias en bitmaps/conteos.
- `e2fsck -f -p -E fixes_only -z …` devolvió 1 (corregido), sin `-y` ni reparación
  montada; nuevo `e2fsck -fn` devolvió 0 y el superblock quedó `clean`.
- `resize2fs -z … ROOT 58856448` devolvió 0; comprobación offline completa posterior
  también 0, con los mismos 331629 inodos ocupados que después de reparar.
- Montaje temporal `ro,noload`: ocho hashes de configuración/launchers iguales y
  `lost+found` vacío. Se desmontó y desactivó el LV antes de volver a fastboot.
- H29 restaurado: los **diez hashes de particiones completas de arranque A/B**
  coinciden con el preflight; UUID del filesystem, VG seqno 11, tamaños/extents
  LVM y hash del primer MiB del PV conservados. Ninguna escritura a B.
- A las 14:21 ART: systemd nativo, raíz RW, SSH, Wayfire/Plasma/Maliit activos,
  `errors_count=0` y sin errores de corrupción/I/O en el filtro del kernel actual.
  Escritura temporal como usuario, `fsync` y lectura SHA-256 aprobados; archivo retirado.
  Inventario dpkg y hold de Plasma iguales. `bluebinder`/`lxc-net` siguen fallidos
  como antes; fuera de esta operación. Interacción física posterior, pendiente del usuario.

Logs: `.work/eqs-grow.sconUf/{fsck-offline-preen,fsck-after-repair,resize-offline,fsck-after-grow}.txt`,
`readonly-files-after.txt`, `restore-h29-flash.txt`, `native-after.txt` y `native-final/`.
El undo de crecimiento, 3,2 GiB, se conservó comprimido (~74 MiB) con SHA-256
del contenido descomprimido verificado contra recovery; dos intentos de `adb pull`
fallaron, pero `adb exec-out gzip -c …` funcionó. Causa del corte de transferencia
no establecida; no fue un reinicio del teléfono.

**No repetir el resize para recuperar el arranque**, hacer factory reset, reparar
la raíz montada ni usar el flasher completo. Los backups H27/H28 siguientes son históricos.

## Iteración vigente: selección explícita del slot A

**H27, 5 de septiembre:** preview instalado y flasheado con el conjunto H13 de arranque A; respaldo completo de su filesystem fuera del repositorio en `~/.local/share/eqs-backups/preview-h27/`. El filesystem se amplió de 4,68 a 16 GiB tras verificar copia y ensayo; `e2fsck -f -n` antes/después aprobó y la metadata GPT/PV/LV no se modificó. No volver a ejecutar el resize como parte del rescate. La copia `root-before.img` es privada, no un artefacto distribuible.

El rescate exacto y el flasher con hashes están en `.work/eqs-preview-h27/boot-bundle/`. La preview usa `eqs-preview.timer` y **no retorna automáticamente a fastboot**. Si no hay acceso nativo, entrar físicamente en fastboot y usar el rescate A autorizado; no hacer factory reset ni asumir que recovery v14 tiene un kernel propio. Antes de cualquier nuevo ensayo, leer el estado real.

El 5 de septiembre se encontró A no arrancable con cero intentos y B activo. El rescate A más `set_active a` recuperó ADB y restableció siete intentos. **B no es un respaldo válido; no asumir que escribir A lo selecciona.**

El `port/bringup/flash-candidate.sh` actual reconoce Motorola y verifica selección/reintentos tras completar el conjunto A. El modo explícito `--rescue-a` permite recuperar desde B activo, sin escribir sus particiones. El script no reinicia ni toca userdata. Se probó físicamente con el bundle privado Halium10; el ZIP Halium2 antiguo conserva su script anterior.

Halium10 también confirmó retorno automático del servicio de diagnóstico a fastboot y posterior rescate. Esto no es arranque gráfico ni restauración completa de Android. Conservar pstore antes de más reinicios. [Evidencia y límites](BRINGUP-PLAN.md#slots-ab-y-retorno-automático--5-de-septiembre).

**Permisos LVM:** Halium11 encontró el LV raíz configurado persistentemente como sólo lectura; se corrigió con backup y Halium12 confirmó raíz RW/journal persistente. Para una inspección sin escrituras, montar `ro,noload`; no usar `lvchange --permission r` como sustituto, porque persiste tras reiniciar. No hay que formatear ni redimensionar. [Diagnóstico y corrección exactos](BRINGUP-PLAN.md#raíz-lvm-escribible-y-captura-persistente).

## Antecedente: candidato Halium2

**5 de septiembre:** primer flash autorizado completado en `vbmeta_a`, `dtbo_a`, `vendor_boot_a` y `boot_a`, seguido de reinicio normal. Sin escrituras a userdata/B/recovery. Arranque aún no confirmado. El guard del flasher del ZIP original no reconoce `securestate` ni la versión de bootloader segmentada de Motorola: falla antes de escribir. Se usaron comprobaciones equivalentes verificadas y comandos explícitos; no ejecutar ese script esperando que el preflight funcione sin corregirlo.

El bundle local `eqs-halium2-existing-rootfs-20260905.zip` actualiza solamente el arranque A y conserva userdata. Incluye un procedimiento explícito de rescate y comprobación offline; ver [instrucciones del candidato](../port/bringup/README.md). Sus pruebas son host/simuladas, no un ensayo físico del conjunto. No ejecutar los flashers completos antiguos.

## Estado del artefacto anterior

El ZIP `eqs-dev` anterior se construyó e inspeccionó en host y se flasheó físicamente en A/B. Entró en bootloop antes de que apareciera USB gadget/telnet, por lo que no demuestra arranque Droidian, pantalla, touch, red, carga ni USB. La unidad permanece recuperable desde Fastboot; no es una imagen diaria cifrada.

### Estado posterior comprobado: 4 de septiembre de 2026

- La rootfs Droidian está en `userdata`/LVM y se montó desde recovery. **No hacer wipe, factory reset ni volver a ejecutar el flasher completo para diagnosticar el arranque.**
- Evitar el flasher no basta: el initramfs fijado tiene fallback a reparación de `userdata` si falla LVM y resize automático condicionado por un marcador. Antes de otro candidato, proteger ese recorrido para detenerse sin reparar el PV ni redimensionar; ver el [contraste de la revisión externa](BRINGUP-PLAN.md#contraste-local-de-la-revisión-externa).
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
