# Camino corto a Droidian + Plasma Mobile en `eqs`

> Registro fechado. Para la imagen consolidada y el estado posterior, ver
> [release del 10 de septiembre](RELEASE-20260910.md). No repetir ensayos
> históricos ni inferir que un ZIP viejo incorpora cambios posteriores.

Análisis iniciado el 4 de septiembre de 2026, actualizado con ensayos físicos del 5 y feedback del 6. **El objetivo es Droidian nativo con Plasma Mobile 6 en el Edge 30 Ultra**, no construir otra recovery ni cambiar de distribución.

**Actualización de almacenamiento, 9 de septiembre:** ext4 ampliado al LV completo
de 224,52 GiB, reparación/comprobación offline y regreso a H29/SSH/Plasma verificados;
unos 200 GiB disponibles. Las medidas de 16 GiB siguientes son históricas.
[Resultado y recuperación](RECOVERY.md#ampliación-del-filesystem-9-de-septiembre).

**Preview H29 instalado:** `+eqs3` instalado y bloqueo de rotación confirmado por IPC
nativo de Wayfire. El alias del XML MediaProfiles corrige la caída al abrir las
cámaras; probar la app expuso otro fallo en EVA, cuyo módulo faltaba. El candidato
añade sólo ese módulo con la ABI existente, sin cambiar Image/DT ni userdata.
Ensayos nativos: principal y frontal producen 124/113 fotogramas de preview,
respectivamente, sin caída del proveedor. Se inició el preview normal, sin retorno
automático; faltan fotos/calidad, giro físico y exposición de las auxiliares.
[Investigación, pruebas y límites vigentes](H29-CAMERA-ROTATION-BROWSER.md).

**Avance H28 del 6 de septiembre:** raíz existente actualizada con navegación
Plasma/Wayfire `+eqs2`, gestos nativos, módulos eqs de audio/cámara y política
stock correcta. Build/importación ARM64 y tests host aprobados; ensayo nativo
acotado completado con tarjeta ALSA, salidas/entrada PulseAudio y dos cámaras
enumeradas. Se dejó el preview iniciado sin retorno automático. Ver
[estado y límites de H28](H27-NAVIGATION-AUDIO-CAMERA.md#ejecución-h28--6-de-septiembre).
No hubo reinstalación ni escritura de B; SSH y validación física siguen pendientes.

**Antecedente, preview H27:** Plasma visible informado por Eduardo y PNG nativo de 1080×2400 decodificado con paneles y QMLKonsole. Terminal con `/dev/pts/0`, `TERM=xterm-256color` y `tmux 3.5a`. Se instaló el paquete principal PAM/IPC `+eqs1` y siete paquetes pequeños, sin cambiar Qt, HWC ni kernel. Falta comprobar touch, PIN correcto/incorrecto, SSH/TUI y carga sostenida; H27 registró 90 %, 29 °C y `Discharging`.

**Espacio resuelto, sin reparticionar:** el filesystem ext4 era de 5028970496 bytes dentro de un LV de 241076011008 bytes. Con autorización específica se respaldó toda la extensión usada por el filesystem, se cotejó su SHA-256 con una segunda lectura del teléfono y se ensayó el crecimiento sobre una copia con el mismo e2fsprogs ARM64 1.43.4. La ampliación real a 16 GiB pasó `e2fsck -f -n` antes/después; `/` y `/home` muestran unos 11 GiB libres. Hashes de tmux/configuración Wayfire y metadata VG/PV/LV permanecen iguales. No hubo formateo, PV/LV resize ni escrituras a B.

**Entrega de prueba autorizada:** después de la primera captura H27 y el rescate se amplió el filesystem, se instaló el timer opt-in `eqs-preview.timer` y se volvió a flashear el conjunto A conocido H13. Inicia la captura/ADSP a los 90 segundos, sin retorno automático a fastboot; no habilita SSH. Es una excepción explícita para la prueba manual solicitada por Eduardo, no cumplimiento del acceso remoto autónomo. Eduardo confirmó el uso visible posterior al resize, con los fallos de navegación del 6 de septiembre. Paquetes, hashes y rescate en `.work/eqs-preview-h27/`; backup privado fuera del repo en `~/.local/share/eqs-backups/preview-h27/`. No se generó un instalador completo ni se exportó la raíz privada.

**USB: orden de inicio corregido, estabilidad pendiente.** El helper instalado rechazó correctamente el primer H27: ADSP decía `running`, pero `/sys/class/typec/port0` todavía no existía. Ahora la captura espera su registro con `udevadm wait` acotado antes de llamar al helper; si vence el plazo, conserva el error y no hace bind. Regresión RED/GREEN y parser/shell ARM64 aprobados, sin debilitar las 18 guardas de ciclo USB. La unidad USB independiente sigue sin habilitarse; [contrato y límites](../port/bringup/diagnostics/README.md).

El arranque final posterior al resize enumeró el gadget propio a 480 Mb/s con carrier; seguía presente a los seis minutos del arranque, sin volver a fastboot. Hubo dos respuestas IPv6 del teléfono en descubrimiento multicast, separadas de las respuestas locales del host. **El ping unicast posterior falló: 0/5 recibidos.** No declarar estable el transporte ni atribuirlo a suspensión/carga sin logs. Evidencia en `final-usb-monitor.txt`, `final-ipv6-discovery.txt` y `final-ipv6-unicast.txt` de la carpeta H27.

## Plan operativo desde Halium26

**La ruta más corta es conservar el arranque que funciona y conseguir una sesión de desarrollo nativa persistente.** Después se corrigen pantalla, bloqueo y entrada desde esa shell, reiniciando servicios en vez de alternar flash/captura/recovery. No hace falta otro kernel, otra distribución ni migrar todo Plasma a 6.5 para empezar.

La investigación original posterior a H26 fue host-only. Las ejecuciones H27/H28 sí instalaron paquetes y flashearon A con autorización; H27 amplió el filesystem y H28 añadió navegación/medios. Las secciones de investigación e historial conservan hipótesis anteriores; usar el estado vigente para no repetir trabajo completado.

### Qué falta realmente

| Frontera | Evidencia que ya tenemos | Qué falta para avanzar |
|---|---|---|
| Arranque | Kernel `eqs`, systemd PID 1, raíz LVM escribible y journal. | Conservarlo; no reabrir el bring-up del kernel sin una regresión identificada. |
| Gráficos | EGL/GLES Adreno, Wayfire, Plasma, portal KDE, PTY y PNG decodificado; usuario informa arranque visible H27. | Desbloqueo, eventos físicos de touch y uso sostenido. |
| Acceso remoto | RNDIS/IPv6 funcionó en H19; H26 enumeró pero después mostró UDC desconectado. | Transporte estable y SSH autenticado, independiente de la sesión gráfica. |
| Energía | ADSP arranca mediante helper; H24–26 midieron `Charging`, H27 `Discharging`. | Arranque normal del ADSP y estabilidad del USB/cargador; no hay prueba de PD ni carga sostenida. |
| Trabajo | Terminal nativa con tmux; Wi-Fi detecta redes; filesystem de 16 GiB/unos 11 GiB libres. | Asociación/IP/DNS, SSH saliente/TUI y teclado USB. |

### Hallazgos de la investigación H26

Actualización H28: `+eqs2` repone PAM/IPC y agrega navegación; el paquete está en hold. H27 validó PNG y amplió el espacio. No repetir su preparación; quedan las comprobaciones de interacción, transporte y energía.

**1. La capa negra del bloqueo es una hipótesis específica, no otro fallo de boot.** H26 mantiene `LockScreen Splash` en la capa overlay sobre la terminal. En [`LockScreenSplash.qml`](https://github.com/droidian/plasma-mobile-wf/blob/69444e6/components/mobileshell/qml/wayfiretweaks/LockScreenSplash.qml) el fondo es negro; [`WayfireTweaks.qml`](https://github.com/droidian/plasma-mobile-wf/blob/69444e6/components/mobileshell/qml/wayfiretweaks/WayfireTweaks.qml) lo muestra al iniciar/bloquear y lo oculta al desbloquear. También controla brillo/DPMS desde eventos de power e idle: quitar sólo el plugin idle de Wayfire no elimina toda esa ruta.

Comprobar superficie de bloqueo lista, negociación `ext-session-lock`, brillo y salida habilitada. El booleano local `locked` se cambia antes de confirmar el evento del compositor; no usarlo solo como prueba. **No eliminar el bloqueo ni declarar resuelta la pantalla por ocultar el splash.**

**2. Hay defectos concretos en la integración fijada que pueden corregirse sin rehacer la distribución.** Revisé `plasma-mobile-wf` `69444e6`, correspondiente al paquete 6.3.3 instalado; ese árbol no contiene una serie de parches Debian que corrija estos archivos:

| Código | Defecto | Evidencia obtenida ahora |
|---|---|---|
| [`sessionlock.cpp`](https://github.com/droidian/plasma-mobile-wf/blob/69444e6/components/sessionlockplugin/sessionlock.cpp), autenticación | El dato de conversación PAM apunta a un `std::string` temporal ya destruido. | Reproducción sintética: AddressSanitizer `heap-use-after-free`. |
| Mismo archivo, conversación PAM | Indexa el puntero de salida en vez del array de respuestas cuando hay varios mensajes. | Dos mensajes sintéticos: AddressSanitizer `stack-buffer-overflow`. |
| [`wayfireipc.cpp`](https://github.com/droidian/plasma-mobile-wf/blob/69444e6/components/wayfireipcplugin/wayfireipc.cpp), recepción | Libera con `delete` un array creado por `QDataStream::readBytes`. | AddressSanitizer `alloc-dealloc-mismatch`. |
| Mismo receptor IPC | Consume mensajes sin proteger lecturas parciales ni comprobar el estado del stream. | Un frame dividido se pierde; el control con transacciones Qt recupera el mismo payload. |

Las pruebas están en `.work/research-h26/`: C++/Clang ASan, Qt **6.11.2 host**, no el Qt **6.8.2 ARM64** del teléfono. Son reproducciones de patrones de la fuente, **no un crash observado del binario instalado ni prueba de la causa de la pantalla negra**. La documentación de [QDataStream 6.8](https://doc.qt.io/qt-6.8/qdatastream.html) confirma propiedad del array y transacciones para entrada asíncrona. Un parche mínimo debe conservar la autenticación, manejar estilos/errores PAM y límites del frame; no basta cambiar `delete` ni desactivar validaciones. Antes de instalarlo, verificar fuente/paquete efectivo y compilar contra el conjunto ARM64 fijado.

**3. Goodix ya se registra; no corresponde recompilar touch por un warning ambiguo.** H26 informa dos dispositivos `goodix_ts`; el pstore legible muestra firmware listo. La ruta [`input-manager.cpp`](https://github.com/droidian/wayfire/blob/2584132/src/core/seat/input-manager.cpp) intenta mapear todos los dispositivos, incluidos teclados; [`wlr_cursor.c`](https://github.com/droidian/wlroots/blob/bbe45e2/types/wlr_cursor.c) emite el warning si ese dispositivo no está adjunto al cursor. Primero identificar nodo y capacidades touch/teclado, permisos y eventos físicos con [herramientas libinput](https://wayland.freedesktop.org/libinput/doc/latest/tools.html), comprobando opciones de la versión instalada 1.28.1. Hay errores I2C al cambiar modo de carga, pero no demuestran por sí solos pérdida del touch.

**4. USB necesita un responsable y una secuencia medible.** `eqs-adsp-start` y `eqs-usb-rndis` se ejecutan recién desde la captura a los 90 segundos; no son aún integración de arranque normal. Hay que separar rol Type-C, propietario/bind del UDC, enumeración host, carrier e IP. El [modelo configfs](https://docs.kernel.org/usb/gadget_configfs.html) no convierte un `usb0` local en una conexión física. Tampoco una unidad `mtp-configfs` exitosa demuestra competencia: su [script fijado](https://github.com/droidian/mtp-server/blob/2b0f798/mtp-configfs/mtp-configfs) sale correctamente sin configurar nada si falta `mtp-supported`.

Inventariar primero quién escribe rol/UDC: helper nativo, MTP y servicios Android. Preservar RNDIS, que ya tuvo tráfico real. Probar inicio protegido del ADSP antes del bind final, esperando firmware/batería con timeout; **la relación entre transición ADSP/carga y desconexión es una hipótesis**, no una causalidad demostrada. ECM/NCM sólo si se identifica un fallo específico de RNDIS, no junto con otros cambios a ciegas.

**5. Falta espacio en ext4, no capacidad en la UFS.** H26: filesystem de unos 4.6 GiB, 82 MiB disponibles para usuario. La metadata LVM posterior a H11 tiene un LV raíz de aproximadamente 224.52 GiB. No instalar otro lote de paquetes al 99 %, ni seguir borrando archivos para ganar unos megabytes. Proponer un crecimiento acotado **sólo del filesystem**, por ejemplo a 16 GiB dentro del LV existente, con backup verificable y autorización específica. [`resize2fs`](https://manpages.debian.org/trixie/e2fsprogs/resize2fs.8.en.html) no exige ampliar un dispositivo que ya tiene espacio; un archivo undo no protege de un corte de energía.

### Orden de ejecución y aceptación

#### 1. Preparar acceso persistente y espacio, sin cambiar el kernel

- Conservar manifiesto/hashes del bundle H13 utilizado hasta H26 y del rescate A completo; revisar diferencia entre archivos realmente instalados y helpers locales. El ZIP Halium2 no representa ese estado.
- Usar el entorno ARM64 preparado contra `101.20251130`, no los metadatos `101` del contenedor antiguo. Docker y las descargas autorizadas ya están resueltos, sin instalar dependencias en el host. El rechazo previo del hook de preparación SSH sigue siendo independiente: no evadirlo con otro comando/servidor ni habilitar shell sin autenticación.
- Preparar en host los paquetes ARM64 mínimos del snapshot: OpenSSH servidor para **desarrollo**, `tmux` y herramientas de captura/input que realmente falten. Simular resolución de dependencias antes de instalar. El perfil diario seguirá sin SSH entrante; hoy el inspector de rootfs lo rechaza globalmente y deberá distinguir explícitamente dev/daily.
- En una sesión recovery autorizada: comprobar UUID, tamaño de filesystem/dispositivo y estado desmontado. Respaldar datos de la raíz y metadata LVM, verificar que la copia se pueda leer/restaurar y ensayar el crecimiento en una copia antes del dispositivo. Si hacen falta reparaciones, detenerse y evaluarlas; nada de `e2fsck -y` automático, PV/LV resize ni formateo. Un backup sólo de metadata no respalda archivos.
- Aprovisionar por la vía aprobada un OpenSSH compatible y actualizado, login de usuario por clave, sin root/password/forwarding, limitado a la red USB directa; comprobar `sshd -t` y configuración efectiva. Identidad de host y credenciales por dispositivo, nunca en Git/ZIP. Cambiar el PIN de plantilla antes de conectarse a otras redes. No usar el Dropbear de 2016 como solución final de acceso.
- Reutilizar los helpers con una unidad de inicio normal y orden/timeout explícitos. Un solo propietario del gadget; no forzar roles cuando el cable indique host ni tocar política eléctrica/térmica. El servicio SSH debe permanecer independiente de Wayfire/LXC; validar por separado si la disponibilidad del transporte también lo permite.

**Aceptación de autonomía:** espacio suficiente para paquetes/logs y una shell SSH nativa autenticada que permanezca disponible al detener/reiniciar la sesión gráfica. H27 completó el espacio; su preview manual sin retorno automático no cumple todavía la parte SSH. Para ensayos posteriores sin acceso verificado, conservar captura y retorno/rescate acotados. Luego medir recuperación tras reinicio de LXC sin asumir que detendrá sólo gráficos. La [guía Droidian](https://docs.droidian.org/porting-guide/debugging-tips/) justifica devtools/SSH/journal, pero sus ejemplos de Phosh, brillo y `userdata` no son comandos copiables sobre este port LVM/Wayfire.

#### 2. Resolver pantalla y bloqueo desde Droidian, no desde Fastboot

Preparar una captura acotada que registre estado antes/después de cada prueba, sin loguear contraseñas ni todo el entorno. Reutilizar `eqs-capture-once`, journal e IPC existentes; no crear otro framework de diagnóstico.

1. Verificar salida, DPMS/brillo y protocolo de captura. El [Wayfire fijado registra screencopy](https://github.com/droidian/wayfire/blob/2584132/src/core/core.cpp); intentar una captura con `grim` empaquetado bajo el usuario/sesión correctos. La existencia del protocolo no garantiza que la ruta HWC permita capturar. Un rechazo por bloqueo no es una captura negra válida ni justifica saltarse el bloqueo.
2. Correlacionar imagen capturada con una observación física breve. Si hay imagen correcta en captura pero panel negro, revisar presentación HWC/power/backlight. Si la captura válida muestra el splash, revisar el recorrido de bloqueo. Si captura falla, conservar su error y seguir con la evidencia de protocolo/salida; no deducir qué muestra el panel.
3. Aplicar las correcciones mínimas PAM/IPC al paquete fijado, con pruebas host de vida útil, varios mensajes PAM, credencial incorrecta, fragmentación y límites. No autenticar con datos de prueba en el teléfono ni dar un éxito por defecto ante error. Compilar/inspeccionar ARM64 y luego probar desbloqueo real correcto/incorrecto.
4. Identificar el dispositivo Goodix táctil y registrar una interacción física corta. Verificar coordenadas/foco en pantalla de bloqueo y QMLKonsole. Primero el modo nativo anunciado, orientación vertical y escala simple; horizontal/60 Hz se ajustan después. H26 advierte que no encuentra el modo solicitado `1080x2400@60`: no confundir configuración pedida con frecuencia física validada.

No ejecutar `test_hwcomposer` a la vez que Wayfire ni crear dos clientes dueños del compositor Android. La fuente [HWC output](https://github.com/droidian/wlroots/blob/bbe45e2/backend/hwcomposer/output.c) separa commit de buffers y modo de energía: ni EGL inicializado ni superficies IPC prueban que esa presentación llegue al panel.

**Aceptación:** Plasma y terminal visibles, touch útil, PIN incorrecto rechazado y correcto aceptado, recuperación de la pantalla sin perder SSH. La captura digital y la observación física se registran como evidencias distintas.

#### 3. Convertirlo en un cyberdeck mínimo y recién entonces en una imagen

- Configurar Wi-Fi por una vía privada, confirmar asociación, IP, DNS y tráfico; comprobar SSH saliente/TUI con desconexión y reanudación usando el `tmux` ya instalado. No guardar PSK ni credenciales laborales en las capturas.
- Probar teclado USB en modo host como topología separada: no asumir que el mismo puerto seguirá ofreciendo RNDIS. Tener Wi-Fi/acceso alternativo validado antes de depender del teclado; carga por hub, PD y Ethernet vienen después.
- Criterio inicial propuesto, no certificación: **tres arranques consecutivos**, 30 minutos de sesión visible con SSH/tmux, diez reconexiones del cable de diagnóstico y bloqueo/desbloqueo correcto. Carga y temperatura requieren medición propia; un dato `Charging` no aprueba consumo sostenido ni la térmica de carcasa.
- Integrar los cambios que pasaron HIL en los paquetes/adaptación existentes: módulos LXC, firmware/mounts, permisos GPU, ADSP, bus de sesión, acceso dev y parches Plasma. No exportar sin más la raíz privada modificada ni sus claves.
- Construir una imagen **eqs-dev** que reproduzca ese conjunto, con fuentes/paquetes/hashes fijados e instalación completa separada del helper A-only de iteración. Ensayar instalación/restauración con autorización, incluido FastbootD para userdata según la ruta ya probada. Sólo entonces llamarla imagen inicial usable; el ZIP antiguo no incorpora H26.

**Después:** LUKS2, imagen diaria sin acceso de depuración, suspensión, teclado virtual automático, dock/carga y carcasa. No entran telefonía, cámara, audio completo ni cambios cosméticos en el camino crítico. Conservar servicios de energía/térmica; no desactivar todo Android para silenciar errores de audio.

### Reglas para acelerar sin perder evidencia

- El siguiente entregable es **acceso nativo persistente**, no otro número de imagen. Preparar dependencias, espacio, rescate y captura antes de una sesión física; cambios identificados y mediciones separadas aunque compartan arranque.
- Si falla una aplicación o el bloqueo, reiniciar y diagnosticar ese servicio desde SSH. Fastboot queda para cambiar arranque o recuperar una pérdida real de acceso.
- Si USB no enumera, el siguiente foco es rol/UDC/Type-C/host con timestamps monotónicos, no reinstalar Plasma. Si enumera y falla SSH, separar IP/ruta/listener/autenticación.
- Con un fallo reducido en código upstream, parche pequeño y test. No migrar kernel, firmware y escritorio simultáneamente buscando que desaparezca el síntoma.
- Ninguna promesa de horas hasta probar pantalla/touch/USB; reducir ciclos evitables es una mejora verificable. Pedir intervención física sólo cuando aporte una observación que no se obtiene por software.

### Evidencia y alcance de esta investigación

- Local: `.work/halium26-native-terminal/native-capture/{state,journal,wayfire,terminal}.txt`, pstore H26; `.work/halium11-mounttrace/lvm-after.conf`; `.work/eqs-rootfs/inspection/PACKAGES.tsv`; helpers de `port/bringup/diagnostics/`; árboles Motorola y bronco locales como referencia, nunca como imágenes intercambiables.
- Fuentes comparadas: `plasma-mobile-wf@69444e6`, `plasma-workspace@c41cc1c`, `wayfire@2584132`, `wlroots@bbe45e2`, `mtp-server@2b0f798`. `startplasma.cpp` importa más entorno posteriormente: que la whitelist temprana no incluya `WAYFIRE_SOCKET` **no prueba** que Plasma lo pierda. Comprobar esa variable concreta y el socket activo sin volcar secretos.
- Reproducciones host: tres errores ASan esperados y prueba de fragmentación/control en `.work/research-h26/`; README local con comandos y límites. No son tests del binario ARM64 ni correcciones instaladas.
- Búsqueda web nativa y fuentes oficiales mediante GitHub. Tavily no estaba disponible en las herramientas de esta sesión. Sin flash, acceso al teléfono, commit ni push durante esta revisión.

---

## Historial de diagnóstico

Lo que sigue conserva la evolución H2–H26 y las hipótesis anteriores. **Para ejecutar trabajo nuevo, usar el plan operativo de arriba.**

## Avance físico del 5 de septiembre

**Halium5 alcanzó systemd como PID 1 nativo.** El análisis original que sigue queda como historial, no como estado vigente.

- Halium3 confirmó UFS, vendor y raíz LVM. Halium4 localizó `run-init: opening console: No such device`.
- Halium5 conservó kernel y módulos, pasando `-c /dev/null` a validación y handoff. Pstore registra `systemd[1]` gestionando servicios hasta aproximadamente 398 segundos. Alcanzar `graphical.target` no demuestra que Plasma funcione.
- Pantalla negra y sin USB nativo. El getty de `hvc0` falla con `208/STDIN` y llena pstore; journald está vivo pero no se encontraron archivos persistentes.
- `mtp-configfs@rndis` depende de LXC/Android. Los targets genéricos `usb-gadget.target` y `ssh-access.target` no implementan por sí solos acceso de rescate. No está instalado `openssh-server`.
- Recovery v14 con kernel stock volvió a proporcionar ADB. Inspección de raíz con `ro,noload`, sin repair, resize ni reinstalación. Quedan aproximadamente 309 MiB: limitar logs y comprobar espacio antes de instalar paquetes.

Evidencia privada: `.work/halium5-rescue-20260905T113603Z/pstore/console-ramoops-0`.
Boot: `.work/halium5-console-fix/boot.img`, SHA-256
`1f35b4082ff1750ec6df7b7af6e2d1708b262dc0491f4c105c323ade1307e9f2`.

**Siguiente paso:** preservar este kernel, reducir spam de consola y preparar logs persistentes y acceso nativo autenticado; después diagnosticar Android/HWC y Plasma. No reinstalar el sistema ni distribuir Halium2 como si incluyera el arreglo.

## Investigación web y ensayo aislado — 5 de septiembre

El ensayo Halium8 conservó el kernel y el ramdisk de Halium5; cambió sólo la línea de arranque para seleccionar `eqs-capture-once.service` y reducir el log de systemd. El pstore recuperado conserva ahora el inicio: PID 1 arranca esa unidad a los 3,843 s y su proceso sale con código 1 a los 3,849 s. **No era correcto concluir que systemd no cargaba la unidad** a partir de su enlace de activación intacto.

También aparecen errores `Read-only file system` al preparar `/root/userdata/android-data` dentro del initramfs. Esto exige comprobar los montajes efectivos; no demuestra corrupción de UFS ni autoriza fsck/reinstalación.

| Fuente primaria consultada | Qué aporta al próximo paso |
|---|---|
| [Droidian: debugging tips](https://docs.droidian.org/porting-guide/debugging-tips/) | Devtools aporta SSH/RNDIS y persistencia de logs. La guía reconoce fallas de consola en el handoff. No aplicar recetas antiguas de resize a nuestro PV LVM. |
| [systemd 257: selección de unidad](https://github.com/systemd/systemd/blob/v257/man/systemd.xml) | `systemd.unit=` selecciona la unidad inicial; Halium8 confirmó físicamente que la opción fue respetada. |
| [systemd 257: journal](https://github.com/systemd/systemd/blob/v257/man/journald.conf.xml) | `Storage=persistent` conserva fallback a RAM si el disco no permite escribir; requiere flush. Crear el directorio no prueba persistencia. |
| [AOSP: vendor_boot](https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions) | El initramfs real combina vendor y ramdisk genérico. Conservar y verificar ambos; una cabecera válida no demuestra el arranque. |
| [Linux: ramoops](https://docs.kernel.org/admin-guide/ramoops.html) | El buffer tiene tamaño limitado; evitar el spam que reemplazaba las trazas tempranas. No copiar regiones reservadas de otro dispositivo. |

**Corrección del diagnóstico:** el script anterior intentaba borrar su enlace antes de emitir START; con `set -e` un error allí impedía tanto el registro como el reinicio. Se agregó evidencia previa a escrituras, captura de stderr de `rm`/`mkdir` y retorno declarativo por systemd (`SuccessAction`/`FailureAction`, `RebootArgument=bootloader`). Test negativo host RED/GREEN para fallo al desarmar y verificación de sintaxis con systemd ARM64. Halium9 no devolvió ADB ni fastboot durante la ventana observada de más de cuatro minutos. Falta recuperar su pstore: no se da por validado el retorno.

Evidencia privada: `.work/halium8-rescue-20260905T154526Z/`. Halium9 usa el mismo boot aislado, con la nueva unidad instalada. No hay todavía escritorio ni shell nativa utilizable. Próximo foco: errno de la primera escritura, montajes reales y después devtools upstream; no nuevas hipótesis sobre Plasma.

## Slots A/B y retorno automático — 5 de septiembre

Fastboot informó `current-slot=b`, A `unbootable=yes` y `retry-count=0`. Escribir imágenes A no garantiza arrancarlas: [AOSP documenta que `set_active` selecciona el slot, borra la marca no arrancable y reinicia sus intentos](https://source.android.com/docs/core/ota/ab/ab_implement). Se restauró el rescate A, se seleccionó explícitamente A y se comprobaron siete intentos. No se escribieron particiones B ni userdata.

El pstore recuperado de ese estado no identifica el candidato Halium9: no permite atribuirle el último logo. El flasher corregido usa las respuestas reales de Motorola (`securestate`, versión de bootloader en fragmentos numerados), verifica la base exacta y sólo selecciona A después de completar todas las escrituras. `--rescue-a` admite recuperar desde B activo; `--flash-a` lo rechaza. No marca el arranque como exitoso artificialmente.

**Halium10 completó el primer ciclo automático candidato → fastboot → recovery.** El pstore identifica el candidato, slot `_a`, systemd nativo y esta secuencia:

```text
3,824 s  captura START; /run tmpfs rw; / ext4 ro
3,825 s  rm del enlace de captura falla: Read-only file system
5,014 s  reinicio con argumento bootloader
```

El retorno se observó sin intervención física; A conservaba seis intentos y el motivo era `Reboot mode set to fastboot`. El rescate A volvió a entregar ADB. **La causa de la captura fallida ya está localizada en la raíz sólo lectura, no en que systemd ignore el servicio.** Falta localizar la transición RW→RO en el initramfs antes de cambiar el montaje. No hay evidencia de corrupción ni razón para reparar o reinstalar userdata.

Evidencia privada: `.work/halium9-rescue-20260905T160915Z/` y `.work/halium10-slotreset/`. Pruebas host del flasher incluyen metadatos inválidos, integridad, fallos parciales y selección fallida; el flasher corregido también completó candidato y rescate en esta unidad. El ZIP Halium2 original no se modificó.

## Raíz LVM escribible y captura persistente

Halium11 localizó el montaje RO **desde el primer `mount -o rw`**, antes de mover la raíz o montar Android. La inspección LVM encontró `droidian-rootfs` con atributo `-ri-ao----`, dispositivo `ro=1` y metadata `status=[READ,VISIBLE]`: faltaba permiso `WRITE`. `.writable_image` no puede corregir el permiso del volumen de bloques.

Se guardaron `vgcfgbackup` y el primer MiB del PV con hashes; con la raíz desmontada se cambió **sólo** `droidian/droidian-rootfs` a `--permission rw`. La comparación de metadata confirmó permiso READ/WRITE y aumento de secuencia 10→11, sin modificar tamaños, extents ni los otros LVs. No se ejecutó fsck ni resize. [LVM documenta la diferencia entre cambiar permisos y consultar metadata en modo readonly](https://manpages.debian.org/bookworm/lvm2/lvchange.8.en.html). El origen exacto del permiso anterior no está establecido; no atribuirlo al builder sin evidencia.

**Halium12 validó la corrección físicamente sin cambiar el boot de Halium11:**

- Raíz ext4 RW desde initramfs hasta systemd nativo.
- Captura START a los 3,858 s y COMPLETE a los 49,051 s; reinicio `bootloader` a los 49,985 s.
- Recovery recuperó `state.txt`, `journal.txt` (aproximadamente 221 KiB), marcador `START/CAPTURED` y journal binario persistente.
- El UDC real `a600000.dwc3` existe; también hay un UDC dummy, por lo que no hay que seleccionar simplemente el primero.
- LXC, Plasma y RNDIS estaban inactivos deliberadamente por la unidad aislada. Esto no prueba ni refuta su funcionamiento.

Evidencia: `.work/halium11-mounttrace/lvm-before.conf`, `lvm-after.conf`, `pv-header-before.bin` y `.work/halium12-lvmrw/`. Las capturas pueden contener identificadores privados: no publicarlas sin saneamiento.

Para inspeccionar en recovery, usar montaje `ro,noload` **sin cambiar el permiso persistente del LV a sólo lectura**. Antes de arrancar, comprobar el permiso READ/WRITE y desmontar. Halium13 conserva kernel y ramdisk e inicia `graphical.target`; un timer nativo dispara la captura a los 90 segundos para no bloquear el arranque gráfico con la propia herramienta de diagnóstico.

## Contenedor Android y dependencia gráfica

Halium13 completó el ensayo con `graphical.target` y recuperó la captura programada sin botones. `lxc-start` retornó éxito; se ejecutaron ambas etapas de Android init y arrancaron servicemanager/hwservicemanager. **El bloqueo es la notificación de disponibilidad:** `lxc-android-notify` espera `apexd.status=ready` y vence el timeout de 90 segundos. HWC, Plasma y `mtp-configfs@rndis` quedan sin iniciar por dependencia fallida, no por un crash del compositor.

El sistema nativo usa cgroup2 y Android registra errores al montar controladores cgroup clásicos. Algunos clientes libhybris tampoco encuentran `libc.so` fuera del entorno preparado por la notificación. Son indicios para contrastar con propiedades, montajes y logcat del contenedor; no justifican saltarse la espera ni cambiar cgroups a ciegas.

Halium14 localizó la espera anterior: el `init.qti.kernel.rc` exacto del firmware stock contiene `wait_for_prop vendor.all.modules.ready 1`. `vendor.modprobe` sale con código 1 porque intenta cargar módulos stock (`mdt_loader`, entre otros), rechazados por versiones de símbolos incompatibles con el kernel del candidato. No se va a forzar esa carga ni a fingir que APEX está listo. El sistema Android es API32; vendor informa SDK31, no API34 por el nombre comercial Android 14.

Halium15 probó un bind de los módulos correctos antes de LXC, pero siguió viendo los stock: el bind **no recursivo** del directorio padre `/vendor_dlkm` pierde los submontajes. Además `/vendor/lib/modules` es un symlink absoluto a `/vendor_dlkm/lib/modules`. **Halium16 resolvió la frontera** incluyendo `port/bringup/diagnostics/eqs-native-modules.conf` después del mount padre, con bind obligatorio y readonly del árbol del initramfs. Los SHA-256 de `mdt_loader.ko` coinciden fuera/dentro del contenedor; aparecen `vendor.all.modules.ready=1`, `apexd.status=ready` y LXC activo. No se reemplazó el loader stock ni se falsearon propiedades.

**Frontera encontrada en Halium16:** Wayfire 0.9.0 inicia el backend HWC, recibe la salida primaria de 1080×2400/60000 mHz y obtiene sesión logind. Luego registra `Segmentation fault` tras iniciar EGL y sale con código 255; otros reintentos reciben SIGHUP. Por sí solo, eso demostró enumeración HWC, no imagen visible ni causa única del crash.

Halium17 usó GDB 16.3 ya instalado y capturó `SIGSEGV` en `strchr → strstr`. Halium18 agregó registros y mapas: el caller corresponde al offset `0x15dc4` de `/android/system/lib64/libEGL.so` (build ID `222f6ccdd90c99e8eddd8b955998bb1e`). El desensamblado y el [código Android correspondiente](https://raw.githubusercontent.com/LineageOS/android_frameworks_native/lineage-19.1/opengl/libs/EGL/egl_display.cpp) sitúan la llamada en la consulta de extensiones después de inicializar el driver. El aviso de unwind `corrupt stack?` no demuestra corrupción de memoria.

**Halium19 confirmó el fallo previo:** el logcat filtrado en vivo registra `open(/dev/kgsl-3d0)` con `errno 13`, seguido de `eglInitialize` con `EGL_BAD_ALLOC`. El nodo nativo era `root:root 0600` y el usuario droidian no podía leerlo ni escribirlo. Android ueventd administra otro `/dev`; no basta con sus permisos dentro del contenedor. Se añadió `80-eqs-gpu.rules`, limitada a ese nodo, `root:render 0660`. El usuario ya pertenece a `render`. Verificación sintáctica host/ARM64 aprobada; **Halium20 comprobó acceso de lectura/escritura y desaparición del `EACCES`**.

Halium20 pasó a fallar con `ENOENT` dentro del open del driver: **el nodo sí existía**, pero `request_firmware(a730_sqe.fw)` no encontraba el archivo. Motorola monta primero `modem_a`, cuyo directorio `image/` sólo contiene Widevine; la GPU está en `NON-HLOS.bin`, una imagen ext4 anidada. Las propiedades Android seleccionan correctamente ese archivo, pero el mount posterior a `/vendor/super_modem` falla con `EINVAL`. No se falsearon esas propiedades ni se cambiaron particiones de radio.

**Halium21 superó EGL:** se extrajeron en sólo lectura cinco archivos `a730*` de esa imagen y `gmu_gen70000.bin` del vendor stock correspondiente, con [hashes fijados](../port/bringup/diagnostics/eqs-stock-gpu-firmware.sha256). Se instalaron únicamente en `/lib/firmware` de la raíz nativa, usando la búsqueda estándar del kernel. Wayfire registra EGL 1.5, OpenGL ES 3.2, proveedor Qualcomm y renderer Adreno 730; permanece activo durante la captura y `plasmashell` pide servicios por D-Bus. No vuelve a aparecer el crash anterior en ese intervalo. **Esto todavía no es una validación visual, de touch o de uso diario.**

En Halium21 el fallo general del mount super-modem seguía afectando firmware Wi-Fi/DSP. El journal localizó la causa: `context=u:object_r:firmware_file:s0` es rechazado por SELinux antes de inicializar su servidor de seguridad. El kernel sí tiene SELinux compilado; no confundir ausencia de política con ausencia del subsistema.

Además aparecieron errores `ENOSPC` del usuario: el filesystem raíz inicial es de 4.5 GiB aunque el LV sea mucho mayor. Para Halium22 se respaldaron y retiraron sólo 88 MiB de cachés APT regenerables, sin resize ni cambios LVM; se añadió prueba de escritura de usuario y consulta IPC readonly de salidas/ventanas Wayfire. Se desactivó el idle sólo en ese ensayo para que los 60 segundos de DPMS no oculten la sesión antes de capturarla. **Halium22 repitió EGL/Plasma y `HOME_WRITE_OK`, pero dejó la captura IPC vacía:** no probaba ausencia de ventanas. Halium23 usa intérprete absoluto y marcas de inicio/resultado; no se atribuye retrospectivamente una causa sin evidencia.

**Halium23 resolvió el mount y confirmó superficies Plasma:**

- `prepare-supermodem-rc.py` exige el SHA del RC stock exacto y elimina únicamente los dos tokens `context` de los mounts super-modem. Conserva `ro,nosuid,nodev`, slot y selector de imagen. El include LXC monta el RC generado readonly; no modifica vendor ni particiones de radio. Tests host rechazan firmware desconocido y sobrescritura.
- El mount real muestra `loop2` en `/vendor/firmware_mnt`, también propagado al namespace nativo. CDSP, SLPI y modem llegan a estado `up`. La búsqueda inicial de `qca6490/amss20.bin` falla, pero el fallback `amss20.bin` carga: no interpretar ese primer `ENOENT` como fallo definitivo.
- Wi-Fi registra `FW ready`, NetworkManager reconoce `wlp1s0` y el kernel completa escaneos con 8–9 BSS. **No se probó asociación ni tráfico.**
- IPC devuelve `HWCOMPOSER-1`, geometría lógica 360×800 y cuatro escritorios en una fila. Están mapeados el asistente `Initial Start`, fondo, paneles superior/inferior y superficies auxiliares de Plasma. `WF_QUERY_OK` confirma la consulta; no demuestra píxeles visibles ni touch.
- Captura completa a los 136.737 s; reinicio a bootloader a los 315.389 s, seguido de rescate A y ADB en recovery. Se mantiene el boot de Halium13. No hubo wipe, resize, escrituras B ni intervención física del usuario.

**Límites observados en Halium23:** no aparecía `/sys/class/power_supply/battery` y los servicios de carga reportaban que faltaba el dispositivo. La raíz reportaba sólo 2.7 MiB disponibles para usuarios, aunque pasaba la pequeña prueba `HOME_WRITE_OK`: limpiar cachés no había resuelto el margen de espacio de forma sostenible.

Evidencia privada: `.work/halium22-session-capture/` y `.work/halium23-supermodem/`. El overlay stock y logs permanecen fuera de Git.

**Halium24 resolvió dos causas concretas sin recompilar el kernel:**

- Los dos cachés APT de unos 88 MiB se habían regenerado. Se respaldaron con hashes y se desactivó su almacenamiento binario mediante `Dir::Cache::pkgcache`/`srcpkgcache` vacíos. `apt-cache stats` funciona en ARM64 sin recrearlos y el siguiente arranque nativo conserva 82 MiB disponibles y `HOME_WRITE_OK`. No se retiraron paquetes ni se hizo repair/resize. Sigue siendo poco espacio para una imagen diaria.
- La lista de build omite `adsp_loader_dlkm` y cinco dependencias de audio. Ese módulo crea `/sys/kernel/boot_adsp/boot`, esperado por Android init. El driver PAS de cape tiene `auto_boot=false`: ADSP quedaba sin arrancar. El helper diagnóstico exige ADSP/compatible exactos, firmware `adsp.mdt` stock con SHA verificado y ninguna selección alternativa ni otro loader. Escribe una sola vez `start` desde `offline` por la interfaz remoteproc, que llama al mismo `rproc_boot()` del loader. No cambia tensiones, corrientes, protección térmica ni ABI.
- ADSP pasó a `running`; aparecieron capacidad 90, temperatura 290 (décimas de °C) y estado `Charging`. **Es telemetría puntual del driver, no prueba de ganancia neta, PD estable ni temperatura de carcasa.** Algunos mensajes del healthd Android todavía no reconocen la batería; no declarar completa toda la integración de energía.
- Wayfire/Plasma conservaron sus superficies IPC. Captura a los 137.093 s y reinicio a los 310.297 s, con rescate A correcto. Un `grep` informativo vacío detuvo el primer monitor host; se reanudó sólo la observación, sin otro candidato. El retorno nativo no se había detenido. Los comandos informativos del monitor ya no deben abortarlo.

Evidencia: `.work/halium24-adsp-boot/`, `test-adsp.py` y regresión de captura ante fallo del helper. Una eventual ampliación de raíz necesita respaldo y comprobaciones propios; no reactivar el resize automático como atajo.

**Halium25 corrigió la sesión D-Bus y el portal KDE sin introducir KWin:**

- El launcher Wayfire creaba un segundo bus mediante `dbus-run-session`, mientras `startplasmamobile` iniciaba unidades del usuario antes de importar el entorno gráfico. El portal intentaba usar `xcb` y fallaba; el bus privado no encontraba `org.freedesktop.systemd1`.
- Los dos helpers diagnósticos reutilizan el bus PAM existente e importan sólo las variables Wayland/Qt/KDE necesarias antes de arrancar los servicios. `startkderc` fija `systemdBoot=false`: el [código de Plasma fijado](https://raw.githubusercontent.com/droidian/plasma-workspace/c41cc1c/startkde/startplasma.cpp) elige por defecto el arranque systemd si está disponible, y el target instalado requiere KWin. `KDE_NO_KWIN=1` por sí solo no protege esa ruta.
- La captura nativa confirmó portal activo durante más de 100 segundos, Plasma/Maliit/systemd en el mismo bus y procesos Wayfire/plasmashell sin KWin. IPC conserva las superficies; ADSP y telemetría de batería también. Los proxies X11 `xembedsniproxy`/`gmenudbusmenuproxy` todavía fallan por `xcb`; no declarar resuelta toda la integración gráfica.
- Captura completa y rescate A sin intervención física. RNDIS volvió a enumerar después de un timeout inicial; el sondeo host de un minuto no lo había visto. No confundir una muestra ausente con una regresión USB permanente.

Evidencia privada: `.work/halium25-session-bus/`. `test-session.py` prueba rechazo de bus/socket/configuración incorrectos y que un fallo de importación no arranque Plasma. Todavía falta validación visible/táctil; los helpers son diagnóstico sobre la raíz existente, no un nuevo paquete reproducido.

**Halium26 validó una terminal nativa dentro de Plasma:**

- QMLKonsole 25.04.0-1 ejecutó el helper como `droidian`, con PID 1 `systemd`, kernel `5.10.209-android13-0-gbd42a1bb7281`, `/dev/pts/0`, `TERM=xterm-256color` y marca final `NATIVE_TERMINAL_PTY_OK`. No es un chroot ni salida por pipes. Wayfire IPC mostró `org.kde.qmlkonsole` mapeada/activa, PID coincidente y título `Terminal — QMLKonsole`.
- **`tmux` no está instalado.** La prueba lo informa explícitamente; no valida sesiones tmux, SSH, entrada táctil ni renderizado de color real. La capa `LockScreen Splash` sigue mapeada: no deducir visibilidad de la terminal sólo por su activación.
- Portal KDE activo durante más de 100 segundos, ADSP `running`, batería 90/290/`Charging` y `HOME_WRITE_OK`. El host vio RNDIS, pero la captura posterior tenía UDC `not attached`/velocidad `UNKNOWN`; estabilidad USB sigue abierta.
- Captura completa a los 137.237 s, reinicio a los 147.158 s, rescate A y ADB recuperados. No se escribieron B/userdata ni se cambió el kernel. Se dejó recovery con la raíz desmontada y el timer desarmado.

Evidencia privada: `.work/halium26-native-terminal/`. Los tests host reprodujeron y corrigieron dos falsos positivos: `set -e` no corta fallos iniciales de una lista `&&`, y una marca anterior al último comando podía anunciar éxito parcial. Después del ensayo se endureció la captura para leer/limpiar el reporte con permisos de `droidian`, no root; fallo de limpieza impide reutilizarlo. Esa última corrección pasó tests host y comprobaciones ARM64 de permisos en chroot, fue instalada con hash verificado, pero **no tuvo otro arranque nativo completo**. No confundir esa comprobación de archivos con la PTY nativa ya validada.

**USB ya tiene evidencia nativa:** el parent role switch `a600000.ssusb-role-switch` estaba en `none`, mientras recovery usa `device`. Halium19 seleccionó `device` desde el helper diagnóstico: UDC `configured/high-speed`, host `rndis_host` a 480 Mb/s y respuesta ICMP del teléfono por IPv6 link-local, sin modificar la red del host. No demuestra SSH, USB 3, modo host, PD ni hotplug. El helper rechaza rol host y UDC ocupado; revierte su cambio de rol si falla.

Evidencia privada: `.work/halium18-egl-maps/` y `.work/halium19-usb-role-egl/`. El rescate de Halium19 se detuvo antes de DTBO por inodos agotados en `/tmp` del host; se completó el mismo rescate usando `TMPDIR` en el workspace antes de reiniciar. No se arrancó el conjunto parcial ni se escribió userdata/B. Exportar ese scratch también para Fastboot, no sólo para tests. GDB se retiró para el ensayo de permisos Halium20.

Halium20/21 también completaron captura y rescate. En Halium21 la captura terminó a los 136.6 s, pero el reinicio llegó a los 314 s por la fase de parada; no fue un nuevo bootloop ni fallo de captura. Conservar un tiempo de espera acotado que incluya shutdown. Evidencia adicional: `.work/halium20-gpu-access/`, `.work/halium21-stock-gpu-firmware/`.

Acceso autenticado: el launcher USB limitado tiene pruebas host, pero **no está instalado ni probado nativamente**. El hook de credenciales rechazó la preparación completa; no se intentó evadirlo ni habilitar una shell sin autenticación. El Dropbear existente es de 2016 y sólo se contempló como bootstrap acotado por cable; no es aceptable para la imagen diaria. En ese ensayo Docker también rechazaba el acceso al socket; el acceso se resolvió después, sin que eso pruebe un rebuild del nuevo paquete de adaptación. La regla GPU sí tiene evidencia directa en el teléfono.

El sondeo RNDIS independiente de LXC usa [configfs upstream](https://docs.kernel.org/usb/gadget_configfs.html), controlador real y gadget propio, sin ocupar uno ajeno. Halium14 falló al escribir un nombre fijo de interfaz; Halium15, usando el nombre asignado por el kernel, logró el bind y creó `usb0` con IP. **En ese ensayo todavía no había enumeración en el host:** crear la interfaz no demuestra conexión física; Halium19 la confirmó después. No se agregó SSH, DHCP ni reenvío.

Evidencia privada: `.work/halium13-full-userspace/`, `.work/halium14-usb-android-capture/`, `.work/halium15-native-vendor-modules/`, `.work/halium16-lxc-module-bind/` y `.work/halium17-wayfire-gdb/`. Todos completaron captura y rescate automático. Se conservan kernel, ramdisk y raíz; los siguientes cambios son de integración, no otro ZIP completo.

## Conclusión histórica del 4 de septiembre

Tenemos rootfs, paquetes de Plasma y acceso de recuperación. **Todavía no tenemos evidencia de `systemd` como PID 1 de Droidian.** El primer kernel `eqs` carece de opciones básicas de Halium y la recolección de logs de los intentos posteriores fue insuficiente. No hay evidencia para atribuir todos los fallos a USB, al firmware o a Plasma.

La siguiente implementación debe corregir la configuración del kernel `eqs` y permitir localizar el corte del arranque. Reutilizaremos la rootfs instalada y el conjunto Plasma 6.3.x ya empaquetado; no hace falta actualizar a 6.5 ni reconstruir todo el ZIP para cada prueba.

## Problemática original — diagnóstico del 4 de septiembre

**Escribir una imagen y arrancar un sistema son dos cosas distintas.** Fastboot pudo escribir particiones y la recovery pudo leer la rootfs Droidian, pero falta demostrar que el teléfono complete esta cadena:

```text
bootloader → kernel eqs + componentes vendor → initramfs Halium
           → rootfs Droidian en UFS → systemd → Android/HWC → Plasma Mobile
```

El corte exacto no está localizado para cada candidato. El logo de Motorola, la pantalla negra, el bootloop o el mensaje de Android Recovery son síntomas, no pruebas de que Plasma haya empezado ni de que el almacenamiento esté corrupto. El pedido de factory reset no es un diagnóstico de la rootfs Linux: aceptarlo borraría lo que queremos conservar.

Hay dos problemas concretos que resolver juntos: **compatibilidad del arranque** y **logs suficientes para saber hasta dónde llegó**. El kernel `eqs` compilado carece de opciones Halium necesarias. Los intentos alternativos combinaron kernels y componentes distintos: `eqs` 5.10.209, stock 5.10.218 y referencia bronco 5.10.252. Que compartan SoC no garantiza compatibilidad de módulos, device trees ni firmware. Sin una combinación coherente y trazas válidas, otro flash no permite distinguir qué se corrigió o qué se rompió.

La recuperación también está acoplada al experimento: su imagen no contiene kernel y usa el de `boot_a`. Un candidato defectuoso puede dejar sin arranque normal y sin ADB en recovery a la vez. El último rescate comprobado usa kernel stock y recovery v14; **eso es un entorno Android de diagnóstico, no Droidian funcionando**. Slot B tampoco sirve hoy como respaldo automático.

Por eso la tarea inmediata no es reinstalar Plasma ni volver a Android: es obtener un arranque Linux nativo identificable, conservando la rootfs. Después podremos depurar la integración gráfica con evidencia propia.

## Qué está demostrado

| Hallazgo | Evidencia local | Consecuencia |
|---|---|---|
| Al kernel `eqs` le faltan `DEVTMPFS`, `SYSVIPC` y `PID_NS`; `IPC_NS` no está habilitado. | `.work/eqs-kernel/out/.config` y la configuración dentro de `eqs-dev-packages/runs/one/root/image/boot/`. | El build validaba símbolos de la placa, no los requisitos de Droidian. Corregir antes del próximo candidato. |
| Se inspeccionó un directorio pstore sin demostrar su montaje. Una captura confirma que no estaba montado. | `.work/target-recovery-diag-20260904-1458/state.txt`, sección `MOUNTS`. | «pstore vacío» no permite concluir que el kernel no ejecutó o no dejó registros. |
| El candidato monolítico tenía `PSTORE_CONSOLE` desactivado. | `.work/eqs-monolithic-kernel/v1/build/.config`. | No se podía esperar una consola persistente después de un cuelgue/reset. |
| Errores de hsphy, PS5169 y eUSB2 también aparecen en recovery con ADB funcional. | `.work/target-monolithic-pstore-20260904-171052/recovery-dmesg.txt`. | Esos mensajes aislados no identifican la causa del bloqueo. |
| El monolítico usó fuente/configuración `bronco`, sin adaptación de placa `eqs` demostrada, y omitió el override de módulos de esa referencia. | `.work/eqs-monolithic-kernel/v1/`; `reference/repos/droidian-devices/linux-android-lenovo-bronco/debian/initramfs-overlay/override/modules.load`. | No fue una reproducción completa del método de bronco ni un control válido de compatibilidad `eqs`. |
| La rootfs en UFS se pudo montar desde recovery; existe el ejecutable `systemd`. | `.work/target-recovery-diag-20260904-1458/`. | Conservarla. Poder montar archivos o ejecutar un chroot no demuestra arranque nativo. |
| La recovery diagnóstica no contiene kernel propio. | Cabecera v4 de recovery: `kernel_size=0`; v14 funcionó al restaurar `boot_a` stock. | Un kernel fallido en `boot_a` puede inutilizar también la recovery. |

La [guía de adaptación del kernel de Droidian](https://docs.droidian.org/porting-guide/kernel-compilation/) exige devtmpfs y namespaces adecuados. Nuestro `/init` de Halium intenta montar devtmpfs explícitamente. Es una incompatibilidad estática concreta, **no una prueba de que sea la única causa de todos los intentos fallidos**.

La [documentación de ramoops](https://docs.kernel.org/admin-guide/ramoops.html) distingue el almacenamiento persistente de su lectura mediante pstore: hay que verificar productor, región reservada y montaje. Los reinicios posteriores pueden reemplazar registros. No prometemos recuperar ahora el primer fallo.

### Contraste local de la revisión externa

Se leyó el plan `PLAN-BRINGUP-EQS-REVISADO.md` aportado por Eduardo y se contrastaron sus hallazgos nuevos con el working tree y el initramfs extraído, sin ejecutar operaciones de almacenamiento ni acceder al teléfono:

- **Inventario inconsistente confirmado:** `out/modules.order` declara 317 módulos in-tree, pero hay 319 `.ko`. Los extras `drivers/gpu/drm/msm/msm.ko` y `sound/soc/codecs/snd-soc-hdmi-codec.ko` también están en el paquete generado. `CONFIG_DRM_MSM` está desactivado en la configuración efectiva y empaquetada. El `find` posterior a `modules_install` los reincorpora, y ambos tienen el `vermagic` esperado. Es un defecto de selección del paquete; no demuestra que se hayan cargado ni causado el bootloop.
- **Consola incompleta:** la configuración `eqs` también desactiva `CONFIG_VT`. Agregar `console=tty0` no basta por sí solo: comprobar soporte, `/dev/console` y parámetros efectivos, no sólo la cadena del header.
- **Protección LVM pendiente:** en el initramfs fijado, si no aparece el LV, se continúa por una ruta de montaje y `e2fsck -y` sobre `userdata`. También hay resize automático condicionado por `var/lib/halium/requires-lvm-resize`. El perfil diagnóstico debe detenerse ante el LV ausente y omitir reparación/resize automáticos. No hay evidencia de que esas rutas hayan dañado esta unidad.
- **Orden previo a PID 1:** el mapeo de `super` y los mounts vendor ocurren antes de buscar LVM. Desactivar LXC en systemd no elimina esos pasos del initramfs. LVM ya se intenta por defecto (`use_lvm="yes"`); añadir `droidian.lvm.prefer` no corrige una búsqueda deshabilitada.

La evidencia de inventario está en `.work/eqs-kernel/out/` y `eqs-dev-packages/runs/one/root/image/`; el comportamiento de arranque se confirmó en el `scripts/halium` extraído y en su [fuente fijada e515727](https://github.com/droidian/initramfs-tools-halium/blob/e515727c13ddf1cfbcc2596046f4451cb2e2a377/scripts/halium). Halium2 incorpora consola Linux y protección LVM, verificadas en host. El empaquetador ya rechaza módulos residuales o ausentes antes de Docker/limpieza y dejó de recopiarlos mediante `find out`; el paquete real pasó config embebida y CRC de símbolos; falta HIL. El perfil Kconfig compartido y el rechazo de configuraciones incompletas ya están implementados; la resolución, compilación y empaquetado con la toolchain fijada pasaron.

## Base que conservamos

- **Firmware:** RETAR Android 14 `U1SQS34.52-21-1-16`, que ya arrancó stock en esta unidad. La fuente `eqs` fijada corresponde a otra revisión; esa compatibilidad sigue pendiente, no justifica otro downgrade a ciegas.
- **Recuperación:** último estado registrado, slot A con `boot_a` stock y recovery v14 con ADB root. El transporte informa `recovery`, no `device`. Debe reconfirmarse al retomar.
- **Rootfs:** Droidian 101, snapshot `101.20251130`, en `userdata`/LVM. Sin wipe ni factory reset. No hay cifrado de producción validado.
- **Interfaz:** `plasma-mobile-wf` 6.3.3, `plasma-workspace` 6.3.4, Wayfire 0.9.0, Maliit y XWayland; sin Phosh/Phoc. Versiones completas en `.work/eqs-rootfs/inspection/PACKAGES.tsv`.
- **Fuentes:** kernel `eqs` `bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582`; bronco `3d1ed931716f88d002207b03db5f0a77e762b921` sólo como referencia de implementación y empaquetado.

**Slot B no es un respaldo stock válido:** hay evidencia de una cadena de sistema/verificación incoherente. Ambos slots comparten `userdata`. Restaurar solamente `boot_a` permite recuperar el entorno diagnóstico conocido, pero no equivale a restaurar Android completo. Ver [recuperación](RECOVERY.md).

## Ensayo físico del 5 de septiembre

Halium2 quedó en el logo sin USB. Se restauró el conjunto de rescate A y se recuperó ADB root en recovery v14: el rescate combinado ya fue ejecutado con éxito, sin escribir userdata/B. Pstore montado explícitamente entregó `console-ramoops-0` (36 375 bytes), con actividad de drivers y botones hasta aproximadamente 689 segundos, sin marcas EQS ni un panic concluyente. Algunos bytes están dañados: no atribuir todos los mensajes a una causa única.

El bootloader agrega `quiet`; las marcas kmsg sin prioridad explícita usan nivel 4 y pueden quedar fuera de la consola persistente. Halium3 conserva kernel/módulos/DT de Halium2 y añade marcas de prioridad 3 antes/después de las etapas tempranas del initramfs. Es un ensayo para localizar el corte, no una reparación de arranque ya demostrada. Evidencia privada: `.work/halium2-rescue-20260905T110633Z/` y `.work/halium3-early-trace/`.

### Halium3: raíz montada, transición a PID 1 por localizar

La captura siguiente (`.work/halium3-rescue-20260905T111502Z/pstore/console-ramoops-0`, 68 056 bytes) contiene marcas inequívocas de Halium3: UFS `/dev/sde31`, vendor, LV `/dev/droidian/droidian-rootfs`, montaje de raíz completado y modo `halium`. `mountroot` retorna a los 3,525 segundos; su rc=1 puede provenir del último condicional de logging bajo `quiet`, no demuestra un error del mount.

Desde recovery se montó la raíz `ro,noload`: journal persistente vacío, `/init` ausente, enlace `/sbin/init` válido y `systemd --version` ejecutable mediante chroot. Se desmontó antes de reiniciar. No se reparó ni redimensionó el filesystem.

Halium4 agrega trazas posteriores al montaje y de validación/handoff, corrige la prioridad del marcador HANDOFF y eleva el nivel de consola desde initramfs. Mantiene el kernel y habilita logging debug de systemd. **Native PID 1 y Plasma todavía no están confirmados.**

### Halium4: fallo concreto de consola en run-init

Pstore (`.work/halium4-rescue-20260905T112429Z/`, 181 657 bytes) registra `run-init: opening console: No such device` al validar cada init, seguido de `No init found`. El problema no es que falte systemd: se aborta antes de validar el ejecutable por la consola no operativa.

Halium5 usa `run-init -c /dev/null` tanto en validación `-n` como en el handoff, y elimina la redirección shell a `/dev/console` que podía fallar antes de ejecutar run-init. Systemd conserva logging explícito a kmsg. Es un fallback de diagnóstico sin terminal interactiva, no una consola gráfica reparada. Regresión host RED/GREEN conserva rechazo de init inexistente. Kernel, módulos y rootfs no cambian; prueba física en curso.

## Plan de ejecución

### 1. Recuperar evidencia sin otro flash

En la próxima sesión de diagnóstico autorizada, usar v14 tal como está: comprobar `/proc/mounts`, montar pstore si falta y copiar sus registros **antes de reiniciar**. Registrar versión de kernel, modo de arranque y hashes de las particiones relevantes, sin volcar identificadores privados al repositorio.

Verificar también la rootfs en sólo lectura y el ejecutable/loader de su init. Si hace falta un smoke test de chroot, usarlo sólo para descartar un problema de archivos o ABI, no como sustituto de Droidian nativo.

**Resultado esperado:** captura válida o constancia precisa de por qué no hay registros. No crear recovery v15 salvo un defecto nuevo y demostrado en v14.

### 2. Corregir el kernel específico de `eqs`

**Avance host:** Halium2 completó configuración, kernel, DTB/DTBO y 331 módulos; paquetes e imágenes dev2 reproducidos dos veces. El paquete comprueba config embebida, inventario y CRC de símbolos. El initramfs se detiene ante LVM ausente, omite repair/resize, registra etapas y conserva módulos mediante tmpfs `/run` para sobrevivir a `run-init`. Se preparó un [bundle A-only con rescate](../port/bringup/README.md). Pendientes: ensayo físico, acceso nativo independiente de gráficos y estabilidad Plasma. No se equipara el bundle a una imagen daily validada.

Partir del pipeline `eqs` que ya compila, no de `bronco_defconfig`:

1. Hacer que `port/kernel/resolve-eqs-config.sh` y `port/kernel/build-host-artifacts.sh` consuman el mismo perfil mínimo Halium con la toolchain del build. Validar **fragmentos → configuración resuelta → kernel → configuración empaquetada**, incluyendo devtmpfs, consola, IPC/namespaces y requisitos del `systemd`/LXC presente.
2. Conservar pstore RAM y consola; comprobar que el DT utilizado reserva la misma región que lee la recovery. Añadir marcas de avance en initramfs antes de los pasos que pueden bloquearse.
3. Reconstruir kernel y módulos afectados con la misma fuente, configuración y toolchain. Empaquetar desde inventarios vigentes y staging limpio, sin recorrer indiscriminadamente outputs reutilizados ni fijar el conteo 333 como prueba de corrección. Identificar explícitamente los módulos externos. Revisar dependencias y versiones de símbolos, y rechazar `--reuse-gates` si no corresponde al perfil validado; no forzar cargas incompatibles.
4. Empaquetar sólo el conjunto de arranque necesario y coherente (`boot`, ramdisk/módulos y DT de `eqs`). Conservar firmware y componentes no afectados. Una modificación de kernel no implica que sea seguro actualizar únicamente `boot` dejando módulos incompatibles.

**Prueba host:** rechazar configuración incompleta, módulos fuera de inventario y mezcla de perfiles; comprobar correspondencia de kernel/configuración/módulos, y `/init`, intérprete y dependencias en el ramdisk compuesto. Ejercitar con mocks el fallo LVM y demostrar que no llama a reparación ni resize. Nunca ejecutar ese test sobre un dispositivo de bloques real. Compilar es necesario, no demuestra arranque.

ThinLTO+CFI ya compila en este host: no imponer Full LTO como tarea previa sin una necesidad demostrada. Hacer drivers built-in sólo si un fallo de carga lo exige. Si se adopta un kernel realmente monolítico, incluir su política de no cargar módulos vendor; no copiar únicamente el `Image` de bronco.

### 3. Obtener un arranque nativo depurable

Probar el candidato con autorización de flash, por cable directo y con rescate preparado. Antes de pedir intervención física, identificar candidato/hashes, cambio mínimo, hipótesis, evidencia esperada y rescate de todas las piezas alteradas. Conservar la rootfs instalada y aplicar la política diagnóstica de detenerse ante LVM ausente, sin reparación ni resize automático. Las primeras correcciones y sus pruebas son host-only y no necesitan fastboot.

Localizar el último punto confirmado:

```text
kernel eqs → /init Halium → módulos/UFS → super/vendor → LVM/rootfs → systemd PID 1
```

Primero iniciar sin sesión gráfica ni autoarranque de LXC; revisar las unidades reales, porque `multi-user.target` no garantiza excluir el contenedor. Instrumentar entrada/salida de las operaciones críticas y fallos de módulos imprescindibles. Recuperar consola persistente y journal acotado después de cada intento; no repetir un flash sin evidencia nueva. La rootfs actual rechaza `openssh-server`; preparar acceso temporal por clave, restringido al USB directo y sin publicar credenciales, antes de esperar una shell por SSH. Usar [devtools](https://docs.droidian.org/porting-guide/debugging-tips/) del snapshot cuando corresponda, sin rehacer toda la raíz.

**Aprobación:** kernel del candidato identificado, raíz Droidian en UFS, `systemd` realmente como PID 1 y shell utilizable. Si sólo falla USB, no retroceder a cambiar todo el arranque: revisar el UDC, rol y configuración gadget finales, comparándolos con la recovery funcional.

### 4. Levantar Plasma Mobile 6

Con el arranque nativo confirmado:

1. Validar el contenedor Android/Halium: mounts vendor, binder, servicios y acceso a blobs. Resolver incompatibilidades concretas con el firmware conservado.
2. Probar la cadena gráfica libhybris/HWC y luego Wayfire + `plasma-mobile-wf` con los paquetes ya presentes. No introducir KWin, Phosh ni otro escritorio como desvío.
3. Conseguir pantalla interna, touch y terminal; después Wi-Fi, SSH saliente y teclado USB.

**Aprobación:** Plasma visible y controlable en el teléfono; abrir una terminal y realizar una conexión SSH real. El arranque de servicios sin imagen/entrada física no alcanza.

### 5. Convertir lo que funciona en una imagen instalable

Reproducir en el builder la combinación **realmente ensayada**, generar manifiesto/hashes y probar instalación y recuperación. Corregir antes el flasher: la ruta probada para cargar rootfs fue FastbootD. La receta versionada usa transferencia por Fastboot y los cambios locales experimentales usan telnet; ambas variantes modifican los slots y `userdata`, y ninguna es el procedimiento para continuar el diagnóstico.

No ejecutar el viejo `flash_all.sh` para iterar. Un ZIP que Fastboot acepta no es todavía un SO que arranca. Cifrado, endurecimiento, suspensión y dock completo siguen después del primer port usable; una imagen de desarrollo no se presenta como daily segura.

## Qué cambia respecto de los intentos anteriores

- Medir progreso por **PID 1 nativo → Plasma con touch → terminal/SSH**, no por cantidad de imágenes generadas.
- No tratar pantalla negra, ausencia de USB o directorio pstore vacío como prueba de una causa específica.
- No reconstruir la rootfs ni cambiar firmware, kernel, módulos y ramdisk simultáneamente sin explicar la dependencia.
- Cada prueba debe conservar identificación del candidato, particiones modificadas, hipótesis y resultado; alcanza una nota junto a sus logs, sin crear otro framework.
- Si una prueba no deja evidencia interpretable, arreglar la captura antes de otro intento. Pedir diagnóstico upstream con un caso reducido si el fallo queda localizado fuera de lo que podemos resolver; no publicar logs privados sin revisión y autorización.

**Próxima unidad de trabajo vigente:** [prueba manual del preview H27 y acceso nativo persistente](#plan-operativo-desde-halium26), conservando el espacio ya corregido. Completar bloqueo/touch y trabajo SSH/tmux. Halium2 queda como antecedente, no como candidato a repetir.

## Alcance de la publicación original

La publicación original contenía el diagnóstico y el plan, no una nueva imagen ni una corrección del kernel. Las rutas `.work/` identifican evidencia conservada sólo en el workspace; firmware, logs privados y binarios no se incluyen en Git. Los cambios experimentales de los builders y los helpers locales de `tools/` requieren revisión separada; esta actualización documental no los declara publicados ni validados como release.
