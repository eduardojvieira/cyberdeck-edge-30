# H29: cámaras, rotación y navegador

> Registro fechado. Para la imagen consolidada y el estado posterior, ver
> [release del 10 de septiembre](RELEASE-20260910.md). No repetir ensayos
> históricos ni inferir que un ZIP viejo incorpora cambios posteriores.

**Preview H29 instalado, 6 de septiembre de 2026.** Principal y frontal producen
vista previa en la app real; el bloqueo de rotación está instalado y confirmado
por IPC nativo. Faltan fotos/calidad, giro físico y cámaras auxiliares. Se conserva
la raíz existente y el rescate A, sin escribir B. Esto no es una nueva imagen diaria.

## Corrección del bloqueo horizontal — 9 de septiembre

**Código `+eqs4` corregido, instalado y activo por SSH, sin reflashear.**
El reporte de Eduardo reveló un límite de los ensayos H29:
comprobaban `lock_rotation=true`, pero no que conservara la orientación.

`QSaveFile` provoca la recarga completa de Wayfire. La INI anterior contenía
`transform=auto`, que el compositor rechaza y convierte en `normal` (vertical).
El journal nativo confirma `Bad output transform in config: auto` al recargar.
Con el sensor bloqueado ya no vuelve a horizontal.
Esto coincide con el [parser y la recarga del Wayfire fijado](https://github.com/droidian/wayfire/blob/258413269d5904e3ed89546af309df020348f0fe/src/core/output-layout.cpp).

El mismo quicksetting ahora lee la orientación **real** de `HWCOMPOSER-1` vía
`QScreen` y guarda `transform` explícito + `lock_rotation` en una sola escritura
atómica, tanto al bloquear como al habilitar la rotación. No lee el acelerómetro
ni agrega daemon, compositor o dependencia de producción. La correspondencia
de orientaciones se comprobó contra [QtWayland 6.8.2](https://github.com/qt/qtwayland/blob/v6.8.2/src/client/qwaylandscreen.cpp).

La regresión falla contra el parche anterior y pasa con el nuevo bajo
ASan/UBSan/LSan. Cubre las cuatro orientaciones, habilitar/deshabilitar,
persistencia, INI incompleta o inválida y ausencia de pantalla real. También
pasan las 27 regresiones de PAM/IPC/navegación y los seis rechazos del builder.
El paquete ARM64 final pasa importación Qt 6.8.2. En el teléfono, su singleton
mantiene `90` y `270` al desactivar/reactivar autorrotación: se verificaron tanto
el transform real del compositor como el booleano efectivo por IPC. Se restauró
la orientación inicial `270`, autorrotación habilitada y los demás bytes de la
INI intactos. No se simuló movimiento del sensor ni entrada táctil.

Se recargó sólo la unidad de usuario de plasmashell, con la sesión desbloqueada.
Plasma PID 6234 → 39036; Wayfire 5801, terminales, Firefox y boot ID intactos.
El paquete conserva su hold; auditoría y verificación dpkg limpias.
[Artefacto, comandos de prueba y respaldo](../port/plasma-mobile-wf/README.md#current-phone-installation-and-rollback).
Evidencia privada: `.work/eqs-rotation-lock/`. Prueba manual pendiente: bloquear
en ambos horizontales, girar físicamente, bloquear/desbloquear la sesión y volver
a activar el sensor. Tampoco se ensayó otro arranque.

## Hallazgos y siguiente acción

| Problema | Evidencia | Acción / límite |
|---|---|---|
| Cámaras con 0 MP | Abrir 0 o 1 como usuario nativo mata `minimediaservice`: `MediaProfiles.cpp:1001 CHECK(fopen(xml))`. La propiedad apunta a un XML inexistente. | Alias de overlay relativo `media_profiles_vendor.xml → media_profiles_cape.xml`. Ambas abren y enumeran tamaños. La app real reveló además EVA ausente; con su módulo, **principal: 124 fotogramas; frontal: 113**, ambas en PREVIEW. Foto/calidad aún no validadas. |
| Faltan auxiliares | Los cuatro sensores pasan el probe del kernel. Stock expone cinco IDs HAL (cuatro físicos + uno lógico), Droidian sólo dos. Stock también limita la lista pública API1 a dos. | El tercer ensayo con `multiCameraLogicalXMLFile=eqs.xml` sigue exponiendo sólo dos: override retirado. No es un arreglo para las auxiliares. |
| Bloqueo rota con autorrotación desactivada | Plasma modifica KScreen, pero Wayfire escucha SensorProxy y usa `autorotate-iio/lock_rotation`. | Parche al quicksetting existente, sin daemon ni otro compositor. Paquete `+eqs3` instalado. **Ensayos nativos 4–6: singleton PASS y Wayfire confirma `lock_rotation=true`.** Falta giro físico con/sin bloqueo. |
| Firefox desborda / preferencia Chromium | Ancho incorrecto reportado por Eduardo; aún no reproducido instrumentalmente. | Chromium oficial ARM64 con Ozone/Wayland, sandbox intacto y prueba de viewport real. Descarga puntual pendiente de autorización por la regla de red del workspace. |

## Cámaras: qué quedó demostrado

- Kernel H28 sin cambiar: `mot_s5khp1`, `mot_ov60a`, `mot_s5kjn1`, `mot_imx663`
  pasan lectura de ID y probe en slots 0–3.
- Los errores de carga directa `CAMERA_ICP` tienen fallback de ueventd exitoso:
  el mismo log confirma `FW download done successfully`. No justifican otro kernel.
- El ensayo inicial, sin Qt ni preview, reprodujo `DEAD_OBJECT`. Tombstones 27/28
  sitúan el aborto en MediaProfiles, no en el servicio USB/UVC Motorola que también falla.
- Con el alias, API1 informa máximo de foto **4096×3072 trasera** y
  **4576×3296 frontal**. Son capacidades reportadas, no JPEGs capturados ni prueba
  de calidad. No confundirlas con los 200/60 MP físicos o prometerlos en esta API.
- El XML stock cape tiene SHA-256
  `fcc1503d03954c8618deb6b7b72025fb91e25968fb723964fc8d9fbf7d4c026e`.
  No se inventan perfiles ni se copian blobs de bronco.

## Verificación local y evidencia privada

```sh
python3 port/plasma-mobile-wf/test-rotation.py PINNED_PLASMA_SOURCE
python3 port/plasma-mobile-wf/test-safety.py .work/plasma-safety/upstream-full
python3 port/plasma-mobile-wf/test-build-package.py PINNED_PLASMA_TAR_GZ
python3 port/bringup/diagnostics/test-camera-probe.py
python3 port/bringup/diagnostics/test-capture.py
python3 port/kernel/test-module-inventory.py
python3 port/plasma-mobile-wf/test-navigation-config.py
```

Rotación: clase C++ exacta, QtCore + ASan/UBSan; persistencia, recarga por reemplazo
atómico, preservación de escapes y rechazo de archivos inválidos. Safety: 27 PASS.
Builder: seis rechazos, con RED previo para el gate faltante del parche de rotación.
Esto es evidencia **host**, no gestos ni giro físico. Los ensayos nativos de cámara
sí corrieron en eqs como UID 32011, con timeout y retorno acotado a bootloader.
Los tres primeros ensayos no abrieron preview ni capturaron imágenes; el helper es opt-in temporal. Los ensayos 4–6 abren la app instalada durante 22 segundos como usuario, sin entrada sintética, desbloqueo ni disparo de fotos; consultan estadísticas mientras está abierta.

`.work/eqs-h29/` conserva copia de archivos anteriores, fuentes consultadas,
logs `native-camera-trial1/2/3` y `native-trial4/5/6`, tombstones acotados y salidas de build. No publicar
bugreports completos ni datos personales. Los helpers temporales de apertura y
rotación ya se retiraron; el preview final no abre cámaras automáticamente.

## Paquete H29 original y rescate (6 de septiembre)

Sólo `plasma-mobile-wf +eqs3`, SHA-256
`acc879833e6ff3dd2845f346d483ed17337b26883dd4a4b4061567c0c25243ab`.
`dpkg --audit` limpio, hold retenido, guardas temporales de servicios/flash
retiradas. Qt, Image/DT H28, HWC y layout de datos no cambiaron; el ensayo 5 agrega un módulo a vendor_boot. La INI conserva
sus bytes anteriores y agrega `lock_rotation = true`; propietario/modo retenidos.
Los ensayos 4–6 recuperaron logs y confirmaron el ajuste efectivo. No se desbloqueó
la pantalla para obtener capturas.

El conjunto `.work/eqs-h29/boot-bundle/` pasó hashes y se flasheó sólo en A; se
inició el arranque normal a las **17:32:48 UTC**. Se retiró el retorno automático,
se habilitó `eqs-preview.timer` sin acción de reinicio y se restauró la selección
de cámara principal. `final-root.log` registra auditoría limpia, ownership y
hashes; `final-flash.log` registra cada escritura. No se reinstaló `userdata`.
Los ensayos anteriores prueban arranque nativo; la pantalla final queda para
la observación de Eduardo, no se infiere de un `fastboot reboot` exitoso.
La observación host de las **17:35:06 UTC** confirma el gadget `Droidian / eqs
USB diagnostic` a 480 Mb/s con interfaz RNDIS; no demuestra pantalla, SSH ni
estabilidad sostenida. Los checks host finales figuran en `final-host-checks.log`.

### Segundo fallo de cámara: EVA omitido

La app instalada inicia el sensor principal y el kernel observa el primer SOF,
pero el proveedor Qualcomm termina con SIGSEGV en
`CamX::EVANode::ExecuteProcessRequest+1604`: falló crear la sesión EVA y luego
se desreferenció un puntero nulo. H28 no incluía `msm-eva`; el init vendor había
esperado 61 segundos sin encontrar el control de arranque CVP.

El DT eqs real contiene `qcom,msm-cvp` y firmware `evass`, atendidos por
`qcom/opensource/eva-kernel`. `cvp-kernel` atiende otro compatible, `msm-cvp21`;
no cargar ambos por intuición. El módulo nuevo se compiló con las fuentes y ABI
H28, sin cambiar Image/config/DT. El inventario anterior falla por ese módulo
ausente; el nuevo pasa **317 internos + 52 externos**.

Dos empaquetados `vendor_boot` idénticos pasan dependencias/CRC de símbolos de
los 369 módulos y mantienen los 325 tempranos. EVA se solicita en systemd, no
se agrega a la lista temprana. SHA-256 del candidato:
`766b36c0ae86bd1bd350a1c228eaf2961b95e75ffe2cb2b7743469cb90a24632`.
**Ensayo 5 nativo:** firmware `EVA.FIRMWARE.3.0-47` arrancado, control CVP
completa en 0,882 s en lugar de fallar a los 61 s. App en `PREVIEW`, salida
1920×1440 con **124 fotogramas producidos** al consultar; sin muerte del proveedor
ni `DEAD_OBJECT` durante la prueba. Captura de foto configurada a 4096×3072,
pero no se accionó el disparador. **Ensayo 6 nativo:** frontal ID 1 en `PREVIEW`,
1920×1440 y **113 fotogramas producidos**, sin los fallos EVA/proveedor anteriores.
La app seleccionó foto 4:3 de 4000×3000; tampoco se accionó el disparador. Entre
ambos ensayos sólo cambió la selección de cámara, no el paquete ni el arranque.

La raíz nativa muestra `/dev/cvp` como root 0600, y Android lo ve correctamente
como system:camera 0660: no ampliar permisos globales. El control sysfs `boot`
es de escritura, por lo que su rechazo a `cat` no indica fallo del firmware.


## Fuentes y código consultados

- [Droidian: diagnóstico de cámaras y ambas rutas AAL/droidcamsrc](https://docs.droidian.org/porting-guide/debugging-tips/#camera-support).
- [AAL fijado: conexión antes de inicializar resoluciones](https://github.com/droidian/qt5-cameraplugin-aal/blob/8f9043571fcc3cea6ddfa32314a2dbc53742e594/src/aalcameraservice.cpp).
- [Camera app fijada: selección de resolución y etiquetas](https://github.com/droidian/droidian-camera/blob/a0b51cd89ca73d7688d97ec42fc285c9997de8a7/src/qml/main.qml).
- [API de multicámara Android: IDs físicos y cámara lógica](https://source.android.com/docs/core/camera/multi-camera).
- [MediaProfiles Android 12.1: propiedad XML y apertura fatal](https://github.com/LineageOS/android_frameworks_av/blob/lineage-19.1/media/libmedia/MediaProfiles.cpp).
- [EVA fijado: dispositivo CVP y firmware](https://github.com/eqs-development/android_kernel_motorola_sm8475-modules/blob/9f8d247d457622c08ff547e5498e6fa453e876ed/qcom/opensource/eva-kernel/msm/eva/cvp.c).
- [Wayfire fijado: autorotate-iio](https://github.com/droidian/wayfire/blob/258413269d5904e3ed89546af309df020348f0fe/plugins/single_plugins/autorotate-iio.cpp).
- [Qt 6.8: QSaveFile](https://doc.qt.io/qt-6.8/qsavefile.html) y [QFileSystemWatcher](https://doc.qt.io/qt-6.8/qfilesystemwatcher.html).
- [Chromium: Ozone/Wayland](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/ozone_overview.md) y [paquetes de seguridad Debian trixie](https://packages.debian.org/trixie/chromium).

## Próxima prueba manual

1. Despertar y desbloquear normalmente; desactivar autorrotación y girar el equipo,
   tanto desbloqueado como bloqueado. Volver a activarla y repetir.
2. Abrir Cámara, probar principal/frontal y guardar una foto con cada una. Comprobar
   archivo, foco, colores, orientación y dimensiones; los contadores de preview no
   sustituyen estas pruebas de imagen.
3. Auxiliares y resoluciones mayores requieren resolver la exposición HAL/API,
   no cambiar etiquetas ni prometer 200 MP. Chromium sigue sin instalarse.

## Hub USB-C y teclado

**Actualización del 7 de septiembre: el teléfono mantiene hub y teclado sin PD
después de negociar source antes de retirar el cargador.** Eduardo confirmó
funcionamiento; SSH a las 19:14 ART corroboró receptor presente, host/source,
batería descargando y pantalla encendida. **La reconexión posterior sin PD falló**;
reinicio aún sin validar. No se instaló un parche de alimentación ni se reflasheó.

Antes de ese avance, sólo funcionaban con alimentación externa. El control
nativo de las 18:50 ART confirmó la enumeración con PD. El problema se concentra
en iniciar/mantener la alimentación; no repetir POR1 ni PM. No se midió tensión
en el conector ni carga sostenida del teléfono.
El control de datos y el rol de alimentación son distintos
([clase USB Type-C de Linux](https://docs.kernel.org/driver-api/usb/typec.html)).
Eduardo confirmó luego que el teclado deja de responder al retirar PD y pausó
la reparación. **El 7 de septiembre a las 17:54 ART pidió retomarla por SSH:**
necesita alimentar el hub sin power bank; admite cortes durante el reposo,
pero no con la pantalla encendida. No repetir los ensayos PM/POR1 ya fallidos.

### Investigación del 8 de septiembre: qué parche corresponde

**Todavía no hay una corrección causal validada.** La siguiente intervención debe
distinguir una alimentación que no llega al hub de un fallo de inicialización
con VBUS presente; no repetir resets de PHY, PM ni escrituras de `source`.
Esta revisión usó fuentes web, código local y capturas existentes, sin actuar
sobre el teléfono.

Fuentes locales limpias y fijadas para la comparación:

| Árbol bajo `reference/repos/` | Commit |
|---|---|
| `eqs-development/android_kernel_motorola_sm8475` | `bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582` |
| `eqs-development/android_kernel_motorola_sm8475-modules` | `9f8d247d457622c08ff547e5498e6fa453e876ed` |
| `droidian-devices/linux-android-lenovo-bronco` | `3d1ed931716f88d002207b03db5f0a77e762b921` |

**UCSI no quedó atascado en la conexión fría capturada.** Desde uptime
55228 s, `empty-hub-ucsi.txt` contiene 14 observaciones CCI sin
`NOT_SUPPORTED`, `BUSY` ni `ERROR`. Las nueve escrituras CONTROL reciben la
confirmación esperada en 0,290–0,419 ms: cuatro consultas, sus cuatro ACK y
un ACK del cambio de conector. Esto delimita esa transición, no certifica
todo UCSI ni otras conexiones.

| Candidato encontrado | Aplicabilidad al fallo observado |
|---|---|
| Copiar `ucsi_glink.c` de Bronco | Es idéntico byte a byte al de eqs; no hay diferencia que transplantar. |
| [ACK de comandos no soportados](https://lists.openwall.net/linux-kernel/2024/03/20/314) | Bronco sí lo incorpora y eqs no. Corrección real, pero no hubo `NOT_SUPPORTED` en esta transición. No presentarla como arreglo del hub. |
| [Cambio de manejo de `CCI_BUSY` en Qualcomm](https://lkml.rescloud.iu.edu/2404.0/08267.html) | El callback local ya espera ACK/COMMAND_COMPLETE, sin la salida prematura por BUSY eliminada por ese parche. Tampoco se observó BUSY. |
| [VBUS antes del inicio de datos en TCPM](https://www.spinics.net/lists/stable-commits/msg424777.html) | Señala la importancia de la secuencia, pero modifica `tcpm.c` de Linux. En eqs esa política corre en firmware ADSP, visible mediante UCSI; no se arregla copiando ese diff. |

Bronco también tiene cambios de timeout, reset e inicialización UCSI. No
explican por sí solos esta conexión atendida en milisegundos. El SHA-256 común
de `ucsi_glink.c` es
`46a68ca2f74f3b6cbf91072a7cd4b005fa3b104b81366088d5583e16eb5ed952`.
`dwc3_otg_start_host()` está en `drivers/usb/dwc3/dwc3-msm-core.c`: configura
PHY/xHCI y el rol de datos, no un regulador de salida VBUS.

**El orden temporal es una pista, no la causa demostrada.** Los contadores
UCSI/IPC y los eventos coincidentes de firmware permiten alinear aproximadamente
la captura a 19,2 MHz: notificación UCSI en 55228,333 s, inicio del host en
55228,356 y log `SourceVbus=1` en aproximadamente 55228,474. Este último aparece
unos 142 ms después de la notificación; no mide cuándo subió la tensión física.
Antes, `HW_GetVbusVoltage` informa **−1 mV**: no tratarlo como tensión negativa
medida, cero voltios ni lectura ADC válida. Tampoco los 5200 mV solicitados
demuestran salida estable. No agregar un delay arbitrario basándose sólo en esto.

**El diagnóstico ADC no entregó datos ni sin hub ni con PD y receptor enumerado.
No sirve como medida de VBUS en esos estados; suministro USB aún pendiente.** El parche
optativo `port/kernel/patches/0002-qti-charger-read-only-telemetry.patch` reutiliza
`qti_glink_charger`, sin daemon ni cambios en órdenes de potencia:

- Agrega `switchedcap_snapshot`, lectura sysfs **0400**, bajo demanda, con campos
  crudos `vusb_mv`, `vbus_mv`, `vout_mv` e `ibus_ma`, entre otros. Consulta sólo
  los convertidores configurados (1–2), valida el layout de 40 bytes y rechaza
  una representación inválida del booleano recibido. Valores crudos negativos
  o ceros no prueban tensión en el conector: falta contrastarlos con el control
  funcionando.
- El lector compartido valida cabecera y longitud; acepta el campo de propiedad
  en cero que devuelve este firmware, o el ID solicitado si se informa. **No
  puede usar ese cero como correlación.** Un lock corto protege la respuesta
  contra sobrescrituras/duplicados pendientes. Una consulta ADC no se
  encola detrás del cargador (`EBUSY`). Usa el timeout de respuesta existente
  de 5 s; después de **cualquier lectura fallida**, incluso una normal del
  cargador, las siguientes consultas ADC dan `EPIPE` sin reenviar. Una respuesta
  de batería tardía también tiene 40 bytes. El protocolo no tiene ID de
  transacción: no resetear ese bloqueo para perseguir una respuesta tardía.
  Las lecturas normales del cargador continúan.
- Pasan **14 casos host** compilando las funciones C reales con transporte
  determinista y UBSan, más los **11 tests de configuración eqs**. El baseline
  demuestra aceptación de propiedad equivocada, sobrescritura por duplicados y
  reintentos ADC inseguros. No son pruebas de scheduling del kernel ni HIL.
- El build ARM64 con la toolchain H29 pasó: **75 símbolos importados** con CRC
  compatible, exports preservados y mismos hashes de kernel/config/symvers.
  Incluye `CONFIG_WIRELESS_CPS4035B=m` para el formato correcto de diagnóstico.
  No aplica automáticamente el parche a builds de producción.

Verificación: `python3 port/kernel/test-charger-telemetry.py`,
`python3 port/kernel/test-eqs-config.py` y
`python3 port/bringup/diagnostics/test-usb-adc-prepare.py` (**14 casos de
preparación de un solo arranque**, simulados en host). Receta, manifiesto y
artefacto corregido privados: `.work/eqs-usb-adc-wire.8437112q/`;
`artifacts/candidate/qti_glink_charger.ko`, SHA-256
`5d8142809f6ec33b198a7f2eddbb4b97fd2608ac6d662ca05a22484c46850c85`.
**Un `.ko` no es una imagen fastboot.** No se empaquetó ni flasheó otra imagen.

**Prueba del 8 de septiembre y corrección del diagnóstico:** el primer candidato
`f43a99d…` arrancó con SSH/Plasma, pero provocaba timeouts en lecturas normales
1 y 34; se rechazó antes de consultar ADC o conectar el hub. El retorno al H29
original `148f1c4c…` quedó comprobado por SSH a las 17:22 ART, sin esos timeouts.
Su logger upstream registró **31 respuestas con campo de propiedad cero** para
consultas 0, 1, 21, 34 y 36. No es una conjetura sobre alimentación: es una
incompatibilidad del primer diagnóstico con la ABI real. Dos nuevos tests
fallaron con ese candidato y pasan con la corrección; no se retiraron los tests
anteriores ni las guardas de longitud/cabecera.

**Activación temporal:** el initramfs conserva los módulos en
`/run/eqs-modules` y los monta sobre `/usr/lib/modules`. La copia en la raíz
persistente no gobierna ese árbol. `eqs-usb-adc-prepare.service`, antes de
modules-load/udev, verifica kernel y hashes y reemplaza únicamente el `.ko` en
RAM mediante rename atómico. Consume y sincroniza primero el marcador de
armado; el siguiente reinicio recupera H29 desde el `vendor_boot` intacto.
Rechaza módulos ya cargados: **no hace hot-unload del driver del cargador**.
El backup exacto está en `/var/lib/eqs-usb-adc/h29-qti_glink_charger.ko`.
El candidato corregido se armó a las 17:29 ART y se reinició a las 17:30.
SSH comprobó módulo `5d814280…`, interfaz sysfs 0400 y servicios
SSH/Plasma/LXC activos. `systemd-analyze --man=no verify` aceptó la unidad y
el orden con sysinit/modules-load/udev; `--man=no` omite sólo manuales ausentes.
El marcador quedó consumido y se deshabilitó otra vez la unidad.

**Resultado ADC sin hub, 17:33:54 ART:** una consulta 49 de 40 bytes recibió
respuesta en unos 0,27 ms, pero con `data_size=0`. Se rechazó con `ENODATA`;
no se inventaron lecturas ni se reintentó. Esto **no mide cero voltios** ni
demuestra que la consulta falle también con alimentación conectada. A las
17:36, las consultas normales 0/1/21/36 seguían completándose correctamente;
el bloqueo de ADC no detuvo la política normal del cargador. Estado: 39 %,
29 °C, sin pareja USB. Capturas privadas: `/var/lib/eqs-usb-adc/` en el teléfono.

**Control alimentado, 17:55:52 ART:** Eduardo dejó hub + dongle + PD conectados
después de varios intentos. El journal registra esas desconexiones; no atribuirlas
a cortes espontáneos. Tras el reinicio temporal de las 17:52, se verificaron
hub, receptor `usbhid` y LAN enumerados, host/sink, PD online, 40 % y 29 °C.
Las lecturas normales completaban correctamente antes de una única consulta ADC:
49/40 bytes → respuesta de 84 bytes con propiedad cero y `data_size=0` en unos
0,79 ms → `ENODATA`. No hubo lectura de voltaje ni reintento. Las consultas
normales 0/1/21/36 y los dispositivos USB continuaron después del error.
Las 14 capturas de este control se recuperaron y verificaron por SHA-256 en
`.work/eqs-usb-adc-wire.8437112q/powered-target/`.

**Se cierra esta vía ADC:** no resetear el latch, cambiar IDs al azar ni dejar un
sondeo permanente. Hace falta medir VBUS externamente durante una conexión fría
para separar alimentación ausente/inestable de inicialización de datos con
tensión presente. No reinstalar la distribución ni escribir particiones de
arranque. Con el helper deshabilitado y el marcador ausente, a las 17:57 ART se
solicitó un reinicio normal. A las **17:59:42 ART quedó verificado H29 original**
(`148f1c4c…`), sin interfaz ADC ni ejecución del helper. SSH/Plasma/LXC seguían
activos, con hub/receptor/LAN enumerados y carga PD (41 %, 29 °C). No hubo
fallos de lectura normales en el journal capturado. Evidencia de retorno:
`powered-target/powered-h29-return-*`, también recuperada y verificada.

El control directo mediante adaptador USB-C–USB-A simple sigue **sin confirmar**;
no usarlo como otra prueba fallida. Análisis reproducible, privado y sin acceso
al teléfono: `python3 .work/eqs-usb-hub/source-ssh/analyze-empty-hub.py`.
Pasaron sus comprobaciones de decodificación/longitud y completitud de esta
captura. No son un test eléctrico ni una corrección de alimentación instalada.

### Diagnóstico nativo por SSH: alimentación, no otro flash

- Con el hub conectado sin PD, Type-C y DWC3 están en host/source; el modo
  Type-C informado es **1,5 A**, sin pareja PD. Sólo aparecen las raíces USB.
- El cargador informa `chrg_otg_enabled=1`, 5200 mV, LPD=0 y nivel térmico 0.
  La batería está al 80 %, 29 °C y estado `Good`. `force_usb_suspend` se leyó
  como 0. No confundir los límites de **entrada** en cero con un límite de
  corriente de salida OTG, ni la telemetría con tensión medida en el hub.
- El backend de logs realmente disponible es Motorola `bm_adsp_ulog`, con
  `/sys/kernel/debug/bm_ulog/dump` e IPC `bm_ulog`; no está expuesto
  `/sys/kernel/debug/charger_ulog`. El dump solicita logs al firmware y reaplica
  el filtro existente: no habilita VBUS ni cambia voltajes/corrientes.
- La captura ampliada de 600 segundos terminó a las 18:11 ART: 591 muestras,
  con desconexiones a los 6020, 6027, 6076 y 6086 segundos de uptime y conexiones
  intermedias a los 6021, 6030 y 6078. Eduardo confirmó haberlas realizado;
  **no son evidencia de cortes espontáneos**. No enumeró ningún dispositivo externo.
- El firmware registra `SourceVbus=1, Voltage=5200 mV` y apagados con
  `SourceVbus=0`; también aparecen `FaultSts=0` y OTG activado. Se observan
  errores I²C del componente inalámbrico CPS, pero no se demostró que causen el
  fallo USB. Solicitar 5,2 V no prueba entrega en el conector bajo carga.
- Al finalizar, el puerto indicaba `none`/sink, coherente con la última
  desconexión. El capturador terminó por su timeout; no quedó un servicio nuevo.
  No se modificaron roles, política PM, kernel ni firmware.

Código contrastado: `bm_adsp_ulog.c`/su README y `qti_glink_charger.c` del árbol
Motorola fijado, además de `ucsi.c` del kernel eqs. Evidencia privada copiada y
verificada por SHA-256 en `.work/eqs-usb-hub/source-ssh/`: firmware, journal e IPC
UCSI. La captura local de firmware tiene SHA-256
`0c12f448b212316fd8e4477607f9018962dd754f6881ed364a13aabc86eccb50`.
Esa captura no localizó la causa del fallo al conectar sin alimentación externa.

**Corrección host del diagnóstico, no del suministro USB:** el builder invocaba
Kbuild directamente, omitiendo `CONFIG_WIRELESS_CPS4035B=m`, que el Makefile
Motorola selecciona para eqs. El módulo instalado muestra el formato genérico
con campos PEN/FOLIO. Ambos structs miden 60 bytes, pero `usb_otg` está en offset
50 para CPS4035B y 52 para el genérico: OTG=1 se muestra como `PEN_ERROR=1` y
`USB_OTG=0`. No interpretar ese cero como falta de orden OTG. La corrección agrega
la opción al comando existente, sin cambiar código de control de potencia.

Regresión RED/GREEN en `test-eqs-config.py`: 11 tests aprobados; el Kbuild fijado
selecciona `-DWIRELESS_CPS4035B` con la opción y no lo hace sin ella. También pasan
los 18 checks USB del modelo host. **En esa etapa no se recompiló ni reemplazó
el módulo**; el candidato ADC posterior sí incluye la corrección, sólo en host.
No reiniciar ni flashear solamente para corregir una etiqueta de log.

**Corrección de la prueba de las 18:33 ART:** Eduardo aclaró después que el hub
estaba desenchufado. Por tanto, `screen-wake.txt` (84 muestras con sink/none,
incluyendo 46 con panel encendido) **no es una prueba válida del hub conectado**
ni evidencia de un fallo de detección Type-C. Queda sólo como registro histórico.

Eduardo confirmó la conexión posterior y que el teclado sigue sin responder.
Coincide con el attach de las 18:39:45 (uptime 8240 s), sin cambios del agente en
roles ni drivers. A las 18:44 seguía host/source, 1,5 A, pareja sin PD, 5200 mV
informados y sólo raíces USB. No estaban activos los modos factory/demo,
suspensión de cargador o deshabilitación de carga; son lecturas, no ajustes.
Con el hub realmente conectado se repitió el despertar: a las 18:45:17 y
18:45:22 el panel estaba encendido (brillo 2756), host/source seguían activos y
sólo aparecían raíces USB. `attached-screen-wake.txt` conserva ese control válido;
encender la pantalla por sí solo tampoco resolvió este caso conectado.

### Control con PD y cambio negociado de alimentación

**Control con PD completado a las 18:50:13 ART**, sin mover el cable
hub–teléfono. Eduardo confirmó que el teclado responde. Captura por SSH:

| Componente | Identificación y driver |
|---|---|
| Hub USB2, cuatro puertos | `214b:7250`, `hub`, 480 Mb/s |
| Receptor RF compuesto | `1915:1025`, `usbhid` + `snd-usb-audio`, 12 Mb/s |
| Ethernet 10/100 | `1a86:e397`, `cdc_ether` |
| Billboard del adaptador AV | `343c:0000`; no requiere driver para el teclado |

Type-C y DWC3: datos **host**, potencia **sink**, pareja con PD. La raíz USB3
no tiene hijos: no asumir hub SuperSpeed ni Ethernet gigabit. El teléfono
informa entrada de 4,571 V/550 mA y batería en `Charging`, 29 °C; no es una
prueba de carga sostenida. El descriptor `Self Powered` con PD conectado
tampoco demuestra que el hub necesite siempre alimentación externa.

**A las 18:57:19 se ensayó sink → source → sink mediante la interfaz normal
`power_role`**, con pareja PD comprobada, SSH por Wi-Fi y sin almacenamiento USB.
Ambas solicitudes devolvieron 0; se restauró sink a las 18:57:21 y todos los
dispositivos siguieron enumerados. El firmware informa `VbusPresentStatus=1`
y `SourcingVbusStatus=1` durante source. **PD permaneció conectado: esto prueba
la negociación, no que el teléfono pueda alimentar el hub sin ayuda.** No se
modificaron tensiones, límites de corriente, registros PMIC ni protecciones.

Evidencia privada copiada y verificada por SHA-256 en
`.work/eqs-usb-hub/source-ssh/`: `powered-control-*`, descriptores,
`pd-swap-result.txt` y `pd-swap-firmware.txt`. El resultado del swap tiene hash
`e1cfb3c49f7570c4d56ed78c39c922cbb7f70ed007acb392ce87f9ed52f8e743`.

**Control exitoso, preparado a las 19:04:53:** se negoció source otra vez
(retorno 0, hub y receptor presentes) y se dejó seleccionado **antes de retirar
sólo PD**. Eduardo confirmó: «sigue funcionando sin alimentacion externa».
A las 19:14:15, SSH mostró batería `Discharging`, entrada USB `online=0`,
host/source, panel encendido y hub/receptor/LAN presentes. Que la pareja siga
anunciando capacidad PD no significa que el cargador externo siga conectado.

La captura tuvo 672 muestras entre 19:04:53 y 19:16:25, todas con el receptor
presente, incluyendo panel encendido y apagado. **La hora exacta en que Eduardo
retiró PD no consta**: no atribuir toda la captura al funcionamiento sin cargador
ni equiparar panel apagado con suspensión del sistema. Se detuvo el capturador
a las 19:16:26; no quedó servicio nuevo y no se cambió el rol de potencia.
Los cinco archivos `pd-handoff-*` se copiaron y verificaron por SHA-256; la captura
tiene hash `ed3d5727e2aac1825a38625044b306dd81f2a06fa041f34bcfcd840fac9798ee`.

**Límite de esta solución provisional:** `SET_PDR` sólo aplica a la conexión PD
actual y se restablece al desconectar la pareja o reiniciar el controlador,
según [UCSI §4.5.10](https://www.intel.cn/content/dam/www/public/us/en/documents/technical-specifications/usb-type-c-ucsi-spec.pdf).
Además, el driver fijado no envía otra orden si ya informa source. Por eso una
regla que escriba source al arrancar no demuestra ni resuelve el caso frío.
La reconexión posterior sin PD falló, como consta abajo; no automatizar esta
recuperación como si resolviera el inicio de una conexión nueva.

A las 19:17 se observó desconexión USB (uptime 10460,400 s) y reenumeración
completa (hub desde 10461,140 s), con nuevos números de dispositivo y
host/source aún activo. El agente no cambió roles ni drivers. Eduardo observó
que se apagó la pantalla, pero aclaró que también pudo haberse movido el cable.
La causa queda sin confirmar: no contar este evento como una reconexión física
validada ni como un corte espontáneo. En el journal, el brillo llega a cero a los
10487,424 s, unos 27 s **después** de la desconexión USB: tampoco demuestra que
el apagado del panel causara ese reinicio del hub.

### Reconexión sin PD: fallo confirmado, no solución persistente

Eduardo realizó la prueba explícita de desconectar hub–teléfono y reconectar
sin PD: el teclado no respondió. El journal conserva la desconexión a las
**20:34:47 ART** (uptime 15142,406 s), apagado del host y nuevo inicio a las
**20:34:54** (15149,344 s), sin enumerar después el hub. UCSI registra ambos
eventos; no se perdió la detección de conexión Type-C.

SSH a las 20:36:04 confirma pantalla encendida (brillo 1157), host/source,
modo **1,5 A**, pareja **sin PD**, únicamente raíces USB y batería descargando
a 29 °C. La lectura de 5200 mV sigue siendo telemetría, no una medición del
conector. El resultado delimita el fallo al inicio de la conexión sin ayuda;
no identifica todavía si es la secuencia de potencia, una caída bajo carga u
otro problema del arranque del hub.

**Cobertura real:** `cold-reconnect-capture.txt` terminó por su límite de 900 s
a las 19:36:26, antes de esa reconexión. Sus 873 muestras corresponden al estado
anterior y **no capturaron la transición de las 20:34**. El resultado se sostiene
en el reporte del usuario, journal persistente, IPC UCSI y lectura actual; el
dump puntual de firmware posterior quedó vacío. No inventar trazas del borde
que faltan ni pedir repetir una prueba idéntica sin una nueva hipótesis.

Los cinco archivos `cold-reconnect-*` se copiaron y verificaron por SHA-256.
Journal: `75552e96da51fdee0e71c540967d67939ec32de929401c90abe309aa8be0e8eb`.
Estado: `49a08fd4b41ada2dc771b82fb8b48417a8e11cc228c74c62779e59210bca8dab`.
No quedaron capturadores activos; no se modificaron roles, PM, kernel ni firmware
durante esta comprobación.

**Recuperación provisional:** Eduardo volvió a alimentar el hub por PD.
A las 21:07:04 se verificó host + sink + pareja PD, receptor `usbhid`, SSH por
Wi-Fi, sin almacenamiento USB y batería a 29 °C. A las **21:08:04** se solicitó
source mediante la interfaz estándar: retorno 0, host/source, entrada USB
`online=0` y mismos dispositivos presentes. Se dejó source seleccionado y se
pidió retirar sólo PD. El 8 de septiembre Eduardo respondió «listo» y pidió que
el arranque sea automático sin alimentación externa. SSH a las 07:21 ART mostró
host/source, entrada USB `online=0`, batería descargando a 29 °C y hub/receptor
presentes. No hubo una nueva confirmación de pulsaciones ni captura continua
durante la noche: los números USB cambiaron a hub 7/receptor 8. El journal
recuperado sólo cubre desde aproximadamente las 03:52 ART, no toda la noche.
En esa recuperación no quedaron servicios ni capturadores nuevos. Registro privado
`pd-recovery.wHVFRx.txt`, SHA-256
`8ec772cb87a0721db110375bad413dca5c24c85f4f4e668e30875319af4acd15`.
No automatizar esta recuperación como si resolviera la conexión inicial sin
cargador, ni forzar swaps con pareja sin PD.

**Control del hub vacío: fallo confirmado el 8 de septiembre.** Eduardo respondió
«listo» al pedido de conectar únicamente el hub, sin PD ni receptor/periféricos.
La captura detectó desconexión a las 07:42:31 ART y nueva conexión a las 07:42:53;
terminó con `COMPLETE` a las 07:43:53. Las 430 muestras muestran host/source,
modo 1,5 A, pareja sin PD y únicamente raíces USB: no apareció el hub. En 319
muestras el panel tenía brillo distinto de cero; en las otras 111 estaba apagado.
El fallo ya estaba presente con la pantalla encendida. Batería a 29 °C.

El firmware registra `SourceVbus=1`, solicitud de 5200 mV y `FaultSts=0`;
ninguna de esas lecturas sustituye una medición eléctrica en el conector.
El fallo no requiere la carga del receptor, pero aún puede depender del arranque
de la electrónica del hub o de la ruta de alimentación del teléfono. Se preguntó
si hay un adaptador OTG simple disponible para comparar el receptor conectado
directamente; no pedir otra reconexión idéntica del hub como solución.

El capturador terminó y no quedaron procesos activos. No se escribieron roles,
PM, registros ni firmware, ni se instaló una unidad/regla de alimentación. Los
cuatro archivos `empty-hub-{capture,kernel,result,ucsi}.txt` se copiaron a la carpeta
privada de evidencia y sus SHA-256 coinciden con el teléfono. Captura:
`7f1ac85d6bbb88122efd27ef552bf030c95fe62cdab1ac212df8c94ff40cba8b`.
Las reenumeraciones observadas antes de la desconexión Type-C coinciden con la
manipulación del ensayo; no se atribuyen a un fallo espontáneo.

La revisión adicional de fuentes encontró telemetría ADC de switched-capacitor
en `qti_glink_charger`, pero compilada sólo con `SWITCHEDCAP_DUMP`; no está
expuesta por el módulo actual. Activar `debug_enabled` no la incorpora. Tampoco
se debe usar `wireless_fw_update` como interruptor OTG: escribe firmware. El
archivo `cps4035.bin` existe y la versión inalámbrica devuelve `0x0` también con
el hub funcionando; esos datos no identifican por sí solos la causa. No se
compiló ni cargó un módulo nuevo durante esa revisión inicial. El candidato ADC
posterior está descrito arriba; aún no se instaló.

### Antecedentes sin alimentación PD

Eduardo reporta el hub como el problema restante de su uso actual. El teclado es
un **MRSVI A8 inalámbrico con receptor USB RF de 2,4 GHz**, no un teclado cableado.
Confirma que **el mismo hub y receptor funcionan en otra computadora y en otro
Android sin cargador externo**. El hub tiene entrada PD opcional; no tratar su
ausencia como requisito incumplido ni repetir esas comparaciones. Modelo del hub
y VID:PID del hub/receptor aún desconocidos. Las fotos de `dmesg` no conservaban
una conexión identificable del hub. La sesión posterior en recovery recuperó el journal
nativo completo. Se restauró H29 A sin reinstalar la raíz ni tocar B.
La prueba posterior de Eduardo confirma que **reiniciar con el hub conectado
tampoco lo hace funcionar**. No repetir ese paso como solución ni atribuirlo
sólo a conexión en caliente.

Las fotos posteriores muestran:

- `lsusb -t`: sólo raíces `dummy_hcd` (480M) y `xhci-hcd` (480M/10000M), sin
  hub externo ni teclado. Es registro del controlador host, no velocidad de un
  dispositivo conectado ni prueba de alimentación VBUS efectiva.
- Type-C: `data_role=[host] device`, `power_role=[source] sink`. Son dos
  capturas separadas, no una traza continua de la conexión.
- El intento de consultar DWC3 usó `/sys/class/usb_role/*_role`, no `*/role`.
  Ese error de ruta no demuestra que falte el role-switch.
- Con la ruta corregida, Eduardo aclara que la foto de las 17:30 era **sin
  hub**: Type-C host/sink y DWC3 `none`. No es una falla del rol con hub conectado.
- La nueva foto de las 17:40, **con hub conectado**, muestra en la misma consulta
  Type-C host/source y DWC3 `host`. No hace falta repetir ni forzar esa selección.

El foco en esas capturas era **por qué no enumera el hub**, antes de HID/Plasma. La hipótesis
de quedar permanentemente en modo periférico no explica la última captura.
El rol host ya está confirmado; la causa de la falta de enumeración, no.

- La configuración H29 incluye xHCI, DWC3 dual-role, OTG y USB HID/genérico;
  no deshabilita hubs externos. No falta simplemente activar el driver de teclado.
- `eqs-usb-rndis` prepara el teléfono como periférico para la PC, no como host.
  Rechaza un rol Type-C host y no gestiona hotplug; su presencia es una pista,
  **no prueba de que esté bloqueando el hub**. UCSI puede cambiar el rol después.
- Pasan los 18 checks existentes de ciclo de vida USB en archivos simulados:
  `python3 port/bringup/diagnostics/test-usb-rndis.py`. No validan el hub físico.

Mantener sólo hub y receptor, sin discos ni Ethernet. La prueba de reinicio con
hub ya falló: no repetirla como solución. La comparación con otro Android sin PD
prioriza un problema del port o su compatibilidad USB, sin demostrar por sí sola
la tensión real del eqs. No forzar `host`, VBUS ni el rol de alimentación a ciegas.

### Qué dicen los nuevos logs

- `runtime idle`, `runtime suspend`, `could not transition HS PHY to L2` y
  `DWC3 in low power mode` muestran una transición de ahorro de energía. En el
  kernel H29, `dwc3_msm_prepare_suspend()` imprime el aviso L2 y devuelve cero:
  **no es por sí solo un fallo fatal ni prueba de la causa del hub**.
- `unexpected PWR_EVNT, irq_stat=241000` también aparece en la captura nativa
  H29 trial6 junto a conexión USB y enlace gadget listo. No distingue este fallo.
- `USB_OTG: 0` proviene del dump de carga inalámbrica, no del rol DWC3. La
  revisión por SSH confirmó además el formato CPS4035B mal seleccionado
  descrito arriba: ese campo está desplazado y no informa el OTG real.
- El filtro anterior `usb|xhci|dwc3|vbus|redriver` seguido de `tail -30`
  seleccionó muchos dumps periódicos por `USB_OTG` y descartó eventos anteriores.
  No reutilizarlo como captura suficiente del enchufado.

Fuentes locales: kernel `bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582`,
`drivers/usb/dwc3/dwc3-msm-core.c` y `drivers/base/power/sysfs.c`; módulos
`9f8d247d457622c08ff547e5498e6fa453e876ed`,
`motorola/drivers/power/qti_glink_charger/qti_glink_charger.c`.

### Lectura directa y prueba automática instalada

El 6 de septiembre se leyó la raíz con `ro,noload` desde el rescate A conocido.
El último journal nativo confirma host/xHCI al arrancar y al reconectar a los
1399 segundos, **sin eventos de dispositivos externos ni intentos de leer sus
descriptores**. A los ~1,3 segundos vuelve a runtime suspend. El helper RNDIS
había rechazado ese arranque en host, sin enlazar el gadget.

También falla el probe de PS5169 `1-0030` con `-107`; en recovery stock falla
con `-22` y queda sin driver enlazado aunque ADB USB2 funciona. Es una pista
para SuperSpeed, no una explicación demostrada del teclado USB2. No reprobar
ese driver en bucle ni inventar una alimentación `vio` por el aviso opcional.

### Resultado del ensayo conectado: el padre no despierta xHCI

Se recuperó el boot `cda8d02495984a2ab66646c5c06ffae9` desde recovery con la
raíz `ro,noload`. A los 148,6 s, Type-C/DWC3 indicaban host/source y las tres
capas estaban suspendidas. `APPLIED on` despertó **sólo el padre**: DWC3 y
xHCI siguieron suspendidos en todas las muestras hasta los 269,37 s, sin hub
externo. `RESTORED auto` a los 269,38 s confirma la restauración. Coincide con
el teclado sin respuesta que informó Eduardo; **no descarta todo runtime PM**.
Evidencia privada: `.work/eqs-usb-hub/result-1/{trial,kernel}.txt`.

### Resultado USB2: mantener activo el host no resuelve la enumeración

El ensayo iniciado a **22:34:23 UTC** terminó; Eduardo informó que el teclado
sigue sin responder y devolvió el equipo en Fastboot. Se leyó el boot
`17e19f08d16d424a9fa230cc29ece78f` con raíz `ro,noload`:

- `APPLIED on` a los 178,82 s. Raíz USB2, xHCI, DWC3 y padre permanecieron
  **activos** en todas las muestras hasta los 279,50 s, con host/source,
  pero sólo aparecieron las raíces internas: ningún hub externo ni descriptor.
- A los 284,98 s el kernel pasó a rol `NONE` y eliminó el controlador; el helper
  terminó a los 289,51 s con `DEVICE_GONE`, sin escribir sobre su sustituto.
  Hubo otra conexión a los 289,87 s, fuera de esta comparación.
- A los 254,97 s el driver real de carga informó `chrg_otg_enabled=1` y
  `chrg_mv=5200`. Es distinto del dump inalámbrico `USB_OTG: 0`; no es una
  medición independiente de tensión en el hub ni de su alimentación downstream.
- Los parámetros de repeater NXP leídos del DT stock coinciden con H29:
  host `40:06, 22:07, 24:08`, device `40:06, 22:07, 64:08`.

**No rearmar este ensayo ni instalar un override permanente de autosuspend.**
Mantener despierta la jerarquía USB2 no bastó. Esto no descarta todo fallo de
inicialización/PHY, pero no justifica repetir PM, forzar VBUS o modificar la
calibración. El marcador ya fue consumido; en el siguiente arranque la unidad
no aplica ajustes. Evidencia privada: `.work/eqs-usb-hub/result-2/`.
Tras recuperar los logs se desmontó la raíz y se restauró H29 A con hashes
verificados y reintentos restablecidos; reinicio normal solicitado a
**22:53:52 UTC**, sin rearmar la prueba ni modificar archivos de la raíz o B.

### Investigación de código tras confirmar el receptor RF

**El fallo observable precede al teclado:** falta el hub externo en la enumeración.
No hay evidencia para agregar un driver RF, cambiar Plasma o ajustar emparejamiento.
El transporte USB debe existir antes de inspeccionar los informes HID del receptor
([documentación HID de Linux](https://docs.kernel.org/hid/hidintro.html)). La marca
A8 no identifica por sí sola el chipset o VID:PID; no inventar un quirk del receptor.

Se compararon los árboles limpios eqs `bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582`
y Bronco `3d1ed931716f88d002207b03db5f0a77e762b921`:

- Bronco incluye el [cambio Qualcomm `d495a25`](https://github.com/droidian-devices/linux-android-lenovo-bronco/commit/d495a25ad3c4e4cabfc071bc5dbc337b44068899):
  `udelay(10)` tras afirmar POR en `msm_eusb2_phy_init()`. Su justificación es
  mantener el reset al menos 10 microsegundos después de estabilizar las fuentes.
  El árbol eqs no incluye ese retardo explícito. En esta revisión inicial era una
  hipótesis sin ensayo; **POR1 se probó después y no resolvió el fallo** (abajo).
- `repeater-i2c-eusb2.c` y `ucsi_glink.c` son idénticos entre ambos árboles.
  No copiar todo el driver PHY de Bronco: también contiene cambios EUD y un
  override de corriente RNDIS ajenos a esta hipótesis. Nunca flashear Bronco.

El plan de comparación, ya ejecutado abajo, agregó **estado del puerto USB**,
sin repetir el ensayo PM.
[`lsusb` verbose, `do_hub()`](https://github.com/gregkh/usbutils/blob/master/lsusb.c)
ya consulta `GET_STATUS` y muestra conexión, habilitación, reset y sobrecorriente.
Usarlo de forma acotada sobre la raíz xHCI identificada, junto con eventos del
enchufado e interrupciones. La ruta usbfs del kernel gestiona resume y referencias;
la consulta puede despertar el dispositivo. Evitar lecturas MMIO a ciegas del
`portsc` debugfs: su lector local no toma una referencia PM y escribirlo puede
activar el modo de compliance.

Con esa observación, evaluar un único candidato eqs con el retardo Qualcomm aislado,
kernel/módulos coherentes y rescate H29, sin reinstalar la raíz ni tocar Plasma o B. Comparar
no sólo las teclas: primero conexión/reset del puerto, luego hub, receptor y eventos
de entrada. **Esta investigación no modificó ni flasheó el teléfono ni rearmó pruebas.**

### Candidato USB POR1: compilación y ensayo

La configuración efectiva H29 declara `CONFIG_USB_MSM_EUSB2_PHY=m`: no hace falta
recompilar el kernel. Se compiló el módulo aislado con el parche versionado
`port/kernel/patches/0001-eusb2-por-delay.patch`, la misma toolchain ThinLTO+CFI,
configuración y símbolos H29. Al compilarse externamente pierde las etiquetas
`intree`/`scmversion`; conserva nombre, alias, dependencias, vermagic y CRC de imports.
No se fuerza su carga ni se alteran verificaciones de ABI.

- Bundle local: `.work/eqs-usb-hub/por-candidate/boot-bundle/`.
- `candidate/vendor_boot.img`: SHA-256
  `e9ea0e9b7ab1f7957ef740feacf95721094538c6d08c10283cf73518a0e452b8`.
- Comparación completa de ramdisks: **sólo cambia `phy-msm-snps-eusb2.ko`**.
  Dos empaquetados idénticos; 369 módulos pasan controles CRC y dependencias.
  `boot`, DTBO, vbmeta y rescate permanecen idénticos a H29.
- Desensamblado ARM64: el candidato agrega la llamada `udelay(10)` donde corresponde;
  la compilación baseline no la contiene. Esto no mide el tiempo real del PHY.

Se reutilizó `eqs-usb-host-test` como **captura de puertos**, eliminando todas las
escrituras de política PM. Espera host hasta 15 minutos y toma 13 muestras acotadas;
registra boot ID, hash del módulo, roles, interrupciones y estado del puerto.
Se detiene si cambia el rol/controlador o falla la consulta. No confunde un
`lsusb` con exit 0 pero sin estado del puerto con una captura válida.

RED: la versión anterior cambiaba PM y luego una primera implementación aceptaba
la salida incompleta. GREEN: 16 escenarios + contrato de unidad; además pasan los
18 checks RNDIS y los mocks del flasher. `sh -n` y validación de unidad en host
(ruta del ejecutable mapeada) pasan. Logs en `.work/eqs-usb-hub/por-candidate/`.

**Preparación inicial de la referencia H29, antes de instalar POR1:**
Con el teléfono autorizado en Fastboot se entró a la recuperación stock conocida,
se guardó pstore con montaje comprobado y se inspeccionó la raíz `ro,noload`.
Se respaldaron el helper PM y su unidad; se reemplazaron sólo esos dos archivos
y se armó `.once` después de validar sintaxis y unidad con los binarios ARM64.
La captura canónica y el identificador H29 conservan sus hashes; los servicios de
retorno automático siguen desactivados. Se sincronizó/desmontó la raíz y se restauró
el conjunto **H29 original** en A, con sus intentos de arranque reiniciados.

- Helper instalado: SHA-256
  `f87655304998d8f2e454ff687c7e46541f4c08f04cb4112bc83ad1f8e7794d4a`.
- Los 17 checks de captura en host se repitieron y pasaron; todavía no prueban el hub.
- Evidencia privada: `.work/eqs-usb-hub/por-candidate/baseline-session/`.
- Medición prevista, ya completada abajo: arrancar Plasma, conectar hub/receptor sin PD durante tres minutos
  dentro de la ventana de 15 minutos y devolverlo en Fastboot con cable directo.
  No pedir comandos táctiles. Recuperar `USB_PORT_CAPTURE` antes de comparar POR1;
  esta captura no aplica el parche ni intenta reparar el hub.

No hubo wipe, reinstalación de raíz, cambios B ni habilitación de acceso remoto.

**Rearme del 7 de septiembre:** Eduardo no realizó la medición anterior. Se
verificaron los hashes instalados y se recreó sólo `.once`, conservando helper y
unidad. Validación ARM64 de sintaxis/unidad aprobada y H29 original restaurado en A.
En ese momento la medición seguía pendiente y POR1 no estaba instalado. Evidencia:
`.work/eqs-usb-hub/por-candidate/rearm-20260907-0917/`.

**Referencia USB2 completada:** el arranque
`94ab4f3960ea49a8a24f846257edc21d` produjo las 13 muestras y `COMPLETE` entre
198,89 y 321,51 segundos. Todas devuelven `Port 1: 0000.0100 power`, sin bits de
conexión, habilitación, reset ni sobrecorriente. Type-C permanece host/source y
DWC3 host; sólo aparecen raíces USB. Las IRQ xHCI no aumentan durante la captura.
El bit de alimentación **no demuestra el voltaje VBUS en el hub**. El problema
sigue antes de HID/Plasma; esta referencia por sí sola no evaluaba el retardo POR1.
La desconexión a los 334,90 segundos ocurrió después de completar la captura.

Logs completos en `.work/eqs-usb-hub/por-candidate/baseline-result/`:
`capture.txt`, `kernel.txt`, pstore y preflight. Se obtuvieron sobre una vista
consistente tras el replay normal de ext4; no hubo fsck ni reparación/borrado del journal.
El módulo H29 observado tiene SHA-256
`7ba72319644cadb3725bedd2e7f1be56ea7b07aea2d1ccd47409b0ece448095c`.

**POR1 flasheado con autorización explícita el 7 de septiembre:** se reutilizó
la captura preparada, con hashes y validación ARM64 conservados. Antes de escribir,
A conservaba siete intentos y `successful:no`, sin un arranque intermedio.
Se verificaron íntegramente candidato y respaldo H29. Fastboot confirmó las cuatro
escrituras de A y el restablecimiento de intentos; `boot`, DTBO y vbmeta siguen
idénticos a H29. Sólo cambia el módulo USB2 en `vendor_boot`. Sin cambios en raíz/B.

El módulo esperado para ese arranque tiene SHA-256
`09577aec4fc5df275823228ec05f4d92fa727f297bb9f73233b479abfbe411f2`.
Logs y hora de arranque solicitado: `.work/eqs-usb-hub/por-candidate/por1-trial/`.
El bundle original `.work/eqs-h29/boot-bundle/` conserva la recuperación conocida
y el retorno a H29; no confundir el rescate stock para ADB con el sistema H29.

### Resultado POR1: módulo cargado, hub todavía sin detectar

El boot `61756e40e179483082713f6e0b85e60a` completó las 13 muestras entre
574,47 y 697,16 segundos. **Todas repiten `Port 1: 0000.0100 power`**, con
Type-C host/source, DWC3 host e IRQ xHCI sin cambios; no aparece el hub externo.
El módulo tiene el hash esperado, el initramfs registra `MODULE OK` y la lista
nativa incluye `phy_msm_snps_eusb2(O)`, consistente con la compilación externa
POR1. No fue simplemente un archivo copiado sin evidencia de carga.

El hub se desconectó a los 1395,58 segundos: la captura no perdió su ventana.
Eduardo confirmó que el teclado seguía sin responder. **El retardo aislado de
10 µs no bastó; no repetir POR1 ni presentarlo como solución.**

Se recuperaron los journals tras el replay normal de ext4, se comprobó que `.once`
ya estaba consumido y se desmontó la raíz. H29 original quedó restaurado en A;
Fastboot aceptó el reinicio normal a **10:33:05 UTC del 7 de septiembre**, sin
rearmar pruebas, reinstalar la raíz ni escribir B. Esto no verifica la pantalla
del arranque final. Evidencia: `.work/eqs-usb-hub/por-candidate/por1-result/`
(`capture.txt`, `kernel.txt`, `restore-h29.txt` y `reboot-h29.txt`).

**Pistas anteriores al resultado con PD, sin implementar:** observar inicialización
USB2, clocks, repeater y estado EUD durante el paso a host. H29 tiene
`DYNAMIC_DEBUG_CORE=y`, pero no `DYNAMIC_DEBUG`; antes de usar `dev_dbg`, verificar
los puntos de depuración compilados. No usar `apb_reg_rw` como lector: es escritura.
La revisión de fuentes no justifica copiar otros cambios Bronco ni activar
FSA4480: los overlays eqs de audio/display lo deshabilitan. La recovery stock
tampoco está lista como control host: en esta lectura no expuso roles Type-C.
Se pidió el modelo del hub sin repetir las pruebas ya hechas en otro Android.

### Foco actual: alimentación del hub desde el teléfono

La lectura del código fijado ubica las responsabilidades:

- `ucsi.c:ucsi_pr_swap()` solicita el rol de potencia mediante `UCSI_SET_PDR` y
  `ucsi_glink.c` lo transporta al firmware por PMIC GLINK. Si el rol ya es `source`,
  volver a escribirlo no hace esa solicitud: **no es un interruptor de VBUS**.
- `dwc3-msm-core.c:dwc3_otg_start_host()` inicia controlador/PHY de datos; no
  contiene una habilitación del regulador VBUS. No agregar una a ciegas.
- `qti_glink_charger.c:qti_charger_get_chg_info()` obtiene `chrg_otg_enabled` y
  tensión mediante `OEM_PROP_CHG_INFO`. La referencia sin PD informó OTG=1 y
  5200 mV, pero no hubo medición independiente en el hub. Inicialización ROW/
  revisión de hardware y LPD=0 constan en ese journal; no hay evidencia para
  alterar identidad de placa o desactivar protecciones.

Fuentes: kernel eqs `bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582` y módulos Motorola
`9f8d247d457622c08ff547e5498e6fa453e876ed`, en las rutas USB/power indicadas arriba.
H29 ya carga `charger-ulog-glink.ko`: existe soporte de logs del firmware de carga
sin recompilar el kernel. Preparar una captura acotada de roles, alimentación,
eventos UCSI/carga y enumeración; no reutilizar sólo `GET_STATUS` como voltímetro.

Se pidió una observación sin comandos: retirar sólo PD manteniendo el hub unido
al teléfono y ver si el teclado sigue respondiendo. Puede haber un reinicio del
hub durante el cambio de fuente: una caída inmediata no distingue por sí sola
ausencia permanente de VBUS de una mala transición. Si hace falta medir tensión
real, usar instrumental USB adecuado, no sondear pines ni escribir registros.
No se modificó ni flasheó el teléfono por este nuevo reporte. El workaround con
PD no convierte la alimentación externa en requisito definitivo del cyberdeck.

### Cómo funcionaba el experimento PM USB2 (histórico, ya finalizado)

- `eqs-usb-host-test.service` consume un marcador `.once` antes de ejecutarse.
  Usa `Type=simple`: esperar el hub no debe bloquear el arranque gráfico.
- Espera hasta 15 minutos por Type-C **y** DWC3 en host. No fuerza ese rol.
- Selecciona la única raíz USB2 `1d6b:0002` bajo el xHCI de `a600000.ssusb`.
  No modifica `dummy_hcd`, la raíz USB3 ni las políticas de sus padres.
- Guarda su `power/control`; sólo cambia `auto → on` y comprueba `active` en
  raíz USB2, xHCI, DWC3 y padre. Registra roles/runtime PM/`lsusb -t` durante
  unos dos minutos y restaura el valor original. Si no se confirma resume,
  registra el estado y restaura sin seguir la comparación.
- Fija el directorio de trabajo al objeto elegido antes de escribir rutas
  relativas: no escribe sobre otro dispositivo que reutilice el mismo nombre
  al desconectar. La pérdida de host o del objeto termina el ensayo.
- No cambia kernel, PD, VBUS ni suspensión global; no reinicia el teléfono.
  Puede aumentar el consumo durante la comparación. TERM/INT restauran el valor;
  SIGKILL o un bloqueo del kernel no permiten garantizar esa limpieza. El cambio
  de sysfs no persiste al reiniciar.
- Ya configurado en `on`, rol ausente, raíz ausente/ambigua, kernel distinto o política inválida:
  no aplicar otra política. `flock` impide dos instancias propias simultáneas.

Al aparecer Plasma, conectar sólo hub/teclado y mantener la pantalla despierta,
sin cambiar PD a la vez. Probar entrada inicialmente y a los 10 segundos.
Mantener **la misma conexión tres minutos**; reconectar termina esta comparación
y no la rearma. No pedir comandos en el teclado táctil.
La primera ventana (arranque 21:44:17 UTC) venció sin conexión: el journal
confirma `WAIT_HOST` a los 5,44 s y `NO_HOST; unchanged` a los 901,83 s. No fue
un ensayo fallido del hub ni modificó PM.

Eduardo pidió reactivarla sin escribir comandos en la pantalla táctil. Se recreó
sólo el marcador desde recovery, conservando los hashes de helper/unidad/captura;
se restauró H29 A y se solicitó el nuevo arranque a **22:10:37 UTC**. Esa prueba
ya terminó; su resultado está arriba. Evidencia de rearme:
`.work/eqs-usb-hub/rearm-20260906-2207/`.
Reiniciar por sí solo no rearma el marcador consumido. Si hay acceso nativo
autorizado, recrearlo y reiniciar el servicio evita el paso por recovery y
conserva los logs; no pedirle otra vez a Eduardo que transcriba comandos largos.

Los logs automáticos quedan en el journal persistente:

```sh
sudo journalctl -b -u eqs-usb-host-test.service --no-pager
```

Archivos instalados nuevos: `/usr/local/sbin/eqs-usb-host-test`, su unidad en
`/etc/systemd/system`, enlace en `multi-user.target.wants` y marcador
`/etc/eqs-usb-host-test.once`. Para retirar la prueba: detener su unidad (restaura
PM si estaba aplicado), deshabilitarla y retirar sólo esos archivos. El marcador
consumido impide que vuelva a cambiar PM en arranques posteriores.

Verificación histórica del helper PM: `test-usb-host-test.py` pasaba 16
casos de archivos simulados y el contrato de unidad; también pasaban los 18 checks
RNDIS. RED: el helper anterior dejaba `root_policy=auto parent_policy=on`;
GREEN: el nuevo deja temporalmente `root_policy=on parent_policy=auto` y restaura,
incluidos TERM, desconexión, sustitución del objeto y resume incompleto.
`sh -n` y `systemd-analyze verify` en chroot ARM64 pasan; hash instalado verificado.
**Estas verificaciones no demuestran funcionamiento del hub.**

Instalación y restauración: `.work/eqs-usb-hub/result-1/{install-usb2,restore-h29}.txt`.
SHA-256 del helper USB2 instalado:
`d66ebadea59a1570de460eff5cc9e3b0a4c96a0a8dd362374f1522b7368a0cdd`.

El script del ensayo **anterior** tenía SHA-256
`476f86edf3a074c608d57d8a7a25bf2a899502fcd3802c2f2cc6a328ff41e099`.
Los hashes de la captura canónica, release y kernel/módulos H29 se conservan.
La nueva comparación usa la interfaz nativa documentada de
[`power/control` USB](https://docs.kernel.org/driver-api/usb/power-management.html#the-user-interface-for-dynamic-pm),
sin modificar autosuspend global ni parámetros del kernel.

El resultado ya fue negativo; no repetir la prueba PM. La comparación con otro
Android sin PD prioriza la ruta USB del port. El modelo/VID:PID permitirá investigar
compatibilidad específica, pero no bloquea la revisión de código descrita arriba.

Si Type-C indica host pero DWC3 no, revisar la ruta UCSI/role-switch; si DWC3 ya
es host pero no enumera el hub, revisar xHCI/PHY/alimentación; si aparece el
teclado USB e input, revisar udev/libinput/sesión. No reinstalar Plasma para el
primer caso ni cambiar el kernel por el último. Datos y carga tienen roles
separados ([documentación Linux Type-C](https://docs.kernel.org/driver-api/usb/typec.html));
un teclado funcionando no demuestra todavía host más carga PD simultánea.
