# Diagnóstico nativo de un solo arranque

Perfil temporal de desarrollo, no parte de la imagen diaria. Requiere autorización de hardware y raíz ya instalada; no reinstala ni formatea nada.

## Consulta temporal del cargador H29

`eqs-usb-adc-prepare` y su `.service` son opt-in: preparan **un solo arranque**
con el módulo de diagnóstico de SHA fijado, no un arreglo de alimentación.
El helper va en `/usr/local/sbin/` y la unidad en `/etc/systemd/system/`.
El candidato y el backup H29 se conservan en `/var/lib/eqs-usb-adc/`, propiedad
de root y modo 0700; el marcador `armed` contiene el SHA-256 del candidato.
Habilitar la unidad sólo al autorizar una prueba; no iniciarla en caliente.

Antes de modules-load/udev, consume y sincroniza el marcador, verifica kernel,
hashes y el bind tmpfs nativo, y reemplaza el archivo de módulo mediante rename
atómico. Si el driver ya está cargado, rechaza la operación sin descargarlo.
No modifica boot/vendor_boot: **otro reinicio recupera los módulos H29**.
Para cancelar antes del reinicio, deshabilitar la unidad y retirar únicamente
`/var/lib/eqs-usb-adc/armed`. Para retirar un ensayo activo, lo mismo y un
reinicio autorizado; no usar `rmmod`, `unbind` ni forzar cargas.

