# Bluetooth en eqs — 9 de septiembre de 2026

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
