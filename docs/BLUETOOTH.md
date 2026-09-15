# Bluetooth en eqs — actualizado el 15 de septiembre de 2026

## Mandos y auriculares: revisión del 15 de septiembre

**`joydev` está cargado en el teléfono y habilitado para próximos arranques,
sin reflashear. Falta reconectar el mando Xbox y comprobar botones/ejes en
el navegador.** No se hizo otro reinicio para probar persistencia.

### Mando Xbox por Bluetooth

El Xbox Wireless Controller `045e:02e0` ya llegaba a Linux mediante el driver
`microsoft`: tenía un nodo `event*`, `ID_INPUT_JOYSTICK=1` y permisos de lectura
para `droidian`. Faltaba `CONFIG_INPUT_JOYDEV` en H29. El
[Chromium 142 instalado usa joydev para botones y ejes](https://github.com/chromium/chromium/blob/142.0.7444.175/device/gamepad/gamepad_device_linux.cc#L270-L304);
emparejar correctamente no alcanzaba. No se instaló xpadneo ni se cambió firmware.

Se compiló `drivers/input/joydev.c` **sin modificaciones**, desde eqs
`bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582`, con Android Clang 12.0.5
`r416183b` / LLVM `c935d99d7cf2016289302412d708641d52d2f7ee` y una copia
privada del output H29. Se conservaron ThinLTO, CFI y MODVERSIONS.
Los **63 CRC importados** coinciden con el `Module.symvers` fijado;
`insmod` terminó correctamente y el taint permaneció en `4612`.
Wayfire, Plasma y Bluetooth siguieron activos, sin reiniciarlos.

| Input/artefacto | SHA-256 |
|---|---|
| Configuración H29 y `/proc/config.gz` descomprimido | `38e35affce93f0c08453b8c8577103edd9674c01b4edc7bb3179ef3d8bcd2c08` |
| `Module.symvers` H29 | `16743a80af3d9ef7ae2f930e9312a794b40ea19164663667ce99e2daf3106090` |
| `joydev.c` eqs | `4c51b757b58f73db7ba1b7da8891b3b506925054462561b2e26282d21f3de2e7` |
| `joydev.ko` suplementario | `6c65a9d0a91ad70ee65f269478ddd03d3a18ac6d3ec3d5abac8d74631845097e` |

El build usa Kbuild externo (`M=/module`, `obj-m += joydev.o`), con
`ARCH=arm64 LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu-`, el linker
LLD 12 fijado con `--threads=1` y la configuración **original**, no el fragmento
actual del repositorio. No usar `modules_prepare` como sustituto del output
completo con CRC ni reconstruir todo H29 para este arreglo.
Fuentes, receta ejecutada, `.cmd`, importaciones, logs y binario quedan en
`.work/eqs-joydev-h29/`; el output Bluetooth original quedó intacto.

También apareció un falso mando: el dispositivo virtual **`double-tap`**
expone ejes/botones y joydev le asignó `js0`. No confundir ese nodo con el Xbox.
`80-eqs-gamepad.rules` elimina **sólo** `ID_INPUT_JOYSTICK` para ese nombre,
sin quitar su nodo de eventos ni su función de despertar. En
[Chromium 142 la condición es presencia de la propiedad](https://github.com/chromium/chromium/blob/142.0.7444.175/device/gamepad/udev_gamepad_linux.cc),
por lo que asignar `0` no lo excluiría. La eliminación pasó la comprobación
nativa en `event3` y `js0`; el gesto físico sigue pendiente de regresión.

### Persistencia y alcance

- `/usr/local/lib/eqs-h29-joydev/{joydev.ko,SHA256SUMS}`: archivos root, modo
  `0644`, fuera del `/lib/modules` efímero.
- `/etc/systemd/system/eqs-h29-joydev.service`: copia de
  `port/kernel/eqs-h29-joydev.service`, habilitada en `multi-user.target`.
  Verifica versión de kernel, SHA de configuración y del módulo; no fuerza
  cargas ni descargas. Omite la carga si `joydev` ya existe.
- `/usr/lib/udev/rules.d/80-eqs-gamepad.rules`: instalada y aplicada sólo a
  los nodos `double-tap`. También se incluye en el paquete de adaptación.

`systemd-analyze verify` pasó en host y teléfono. Las precondiciones de
configuración e integridad pasaron en el teléfono. El arranque del servicio
se omitió correctamente porque el módulo ya estaba cargado manualmente:
**no equivale a haber probado un nuevo boot**.

Para comprobar el mando, encenderlo, identificar el `js*` cuyo
`/sys/class/input/js*/device/name` sea Xbox y probar el tester HTTPS con foco,
presionando un botón. No asumir un número fijo de nodo. Falta verificar ejes,
botones, reconexión y navegador; tampoco se probó vibración.

Para revertir, deshabilitar únicamente `eqs-h29-joydev.service`; en el siguiente
reinicio no se cargará el módulo suplementario. No forzar `rmmod` mientras
haya consumidores. Retirar la regla específica sólo si se quiere revertir
también la exclusión de `double-tap`; no borrar emparejamientos.

**Imagen:** el H29 binario y el ZIP existente no cambiaron. El fragmento de
futuros kernels ahora exige `CONFIG_INPUT_JOYDEV=y`, pero eso no agrega
retroactivamente el módulo al H29 fijado ni a una rootfs construida con él.
El loader y módulo suplementarios son una instalación en el teléfono, no una
nueva imagen publicada.

### Auriculares: qué está disponible y qué falta probar

| Función | Evidencia actual |
|---|---|
| Música A2DP y controles AVRCP | BlueZ anuncia los perfiles; PulseAudio carga `module-bluetooth-policy` y `module-bluez5-discover`. Falta reproducción/controles con un auricular real. |
| Transporte de voz SCO | `CONFIG_BT_BREDR=y` incluye `sco.o`; apertura/cierre de socket SCO pasó como `droidian`, sin transmitir audio. `bluebinder` fijado incluye envío/recepción SCO. |
| Micrófono HSP | HSP Audio Gateway anunciado. Falta negociación y grabación reales. |
| Micrófono HFP | PulseAudio Droidian 14.2 depende de oFono; no se observó HFP Audio Gateway `111f`. oFono activo no demuestra ese rol. Falta validar el backend con un auricular identificado. |

No se encontró otro módulo de kernel faltante para audio Bluetooth clásico.
No se conectó un auricular durante esta revisión: la única tarjeta PulseAudio
era `droid_card.primary`. No se prometen codecs avanzados ni LE Audio.
No se migró a PipeWire ni se actualizó PulseAudio: primero comprobar el
auricular real y su perfil, preservando el audio Android que funciona.

Verificación host realizada: 11 tests de configuración, incluido RED/GREEN
para `INPUT_JOYDEV`; validación de regla udev y unidad systemd; paquete ARM64
construido en el SDK local rootless y payload inspeccionado (7 archivos y un
symlink, regla idéntica modo `0644`). No se ejecutó el builder Docker completo
ni se reemplazó el paquete de adaptación instalado.

## Registro original: 9 de septiembre de 2026

> Registro fechado. Para la imagen consolidada y el estado posterior, ver
> [release del 10 de septiembre](RELEASE-20260910.md). No repetir ensayos
> históricos ni inferir que un ZIP viejo incorpora cambios posteriores.

**El controlador ya inicializa y detecta dispositivos en H29, sin flashear;
la carga automática sobrevivió a un reinicio normal del teléfono.**
Faltan pruebas de emparejamiento y uso con periféricos identificados por Eduardo;
los UUID anunciados no demuestran audio, micrófono ni entrada funcionales.

## Qué se corrigió

El kernel instalado `5.10.209-android13-0-gbd42a1bb7281` tenía Bluetooth,
RFCOMM, HID y LE, pero no `CONFIG_BT_HCIVHCI` ni BNEP. Por eso no existía
`/dev/vhci`, necesario para el `bluebinder` instalado (`cec1d04`). El HAL
Qualcomm HIDL 1.0 ya estaba activo: no hubo que reemplazar firmware ni permisos
de sus dispositivos privados dentro de Android.

Se compilaron `hci_vhci.ko` y `bnep.ko` desde la fuente **eqs**, sin modificar
sus archivos C. Se conservaron el kernel, su configuración efectiva,
Clang 12.0.5, ThinLTO, CFI y los CRC de símbolos del build H29. La carga nativa
de ambos módulos pasó sin forzar ABI ni cambiar el taint previo del kernel.

También faltaba el hook de dirección. `androidboot.btmacaddr` de bootconfig
coincide **en orden directo**, no invertido, con la dirección pública que
devuelve el controlador. El helper nuevo valida esa entrada y escribe
`/var/lib/bluetooth/board-address` atómicamente, sin imprimir la dirección;
rechaza valores ambiguos, inválidos, enlaces simbólicos y conflictos existentes.
El post-start original de Droidian vuelve a ejecutarse y termina en cero.

La regla genérica `65-android.rules` también dejaba el `/dev/uhid` nativo
como `system:system 0660`. BlueZ corre como root **sin** capacidades para
ignorar permisos DAC: una apertura con sus capacidades exactas (`0x1400`)
fallaba con `EACCES`. `80-eqs-bluetooth.rules` asigna sólo ese nodo a
`root:root 0600`; la misma prueba ahora pasa. No se ampliaron capacidades
ni grupos. El nodo privado de Android es otro inode y quedó intacto.

## Instalación actual y arranque automático

`/lib/modules` es un bind de un **tmpfs generado por el initramfs**: copiar
los módulos solamente allí no persistiría. Para el H29 instalado se usan:

| Archivo | Función |
|---|---|
| `/usr/local/lib/eqs-h29-bluetooth/{hci_vhci,bnep}.ko` | Módulos suplementarios, sólo para el kernel H29 exacto. |
| `/usr/local/lib/eqs-h29-bluetooth/SHA256SUMS` | Integridad comprobada antes de cargar. |
| `/etc/systemd/system/eqs-h29-bluetooth-modules.service` | Carga oneshot, timeout de 15 s y condición de versión de kernel; omite la carga si VHCI ya existe. |
| `/etc/systemd/system/bluebinder.service.d/30-eqs-h29-modules.conf` | Hace que el puente dependa de esa carga. |
| `/usr/bin/droid/droid-get-bt-address.sh` | Hook instalado desde la adaptación del repositorio. |
| `/usr/lib/udev/rules.d/80-eqs-bluetooth.rules` | Permite a BlueZ abrir UHID manteniendo la inyección de entrada restringida a root. |

La ruta permanente pasó una prueba completa de **parada del puente,
descarga de módulos y arranque por systemd**. Después se reinició el teléfono:
SSH volvió en un boot nuevo, con el mismo kernel H29; loader, `bluebinder` y
BlueZ activos, y el controlador encendido. Wayfire/Plasma seguían funcionando
y el contador de errores ext4 permaneció en cero. Es **un reinicio normal**,
no una validación de arranques en frío repetidos ni ciclos de suspensión.
**Límite observado:** el primer intento registró `bt_power gpio config failed`
y el HAL recibió SIGKILL durante la inicialización; el reintento automático
funcionó unos 60 s después. No se considera resuelta
esa demora ni se agregó un `sleep` arbitrario. La regla UHID se aplicó y
verificó después de ese reinicio, sin otro reboot.

No se cambió PulseAudio, Plasma, el firmware ni ninguna partición de arranque.
La recepción automática de archivos y el acceso de red PAN no se habilitaron.
No se emparejaron dispositivos ajenos encontrados durante el escaneo.

## Evidencia y límites

| Comprobación | Resultado |
|---|---|
| `insmod hci_vhci` y `insmod bnep` | Ambos terminaron en cero; VHCI creó `/dev/vhci`. |
| `bluebinder` y HAL Qualcomm | Activos; log `Bluetooth initialized successfully`. |
| Dirección real frente a bootconfig | Coincide sin invertir bytes; no se publica el valor. |
| Escaneo antes/después de reiniciar | 15 s y 12 s, ambos exit 0 y cinco dispositivos observados; finalizan sin dejar discovery activo. |
| Socket nativo BNEP | Creación/cierre correctos; **no** es una prueba de tethering. |
| Teclado/mouse HID y HOGP | Protocolos y apertura de UHID con capacidades BlueZ verificados; emparejamiento y uso pendientes. |
| Música A2DP/AVRCP | Endpoints registrados; reproducción y controles pendientes. |
| Micrófono HFP/HSP | Pendiente. PulseAudio Droidian 14.2 tiene backend nativo HSP; HFP depende de oFono. No se observó HFP Audio Gateway anunciado. |
| Archivos OBEX | Después del reinicio anuncia Object Push y File Transfer; transferencia real pendiente. |
| Suspensión/reconexión con periféricos | Pendiente. |

No migrar a PipeWire ni activar un módem ficticio sólo para cambiar una lista
de perfiles. Primero probar un auricular real y observar la negociación y SCO.

## Código y verificación en host

- `port/kernel/eqs-halium.config`: ahora exige VHCI y el conjunto Bluetooth
  común, incluido BNEP con filtros. El próximo kernel los integrará directamente;
  no reutilizar los módulos suplementarios H29 con otro ABI.
- `port/adaptation-motorola-eqs/usr/bin/droid/droid-get-bt-address.sh`:
  hook empaquetado, con pruebas de validación y preservación.
- `port/build-adaptation-packages.sh`: verifica contenido y modo ejecutable.
- `80-eqs-bluetooth.rules`: verificada por `udevadm verify` en host y teléfono.

```sh
python3 port/test-bluetooth-address.py
python3 port/kernel/test-eqs-config.py
python3 port/kernel/test-module-inventory.py
bash -n port/build-adaptation-packages.sh
git diff --check
```

Prueba nativa mínima de UHID, como root y sólo con autorización: abre/cierra
el nodo, **no** crea un teclado ni inyecta eventos.

```sh
setpriv --bounding-set=-all,+net_admin,+net_bind_service \
  --inh-caps=-all --ambient-caps=-all python3 -c \
  'import os; fd=os.open("/dev/uhid", os.O_RDWR|os.O_CLOEXEC); os.close(fd)'
```

RED: el resolver anterior aceptaba 11 requisitos Bluetooth ausentes.
GREEN: los 11 tests de configuración, el test de dirección (host y ARM64) y
los dos tests de inventario pasan. La configuración se resolvió con la toolchain fijada;
los paquetes de adaptación se construyeron dos veces con resultados idénticos.
No se instaló el metapaquete ni se reconstruyó una imagen completa.

Artefactos locales privados: `.work/eqs-bluetooth-h29/`, con scripts de build,
configuraciones, `Module.symvers`, logs y paquetes finales en `adaptation-final/`.
Las unidades instaladas y el journal sanitizado están en `phone-files/`.
El build suplementario usa
el output H29 conservado, no la configuración nueva. Las 48 importaciones de
VHCI y las 82 de BNEP coinciden con sus CRC; ambos contienen comprobación CFI.

| Módulo | SHA-256 |
|---|---|
| `hci_vhci.ko` | `59700e154ccbf92eed86534eeca7d46e27703d2ac2ee0c5a2ecb9574c70919d9` |
| `bnep.ko` | `47a8705d6c9033a3507215f1b33f811fe95416b4bbc7294cc0167810ed77abfa` |

## Reversión de esta corrección

Con autorización para modificar el teléfono, detener primero `bluebinder`,
retirar únicamente el drop-in y servicio H29 enumerados arriba y ejecutar
`systemctl daemon-reload`. Descargar `bnep` y `hci_vhci` sólo si no están en uso;
**nunca forzar** la descarga. Un reinicio sin el loader tampoco los cargará.
Los módulos y el helper pueden conservarse inertes para diagnóstico.
Para revertir UHID, retirar sólo `80-eqs-bluetooth.rules`, recargar reglas y
restaurar el propietario/modo anterior del nodo nativo; no tocar el nodo Android.
No borrar `/var/lib/bluetooth`: podría contener emparejamientos creados después.
Respaldo previo: `/root/eqs-bluetooth-before-20260909/`.

## Fuentes

- [Requisitos de kernel Droidian](https://docs.droidian.org/porting-guide/kernel-compilation/).
- [Hook de dirección Droidian](https://docs.droidian.org/porting-guide/debugging-tips/#bluetooth-crashing).
- [bluebinder fijado, cec1d04](https://github.com/droidian/bluebinder/blob/cec1d04/bluebinder.c).
- [Módulos externos y MODVERSIONS](https://docs.kernel.org/kbuild/modules.html).
- [PulseAudio instalado: backend nativo](https://github.com/droidian/pulseaudio/blob/dc4fdb8/src/modules/bluetooth/backend-native.c)
  y [oFono](https://github.com/droidian/pulseaudio/blob/dc4fdb8/src/modules/bluetooth/backend-ofono.c).