`test-usb-adc-prepare.py` pasa 14 casos host, incluida simulación del segundo
arranque. Activación temporal y retorno a H29 se comprobaron físicamente el
8 de septiembre. **Ensayo cerrado:** la consulta devolvió payload vacío tanto
sin hub como con PD y receptor enumerado. H29 original quedó verificado otra vez
a las 17:59 ART, con helper deshabilitado y marcador ausente; no rearmar para
repetir estas consultas. [Resultado y límites del diagnóstico ADC](../../../docs/H29-CAMERA-ROTATION-BROWSER.md#investigación-del-8-de-septiembre-qué-parche-corresponde).

## Capturas de bring-up

**Preview H27 para prueba manual:** `eqs-preview.service` y `eqs-preview.timer` reutilizan la captura a los 90 segundos de cada arranque, pero con `SuccessAction=none` y `FailureAction=none`. Están instalados y sólo el timer preview quedó habilitado; no se arma a la vez el timer de retorno descrito abajo. La captura desarma únicamente el ensayo de retorno, conserva el timer preview y no repite periódicamente. La ventana de prueba de terminal dura unos 60 segundos: luego se abre QMLKonsole normalmente desde el lanzador.

Este perfil no habilita SSH ni garantiza acceso independiente de la pantalla. Para retirarlo, quitar únicamente el enlace `timers.target.wants/eqs-preview.timer`; conservar las unidades/capturas de retorno y el rescate A. `test-capture.py` comprueba esta separación y ambas unidades pasaron el parser de systemd ARM64. No confundir timeout del servicio con una garantía de recuperación ante bloqueo del kernel.

- `90-eqs-dev.conf` en `/etc/systemd/journald.conf.d/`: supera `Storage=volatile` del proveedor, limita journal a 32 MiB y reserva 128 MiB libres.
- `eqs-capture-once` en `/usr/local/sbin/`, ejecutable; unidad homónima en `/etc/systemd/system/`.
- Para ensayo gráfico, instalar también `eqs-capture-once.timer` en `/etc/systemd/system/` y armar el enlace `timers.target.wants/eqs-capture-once.timer` a `../eqs-capture-once.timer`. Dispara a los 90 segundos; no habilitar la captura directamente en multi-user, porque puede bloquear el arranque que queremos observar.
- En eqs se enmascaró sólo `serial-getty@hvc0.service` con enlace a `/dev/null`: fallaba con `208/STDIN`.

La captura registra START y los montajes principales **antes** de intentar desarmarse. Si falla `rm` o la creación del directorio de logs, registra stderr en kmsg. En el camino normal fuerza el intento de flush, espera 45 segundos y guarda `/var/log/eqs-bringup/{state,journal,progress,android}.txt`, luego sincroniza. Incluye estado LXC, propiedades, mounts, logcat y hashes del mismo módulo fuera/dentro del contenedor, con timeouts.

`eqs-usb-rndis`, opcional en `/usr/local/sbin/`, usa el gadget propio `eqs-debug`, sin SSH, DHCP ni forwarding. La captura lo ejecuta después del intento ADSP y registra `usb.txt`. H27 mostró que ADSP puede informar `running` antes de registrar Type-C: ahora `udevadm wait --timeout=8 --initialized=false /sys/class/typec/port0` espera ese registro, limitado además por `timeout 9`. Si falla, no se llama al helper; cuando aparece, siguen vigentes sus guardas de rol/propiedad. Halium19 comprobó RNDIS/ICMP IPv6 por cable directo con la versión anterior; no USB 3/PD/modo host ni estabilidad sostenida.

**Ciclo USB instalado en H27, guardas conservadas:**

- Sin argumentos o con `--start`, crea la definición sólo con UDC libre o reutiliza la propia intacta. Si ya está vinculada, sólo consulta la interfaz; no repite bind ni cambia sus direcciones.
- `--stop` desvincula únicamente ese gadget del UDC y conserva la definición para volver a iniciarlo. No cambia el rol del puerto ni pide una transición de alimentación. Desvincular y eliminar son operaciones distintas en [configfs](https://docs.kernel.org/usb/gadget_configfs.html).
- Rechaza identidad/configuración alterada o incompleta, propietario ajeno, nombres de interfaz inesperados y rol Type-C host/desconocido al iniciar. `flock` evita dos llamadas simultáneas al helper; **no bloquea escritores vendor**. Ante fallo/TERM/INT intenta soltar su nuevo bind; sólo revierte su cambio de rol si UDC y Type-C siguen permitiéndolo. Un atributo ilegible no significa UDC libre ni parada confirmada. Una definición parcial o de propiedad desconocida se conserva para inspección, no se borra a ciegas.

`eqs-usb-rndis.service` es una unidad **opt-in**, instalada pero no habilitada. Ubicación: `/etc/systemd/system/`, con el helper ejecutable en `/usr/local/sbin/`. H27 lo inicia desde la captura después de ADSP/Type-C, no desde esta unidad independiente. La unidad requiere configfs, ordena después de udev-trigger y limita inicio/parada a 15/10 segundos; no arranca ni detiene Plasma/LXC, no reintenta automáticamente y no abre un servidor. Su estado `active (exited)` indica que terminó el helper, **no que haya enumeración, carrier o un peer IP**. La limpieza de un inicio fallido pertenece al helper: [systemd no ejecuta `ExecStop` cuando falla `ExecStart`](https://github.com/systemd/systemd/blob/v257/man/systemd.service.xml).

**No habilitar todavía la unidad USB independiente al boot:** la secuencia ADSP/USB y los escritores vendor siguen por validar; la independencia entre unidades no prueba que el transporte sobreviva al reinicio de LXC. El preview conserva la secuencia acotada de la captura y puede llamar al helper ya iniciado sin reconfigurarlo. Para retirarlo, detener el gadget propio antes de restaurar el helper anterior y retirar sólo la unidad agregada; si cambia la propiedad, conservar el error y usar el rescate preparado. Ningún timeout garantiza limpieza ante bloqueo del kernel o SIGKILL.

Verificación previa: `python3 port/bringup/diagnostics/test-usb-rndis.py` pasa 18 casos en host y ARM64/QEMU con archivos simulados; `systemd-analyze verify --man=no --recursive-errors=no` acepta la unidad con systemd 257.7 del snapshot. Evidencia host: `.work/eqs-native-usb/`. El primer H27 rechazó Type-C ausente, correctamente; el arranque posterior con espera ya enumeró el gadget propio a 480 Mb/s con carrier en el host. No es validación de USB 3, PD, hotplug ni de todos los caminos de rollback.

El preview final seguía enumerado a los seis minutos del arranque y respondió dos veces al descubrimiento IPv6; después perdió los cinco pings unicast. El transporte no está aprobado como estable. No reinstalar por este síntoma: conservar estado y separar carrier, dirección/vecindad, energía y respuesta del peer.

La captura guarda también `egl.txt` con tags gráficos en vivo durante 40 segundos y permisos efectivos de GPU/DMA heaps; evita que el ruido de audio esconda el error inicial.

Para el perfil con módulos preservados por el initramfs en `/run/eqs-modules`, instalar `eqs-native-modules.conf` en `/etc/lxc/` y añadir **una sola vez, al final** de `/var/lib/lxc/android/config`: `lxc.include = /etc/lxc/eqs-native-modules.conf`. El bind obligatorio/readonly debe estar después del padre `/vendor_dlkm`; montar antes desde systemd no sirve con el bind no recursivo de LXC. No usar este fragmento con un initramfs que no produzca ese árbol. No desactiva comprobaciones ABI ni falsea propiedades de disponibilidad.

`60-eqs-wayfire-gdb.conf` es un override opcional en `/etc/systemd/system/plasma-mobile-wf.service.d/` para un ensayo acotado, sólo con autorización de depuración, GDB instalado y `wayfire.ini` ya generado. Conserva Wayfire/Plasma; obtiene backtraces, registros y mapas por journal sin core dump ni debuginfod. Se usó en Halium17–19 y se retiró para Halium20. No dejarlo en uso normal; el código de salida de GDB no indica que el escritorio funcione.

`eqs-wayfire-state.py`, opcional en `/usr/local/libexec/`, consulta únicamente salidas y ventanas por IPC como droidian; la captura lo limita a ocho segundos y guarda `wayfire.txt` con marcas de inicio/resultado e intérprete absoluto. Usa el socket propio de Wayfire, límites de tamaño y lecturas completas. Halium23 confirmó escritorio, paneles y asistente inicial mapeados. No crea ventanas ni simula entrada; una salida/ventana declarada no demuestra píxeles visibles.

**Captura de pantalla comprobada en H27:** `grim` instalado produjo un PNG de 1080×2400, recuperado y decodificado en host, con Plasma y QMLKonsole; Eduardo informó arranque visible por separado. `eqs-capture-once` pide la imagen de `HWCOMPOSER-1` desde el usuario `droidian` y el bus compartido de H25. Guarda `screen.png` y `screen.txt` en el directorio privado de diagnóstico. La unidad transitoria tiene 8 segundos de ejecución, 2 de parada y límite de archivo de 16 MiB; el lanzador también tiene timeout. Elimina imágenes anteriores/parciales y distingue herramienta ausente, rechazo, timeout y cabecera inválida. No cambia brillo/DPMS ni intenta desbloquear. `state.txt` agrega lectura de brillo real/solicitado y `bl_power` cuando el driver los expone.

La cabecera PNG y un exit 0 **no prueban imagen válida ni panel encendido**: decodificar el archivo recuperado en el host y contrastarlo con la pantalla física. Si el compositor rechaza screencopy por bloqueo, conservar el error; no desactivar la protección. La versión de `grim` del snapshot no estaba instalada en H26. Ver [salida PNG por stdout y selección de salida](https://manpages.debian.org/trixie/grim/grim.1.en.html) y [semántica `--pipe`/`--wait` de systemd 257](https://github.com/systemd/systemd/blob/v257/man/systemd-run.xml). Para revertir esta extensión, restaurar la copia anterior de `eqs-capture-once`; no agrega servicios permanentes.

`eqs-stock-gpu-firmware.sha256` identifica los seis blobs stock que Halium21 necesitó para EGL/GLES. Los binarios privados no están en Git. Se extrajeron de `modem_a/NON-HLOS.bin` y del vendor de **esta** base eqs, se verificaron y copiaron a `/lib/firmware`. No asumir compatibilidad con otro firmware/modelo.

`prepare-supermodem-rc.py STOCK_INIT_MMI_RC NEW_OUTPUT` prepara un overlay desde el RC de RETAR `U1SQS34.52-21-1-16` con SHA fijado. Elimina sólo dos tokens `context` rechazados sin política SELinux inicializada, conserva mounts readonly y rechaza otros inputs o un output existente. Instalar el resultado en `/etc/lxc/eqs-init.mmi.rc`, el fragmento `eqs-supermodem.conf` en `/etc/lxc/` e incluirlo al final de la configuración Android, después de respaldarla. Nunca editar la partición vendor. Halium23 comprobó el mount anidado y escaneo Wi-Fi; no asociación, batería/carga ni uso diario. Para revertir, retirar únicamente este include y sus dos archivos agregados.

Check host con el stock privado: `python3 port/bringup/diagnostics/test-supermodem.py RUTA_AL_INIT_MMI_RC_STOCK`. La prueba exige sólo dos cambios, flags/selector/slot intactos y rechazo de input desconocido/sobrescritura. No se distribuye el RC completo ni sus blobs en Git.

`99-eqs-no-binary-cache` en `/etc/apt/apt.conf.d/` desactiva sólo los dos cachés binarios opcionales de APT. Halium23 mostró que habían vuelto a crecer tras la limpieza anterior. Con sus copias y hashes verificados, se retiraron únicamente `pkgcache.bin` y `srcpkgcache.bin`; `apt-cache stats` funciona sin recrearlos. Recuperó unos 88 MiB, sin reparar ni redimensionar la raíz. Halium24 conservó 82 MiB disponibles y no recreó los archivos. Es margen para diagnóstico, no capacidad suficiente para uso diario.

`eqs-adsp-start`, opcional ejecutable en `/usr/local/sbin/`, prueba el arranque del ADSP por la interfaz nativa remoteproc. El cargador Qualcomm omitido junto con audio deja `boot_adsp/boot` ausente, mientras el procesador tiene `auto_boot=false`. El helper exige procesador/compatible exactos, firmware stock con hash fijado, ausencia de selección alternativa y del loader propietario; sólo escribe `start` desde `offline`, una vez. Nunca fuerza módulos, reinicia un DSP en fallo ni cambia límites de carga/térmica. La captura lo limita a 15 segundos y guarda `adsp.txt`; retorno/rescate siguen vigentes. `test-adsp.py` prueba guardas con archivos host, no batería real. Retirar el helper al terminar esta hipótesis; su presencia no constituye una política de carga de producción.

Halium24 comprobó ADSP `running` y batería nativa con capacidad/temperatura/estado `Charging`. No prueba carga sostenida ni sustituye la validación del control de energía completo.

La sesión H25 usa `eqs-wayfire-session` y `eqs-plasma-start` en `/usr/local/libexec/`, `60-eqs-session-bus.conf` como drop-in del servicio Plasma y el autostart Wayfire `plasma = exec /usr/local/libexec/eqs-plasma-start`. Requiere el `startkderc` suministrado en la configuración del usuario: **`systemdBoot=false` conserva el arranque clásico de Plasma**, porque el target systemd del snapshot requiere KWin. Ambos procesos comparten el bus PAM del usuario; sólo se importan variables gráficas explícitas antes de los servicios. No se modifican los launchers upstream. `test-session.py` cubre sockets ausentes, bus dividido, política incorrecta y fallo de sincronización. Revertir restaurando el `wayfire.ini` respaldado y retirando únicamente el drop-in, los dos helpers y el `startkderc` agregados.

**H25 comprobado en el teléfono:** portal KDE activo, bus compartido por Plasma/Maliit/systemd y Wayfire como único compositor en la captura. Persisten errores de los proxies exclusivos de X11 por falta de `xcb`; esto no demuestra aún imagen/táctil funcionales.

`eqs-terminal-probe`, opcional ejecutable en `/usr/local/libexec/`, se lanza dentro de QMLKonsole mediante una unidad transitoria del usuario limitada a 60 segundos. Exige stdin/stdout/stderr TTY, PID 1 `systemd` y usuario `droidian`; escribe kernel, dispositivo PTY, `TERM` y marca final de éxito en un archivo privado. Informa explícitamente si falta `tmux`: esta prueba no sustituye una sesión tmux/SSH. La captura elimina sólo sus reportes anteriores y guarda `terminal-launch.txt`/`terminal.txt`. `test-terminal.py` rechaza pipes y éxito parcial, usando PTY host real pero identidad simulada. Para retirar la prueba, eliminar únicamente el helper y sus reportes; no afecta el arranque normal de Plasma.

**H26 comprobado en el teléfono:** `/dev/pts/0`, `TERM=xterm-256color`, marca final correcta y ventana QMLKonsole mapeada/activa; `tmux` ausente entonces. La captura actual lee y limpia el archivo del usuario mediante `runuser`, nunca como root; si no logra retirar la evidencia anterior, aborta antes del lanzamiento. Pasó regresión host y lectura/denegación/limpieza ARM64 desde recovery. H27 completó un nuevo boot con esa captura, tmux instalado y PNG decodificado; todavía no prueba touch ni trabajo SSH/TUI.

`eqs-usb-shell` **no está habilitado en el teléfono**: la política del entorno bloqueó el aprovisionamiento de credenciales. Si se habilita mediante una vía aprobada, requiere identidad host nueva y fijada, clave pública dedicada y gadget propio en rol device. Escucha sólo en `fe80::2%usbN:22`, sin contraseña ni forwarding, bajo timeout de 40 segundos de la captura. El binario reutilizable es Dropbear 2016.74: exclusivamente bootstrap aislado por cable, nunca uso diario/red general. No están incluidos claves ni binario en este directorio; tests mock no demuestran autenticación real. No eludir el bloqueo mediante una shell sin autenticación.

La unidad **`eqs-capture-once.service`, no `eqs-preview.service`**, pide a systemd un reinicio normal con argumento `bootloader`, tanto en éxito como en fallo. Tiene un límite de inicio de 180 segundos. No garantiza retorno si PID 1 no carga la unidad o falla la ruta de reinicio: conservar rescate A conocido. Los logs pueden contener identificadores; no publicarlos sin revisar.

La unidad no espera local-fs/sysinit/basic; en la prueba aislada se selecciona con `systemd.unit=eqs-capture-once.service`. Esa prueba no activa Plasma ni Android. Quitar ese argumento para un arranque normal. No incluir este retorno automático en una imagen diaria.

Rescate: restaurar el conjunto A conocido, entrar en recovery y leer la raíz con `ro,noload` (no cambiar permisos persistentes del LV). Respaldar configuración antes de instalar. Para retirar el perfil, quitar únicamente los archivos/enlaces anteriores que se agregaron, retirar el include LXC, restaurar los originales si existían y conservar la evidencia en el host. Desmontar siempre la raíz antes de reiniciar.

Checks host: `python3 port/bringup/diagnostics/test-capture.py`, `sh -n port/bringup/diagnostics/eqs-capture-once`. Validación adicional realizada con `systemd-analyze verify` de la rootfs ARM64 desde recovery. Estos checks no demuestran el reinicio físico ni la captura nativa.

En este host `/tmp` puede agotar inodos: antes de tests **y de Fastboot**, usar un scratch propio con espacio, por ejemplo `mkdir -p .work/test-tmp; export TMPDIR="$PWD/.work/test-tmp"`. No borrar archivos de otros proyectos para liberar espacio.

## H28 media capture

La captura agrega `media.txt`: versiones Plasma/PulseAudio, módulos y tarjeta
ALSA, nodos de cámara/audio, inventario PulseAudio y `dumpsys media.camera`, con
timeouts. No reproduce sonido, abre cámaras ni fuerza cargas de módulos. Los
37 módulos nuevos se cargan desde systemd sobre el `vendor_boot` de ABI exacta;
la lista temprana de 325 módulos se conserva. Si existe el loader Qualcomm,
`eqs-adsp-start` rehúsa intervenir: no duplicar el dueño del ADSP.
