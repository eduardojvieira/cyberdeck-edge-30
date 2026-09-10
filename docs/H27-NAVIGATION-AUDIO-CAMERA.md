# H27 → H28: navegación, audio y cámaras

> Registro fechado. Para la imagen consolidada y el estado posterior, ver
> [release del 10 de septiembre](RELEASE-20260910.md). No repetir ensayos
> históricos ni inferir que un ZIP viejo incorpora cambios posteriores.

## Ejecución H28 — 6 de septiembre

**Instalado sobre la raíz existente; ensayo nativo aprobado hasta servicios.** No se reinstaló
`userdata`, no se escribió B y se conserva el rescate A completo. Antes de tocar
la raíz se verificó un backup privado de 16 GiB y se reparó el journal desmontado;
`e2fsck -fn` posterior a la instalación está limpio.

| Cambio | Evidencia disponible | Prueba pendiente |
|---|---|---|
| Plasma `+eqs2` | 27 regresiones host ASan/UBSan, 5 rechazos del builder, compilación ARM64 Qt 6.8.2 e importación de ambos plugins correctas; `dpkg --audit` limpio. | Inicio/Recientes/Cerrar, bloqueo, teclado y 20 ciclos físicos sin reinicio. |
| Gestos | Configuración nativa Wayfire: borde inferior hacia arriba = Inicio; borde derecho hacia adentro = Recientes. Preserva botones y colores; tests del generador aprobados. | Reconocimiento con el dedo. Se ejecutan al soltar, no son animaciones/Back de Android. |
| Audio/cámara | 37 módulos eqs añadidos: 35 audio, `camera`, regulador `wl2868c`; 368 módulos con dependencias y CRC de símbolos correctos. Dos `vendor_boot` idénticos; kernel/DT/lista temprana de 325 sin cambios. | Reproducción/grabación real y preview/fotos; ALSA y proveedores ya enumeran. |
| Política de audio | Parser ARM64 instalado: rutas por defecto fallan; ruta stock `/vendor/etc/audio/sku_cape/audio_policy_configuration.xml` acepta primary/salida. Override instalado mediante el hook PulseAudio existente. | Sonido audible; H28 ya mantiene PulseAudio con salidas/entrada reales. |

**Resultado nativo recuperado:** terminal con PTY/tmux, `+eqs2` cargado, tarjeta
`waipio-mtp-snd-card`, PulseAudio con `droid_card.primary`, `sink.primary_output`,
`sink.deep_buffer` y `source.primary_input`. El HAL de cámara 2.7 enumera dos
dispositivos (trasera/frontal), sin el abort inicial en esta captura. ADSP está
en ejecución bajo el loader vendor; batería 89 %, 30 °C, Charging puntual.
No hubo nueva foto/captura de cámara ni reproducción de audio de prueba.

El panel estaba apagado/bloqueado a los 136 segundos: brillo 0, `bl_power=4`,
`LockScreen Splash`; `grim` rechazó copiar la salida. No atribuirlo a un crash ni
saltarse el bloqueo. La captura completó y retornó a fastboot; se recuperaron los
logs. Después se dejó **el mismo candidato iniciado sin retorno automático**
para la prueba manual, con el hold y la configuración de usuario verificados.
El último arranque comenzó 14:17:48 UTC; RNDIS enumeró 14:19:34 y el host
registró desconexión USB 14:22:06, sin ADB/fastboot posterior. No hay logs nativos
nuevos que permitan atribuirlo a suspensión, rol USB o caída; no repetir flashes
sin evidencia. La pantalla final necesita la comprobación de Eduardo.

PackageKit había **revertido `+eqs1` a la versión upstream** por la preferencia
Droidian de prioridad 1002. Se verificaron dpkg/APT y se retiene únicamente
`plasma-mobile-wf` con `apt-mark hold`: simulación de upgrade sin cambios. No
congelar todo el sistema ni confundir versión de paquete con kernel ejecutado.

