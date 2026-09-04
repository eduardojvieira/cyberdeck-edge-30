# Camino corto a Droidian + Plasma Mobile en `eqs`

Análisis del 4 de septiembre de 2026. **El objetivo es arrancar Droidian nativo con Plasma Mobile 6 en el Edge 30 Ultra**, no construir otra recovery ni cambiar de distribución. Esta revisión usa fuentes locales, capturas previas del teléfono y documentación upstream; no incluye un nuevo ensayo físico.

## Conclusión

Tenemos rootfs, paquetes de Plasma y acceso de recuperación. **Todavía no tenemos evidencia de `systemd` como PID 1 de Droidian.** El primer kernel `eqs` carece de opciones básicas de Halium y la recolección de logs de los intentos posteriores fue insuficiente. No hay evidencia para atribuir todos los fallos a USB, al firmware o a Plasma.

La siguiente implementación debe corregir la configuración del kernel `eqs` y permitir localizar el corte del arranque. Reutilizaremos la rootfs instalada y el conjunto Plasma 6.3.x ya empaquetado; no hace falta actualizar a 6.5 ni reconstruir todo el ZIP para cada prueba.

## Problemática actual

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

## Base que conservamos

- **Firmware:** RETAR Android 14 `U1SQS34.52-21-1-16`, que ya arrancó stock en esta unidad. La fuente `eqs` fijada corresponde a otra revisión; esa compatibilidad sigue pendiente, no justifica otro downgrade a ciegas.
- **Recuperación:** último estado registrado, slot A con `boot_a` stock y recovery v14 con ADB root. El transporte informa `recovery`, no `device`. Debe reconfirmarse al retomar.
- **Rootfs:** Droidian 101, snapshot `101.20251130`, en `userdata`/LVM. Sin wipe ni factory reset. No hay cifrado de producción validado.
- **Interfaz:** `plasma-mobile-wf` 6.3.3, `plasma-workspace` 6.3.4, Wayfire 0.9.0, Maliit y XWayland; sin Phosh/Phoc. Versiones completas en `.work/eqs-rootfs/inspection/PACKAGES.tsv`.
- **Fuentes:** kernel `eqs` `bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582`; bronco `3d1ed931716f88d002207b03db5f0a77e762b921` sólo como referencia de implementación y empaquetado.

**Slot B no es un respaldo stock válido:** hay evidencia de una cadena de sistema/verificación incoherente. Ambos slots comparten `userdata`. Restaurar solamente `boot_a` permite recuperar el entorno diagnóstico conocido, pero no equivale a restaurar Android completo. Ver [recuperación](RECOVERY.md).

## Plan de ejecución

### 1. Recuperar evidencia sin otro flash

En la próxima sesión de diagnóstico autorizada, usar v14 tal como está: comprobar `/proc/mounts`, montar pstore si falta y copiar sus registros **antes de reiniciar**. Registrar versión de kernel, modo de arranque y hashes de las particiones relevantes, sin volcar identificadores privados al repositorio.

Verificar también la rootfs en sólo lectura y el ejecutable/loader de su init. Si hace falta un smoke test de chroot, usarlo sólo para descartar un problema de archivos o ABI, no como sustituto de Droidian nativo.

**Resultado esperado:** captura válida o constancia precisa de por qué no hay registros. No crear recovery v15 salvo un defecto nuevo y demostrado en v14.

### 2. Corregir el kernel específico de `eqs`

Partir del pipeline `eqs` que ya compila, no de `bronco_defconfig`:

1. Añadir un fragmento mínimo Halium a `port/kernel/resolve-eqs-config.sh` y `port/kernel/build-host-artifacts.sh`. Validar la configuración **resuelta**, no sólo el texto del fragmento: devtmpfs, IPC/namespaces y requisitos del `systemd`/LXC efectivamente empaquetado.
2. Conservar pstore RAM y consola; comprobar que el DT utilizado reserva la misma región que lee la recovery. Añadir marcas de avance en initramfs antes de los pasos que pueden bloquearse.
3. Reconstruir kernel y módulos afectados con la misma fuente, configuración y toolchain. Preparar un staging de módulos limpio y revisar su ABI y dependencias. No cargar módulos stock con un kernel incompatible ni forzar su aceptación.
4. Empaquetar sólo el conjunto de arranque necesario y coherente (`boot`, ramdisk/módulos y DT de `eqs`). Conservar firmware y componentes no afectados. Una modificación de kernel no implica que sea seguro actualizar únicamente `boot` dejando módulos incompatibles.

**Prueba host:** el chequeo debe rechazar la configuración original, aceptar la corregida y verificar que el paquete contiene esa configuración y módulos correspondientes. Compilar es necesario, no demuestra arranque.

ThinLTO+CFI ya compila en este host: no imponer Full LTO como tarea previa sin una necesidad demostrada. Hacer drivers built-in sólo si un fallo de carga lo exige. Si se adopta un kernel realmente monolítico, incluir su política de no cargar módulos vendor; no copiar únicamente el `Image` de bronco.

### 3. Obtener un arranque nativo depurable

Probar el candidato con autorización de flash, por cable directo y con rescate preparado. Conservar la rootfs instalada; cambiar un conjunto mínimo con una hipótesis explícita.

Localizar el último punto confirmado:

```text
kernel eqs → /init Halium → UFS y dispositivos → LVM/rootfs → systemd PID 1
```

Primero iniciar sin sesión gráfica para separar fallos. Recuperar consola persistente y logs de userspace después de cada intento; no repetir un flash sin evidencia nueva. El canal de depuración debe existir explícitamente: la rootfs actual incluye cliente SSH, pero rechaza `openssh-server`, y el telnet de emergencia no es un indicador universal de arranque. Para desarrollo, habilitar sólo el acceso temporal necesario, restringido al USB directo y sin secretos. Droidian documenta esta diferencia entre imágenes con y sin [devtools](https://docs.droidian.org/porting-guide/debugging-tips/).

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

**Próxima unidad de trabajo:** fragmento Halium `eqs` + comprobación de configuración/paquete + initramfs observable. La primera acción sobre el teléfono será recoger pstore correctamente, no otro flash completo.

## Alcance de esta publicación

Este commit publica el diagnóstico y el plan, no una nueva imagen ni una corrección del kernel. Las rutas `.work/` identifican evidencia conservada sólo en el workspace; firmware, logs privados y binarios no se incluyen en Git. Los cambios experimentales de los builders y los helpers locales de `tools/` quedan fuera de este commit y requieren revisión separada.