El helper ADSP rehúsa arrancar el coprocesador si detecta el loader Qualcomm;
no se eliminó esa guarda ni se copiaron ganancias/calibración de Bronco. Los
módulos de medios se difieren a `systemd-modules-load`, después de montar raíz.
La captura acotada agrega `media.txt` y no reproduce sonido ni abre cámaras.

Artefactos/evidencia privados: `.work/eqs-preview-h28/`,
`.work/eqs-h28-media/`, `.work/eqs-h28-usability/` y el build
`run-h28-one`. El builder regular incorpora la cadena de medios, pero todavía
no se reconstruyó/validó el paquete kernel dev3 completo. No es una imagen daily.
SSH autenticado sigue pendiente; no se eludió el bloqueo de aprovisionamiento.

La fuente oficial del [parser de audio fijado](https://github.com/droidian/pulseaudio-modules-droid-modern/blob/935726a/src/common/droid-config.c)
y el [reconocedor de gestos Wayfire fijado](https://github.com/droidian/wayfire/blob/258413269d5904e3ed89546af309df020348f0fe/src/core/seat/touch.cpp)
respaldan las rutas elegidas; la aceptación física no se infiere del código.

## Investigación inicial H27 (histórica)

Investigación del **6 de septiembre de 2026**. Eduardo confirma que la preview arranca y puede probarla, pero no puede salir/cerrar aplicaciones con los botones o gestos; tampoco funcionan sonido ni cámaras. **Conservar el arranque actual: primero acceso nativo autenticado y navegación Plasma–Wayfire; después audio y cámaras.** No reinstalar la raíz para corregir estos fallos.

## Qué está demostrado

| Área | Evidencia | Conclusión y límite |
|---|---|---|
| Navegación | El código fijado de Plasma todavía usa controles de KWin; la sesión es Wayfire. El usuario informa botones/gestos inoperantes. | Hay rutas de control sin adaptar. No es evidencia de mala calibración del touch. Falta observar las llamadas y protocolos en la sesión actual. |
| Audio | Logs H27: AGM no encuentra tarjeta SND; PulseAudio no puede parsear su configuración y aborta. El paquete carece de la cadena externa de audio. | Faltan capacidades de hardware y hay un fallo de configuración de userspace. No alcanza con desmutear una salida. |
| Cámaras | El proveedor Qualcomm 2.7 reinicia con SIGABRT al inicializar `camera.qcom.so`. El inventario del candidato no contiene `camera.ko`. | El fallo precede a la aplicación de cámara. La causa exacta del abort todavía no está aislada. |
| Acceso actual | USB directo, gadget `Droidian / eqs USB diagnostic`, RNDIS a 480 Mb/s; dos respuestas unicast IPv6 y rechazo TCP en puerto 22. ADB y fastboot no enumeran. | Transporte comprobado sólo en una muestra corta; no hay shell remota. No se recuperaron logs nuevos de esta sesión. |

Las capturas de software son las guardadas en `.work/eqs-preview-h27/native-first/`, no lecturas nuevas del teléfono. Las consultas USB/red del 6 de septiembre fueron de sólo lectura. **No se reinició, flasheó ni cambió el sistema durante esta investigación.**

## 1. Navegación: conectar los controles al compositor real

Fuente analizada en H27: `plasma-mobile-wf@69444e68c5d59fbcdeb79acc1a49313a4f114148`, paquete principal 6.3.3 con parche local `+eqs1`. Ese parche corrige PAM/recepción IPC, no navegación.

- **Recientes:** `NavigationPanelComponent.qml` llama a `TaskPanel::triggerTaskSwitcher()`, que envía `Mobile Task Switcher` a `/component/kwin` en `org.kde.kglobalaccel`. [Fuente fijada](https://github.com/droidian/plasma-mobile-wf/blob/69444e6/containments/taskpanel/taskpanel.cpp).
- **Inicio:** `ShellDBusClient.openHomeScreen()` llega a `HomeScreen.qml` y a `WindowUtil.minimizeAll()`. Esta última no hace nada sin `PlasmaWindowManagement`. La habilitación/cierre de la aplicación activa también depende de ese protocolo. [Control de ventanas](https://github.com/droidian/plasma-mobile-wf/blob/69444e6/components/windowplugin/windowutil.cpp).
- **Gestos:** el switcher móvil contiene integración de bordes propia de KWin. Elegir «sólo gestos» oculta la barra, pero no crea automáticamente acciones equivalentes en Wayfire. [Switcher](https://github.com/droidian/plasma-mobile-wf/blob/69444e6/kwin/mobiletaskswitcher/plugin/mobiletaskswitchereffect.cpp), [preferencia](https://github.com/droidian/plasma-mobile-wf/blob/69444e6/kcms/mobileshell/ui/main.qml).
- **`plamo` ya está habilitado:** en Wayfire `258413269d5904e3ed89546af309df020348f0fe` sólo expone eventos del botón de encendido mediante `plamo/watch`; no implementa esos controles KWin. [Plugin fijado](https://github.com/droidian/wayfire/blob/2584132/plugins/single_plugins/plamo.cpp).

### Cambio mínimo propuesto entonces; implementado en H28

Reutilizar el cliente IPC existente de Plasma y las acciones disponibles de Wayfire, sin otro escritorio, compositor o daemon:

1. Conectar Inicio, Recientes y Cerrar a una ruta común compatible con Wayfire. La configuración guardada ya incluye `ipc`, `ipc-rules`, `wm-actions` y `scale`.
2. Usar el overview nativo de `scale` para Recientes y solicitudes de cierre para la ventana de aplicación válida; no matar procesos. Inicio debe ser **idempotente**: dos pulsaciones no deben restaurar las aplicaciones ocultas.
3. Después de tener botones operativos, conectar gestos nativos a las mismas acciones. No confundir la preferencia de Plasma con una configuración efectiva de gestos en Wayfire.
4. Mantener el bloqueo y excluir paneles, escritorio, teclado virtual y superficies de bloqueo de las acciones de cerrar/minimizar. No perder la función de ocultar el teclado al adaptar el botón derecho.

Wayfire ofrece `scale/toggle`, `scale/toggle_all`, `wm-actions/set-minimized` y `window-rules/close-view`. `wm-actions/toggle_showdesktop` alterna estado: no sustituye por sí solo un Inicio idempotente. Este fork de `scale` desminimiza vistas al activarse; no atribuir el problema únicamente a `include_minimized=false`. Un IPC exitoso tampoco prueba que cambió la pantalla: el activador devuelve éxito sin propagar el resultado booleano de su manejador. [Scale](https://github.com/droidian/wayfire/blob/2584132/plugins/scale/scale.cpp), [acciones](https://github.com/droidian/wayfire/blob/2584132/plugins/wm-actions/wm-actions.cpp), [IPC](https://github.com/droidian/wayfire/blob/2584132/plugins/ipc/ipc-activator.hpp).

**Aceptación:** test host del encaminamiento y fallos del IPC; prueba física de 20 ciclos abrir → Inicio → Recientes → volver → cerrar, sin reinicio, incluyendo Inicio repetido, aplicaciones minimizadas, teclado y bloqueo. Son comprobaciones pendientes, no resultados actuales.

## 2. Audio: controlador primero, política después

`cmp` confirmó que `boot-bundle/candidate/vendor_boot.img` de H27 es idéntico a `.work/eqs-halium-kernel/eqs-dev-packages/vendor_boot.img`. Su `runs/one/built-modules.list` tiene 331 módulos: faltan, entre otros, `spf_core_dlkm`, `gpr_dlkm`, `machine_dlkm`, codecs y amplificadores que sí figuran en `reference/repos/eqs-development/android_device_motorola_sm8475-common/modules.load`. La lista de recovery no es el contrato completo de un teléfono operativo.

Orden de trabajo:

1. Confirmar en la shell nativa `/proc/asound/cards`, módulos/nodos y mensajes del kernel. Completar sólo la cadena de audio de eqs necesaria, con la misma configuración, fuentes, toolchain y validación de símbolos del kernel. No cargar módulos stock/Bronco a la fuerza.
2. Resolver un único responsable del ADSP: el helper actual se validó para alimentación, no sonido. Añadir `adsp_loader` sin revisar ese helper puede introducir doble gestión del coprocesador.
3. Con la tarjeta disponible, corregir la política de audio de eqs y el error de parseo de `module-droid-card`; verificar qué servicio posee el audio. Tener paquetes PipeWire y PulseAudio instalados no demuestra que compitan en ejecución.
4. Probar altavoz, auricular y micrófono a volumen bajo. Conservar calibración y controles térmicos; no copiar ganancias ni ruteo de otro modelo.

La adaptación local de Bronco aporta referencias de `audio_policy_configuration.xml` y exclusión de una tarjeta en WirePlumber. Su `30-bronco-wait.conf` sólo cambia `RestartSec`; no espera hardware. Su `vendor_modprobe.sh` presupone módulos integrados: **no copiarlo para declarar hardware listo en eqs**.

## 3. Cámaras: estabilizar el proveedor antes de elegir aplicación

`android.txt` registra `vendor.camera-provider-2-7` en `restarting` y un abort en `CamX::HwEnvironment::GetInstance()` durante la inicialización de `camera.qcom.so`. El sufijo `.cfi` de un símbolo no prueba una violación CFI. Un error de `/dev/video33` del servicio de codecs tampoco demuestra por sí solo el fallo de cámara.

Primero cotejar `camera.ko`, dependencias, nodos media, permisos, firmware/calibración y el tombstone completo. No se sabe aún qué comprobación concreta de CamX aborta. Recién con el proveedor estable, verificar una ruta compatible con Android HAL; una aplicación KDE/V4L2 genérica no reemplaza esa adaptación. La rootfs contiene `droidian-camera` y `qt5-cameraplugin-aal`.

**Primer objetivo físico:** preview y foto con cámara trasera principal y frontal. No prometer sensores auxiliares ni modos de 200 MP antes de medirlos. La [guía Droidian](https://docs.droidian.org/porting-guide/debugging-tips/) sirve de referencia, no de lista de parches genéricos que aplicar sin contraste con eqs.

## Acceso y recovery: no confundir conexión con control

El gadget actual sólo expone red. El nombre genérico «Nexus 4 (fastboot)» que muestra `lsusb` para su VID/PID no describe el protocolo activo: los descriptores y el driver son RNDIS. La dirección `fe80::2` pertenece al helper SSH no habilitado, no al gadget normal.

Sin SSH/ADB u otro canal de control ya disponible, **no podemos ordenar desde el host un reinicio seguro a recovery**. La preview tampoco tiene retorno automático. No resetear USB, provocar un fallo o esperar que se agote la batería para forzarlo.

Cuando exista acceso físico o una shell, preparar primero acceso nativo autenticado independiente de Plasma. Si hay que rescatar, seguir [RECOVERY.md](RECOVERY.md): recovery v14 no tiene kernel propio, depende de `boot_a`, y B no es respaldo válido. Una eventual restauración del conjunto A es un flash aparte que requiere autorización; no está implícita en leer logs. Montar la raíz `ro,noload` para inspección, sin wipe ni cambio persistente de permisos LVM.

**Próxima unidad útil:** habilitar el canal de desarrollo y preparar el parche de navegación sobre el paquete existente, con sus pruebas host. Conservar kernel, firmware, raíz y rescate. Audio/cámara tendrán después un candidato de módulos coherente y una validación física separada.
