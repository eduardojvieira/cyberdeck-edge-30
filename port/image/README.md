# Imagen limpia con los arreglos acumulados

`build.sh` compone una **preview**, no una copia del teléfono ni una daily.
Reutiliza el arranque H29 probado; no recompila otro kernel durante la
consolidación. La imagen nueva requiere una validación física propia.

**Receta base del 11 de septiembre:** fija Plasma `+eqs5`, con fechas
sensibles al idioma y textos españoles del bloqueo. El paquete se comprueba
con Qt 6.8.2; **el ZIP del 10 de septiembre conserva `+eqs4` y no fue modificado**.
Hace falta una nueva construcción/validación para obtener un ZIP con este cambio.

## Cohorte actual (28 de septiembre)

La variante `current` parte de la misma base limpia y del **mismo boot H29**.
Instala offline 1777 `.deb` exactos de la actualización comprobada en el
teléfono: Plasma Mobile/Workspace 6.7.5 adaptados, QScreen, libhybris para
glibc 2.43, Qt/KDE y aplicaciones Sid. Conserva las versiones y los 258 holds
de [`port/apt/`](../apt/), incluido Mesa 25.0.7-2. Activa el ocultamiento de
paneles y `es_AR.UTF-8`. No reconstruye el kernel ni copia `/home` vivo.

```sh
sudo port/build-eqs-rootfs.sh --consolidated "$PWD/.work/eqs-current-build" replacement current
```

Salida temporal: `build/eqs-current-20260928.zip` y `build/SHA256SUMS` bajo la
carpeta nueva. No hace falta conservar el ZIP después de verificarlo si los
inputs locales y la receta permanecen disponibles.

`current-packages.json` fija rutas privadas y SHA-256 de los `.deb`;
`current-package-versions.tsv` es el inventario **sólo de paquetes instalados**
(estados `ii`/`hi`). `current-protected-versions.tsv` fija el subconjunto de
riesgo y `current-{auto,manual}-packages.txt` conserva la distinción APT
automático/manual.
Se rechazan inputs ausentes o alterados, una transacción irresoluble,
versiones distintas y holds faltantes. La instalación usa un índice APT local,
sin red, y mantiene bloqueados los scripts que intenten iniciar servicios o
flashear. El ZIP no contiene los `.deb` temporales ni los datos personales.
Aunque la cohorte incluye `openssh-server` del perfil de desarrollo, el servicio
queda deshabilitado y las host keys se eliminan de la imagen limpia.
Estos SHA fijan los binarios locales, pero no sustituyen una firma de origen;
las fuentes/parches de las cuatro adaptaciones propias se documentan en
[`UPGRADE-6.7.md`](../plasma-mobile-wf/UPGRADE-6.7.md).

**No es una réplica completa del teléfono.** Los archivos exactos de seis
paquetes instalados no están conservados: `byobu`, `hollywood` (depende de
`byobu`), `code`, `ghostty`, `onlyoffice-desktopeditors` y `python3-newt`.
La receta los enumera en `current-missing-packages.tsv` y en el ZIP, sin
reemplazarlos por versiones parecidas ni exportar binarios desde el teléfono.
La receta tampoco incluye Flatpaks, imágenes/datos de Waydroid, Homebrew,
cuentas, plugins ni configuración personal. Para una réplica completa hacen
falta los `.deb` verificables y una reinstalación separada de esas capas.

Esta cohorte se ensaya **en host**. Aunque un ZIP pase hashes, `dpkg --audit`,
`apt-get check` y fsck, sigue sin validación de arranque limpio, gráficos,
periféricos y recuperación en el Edge. No flashearlo como daily cifrada.

**Build host del 28/9:** 22 inputs base y 1777 paquetes SHA verificados;
simulación/instalación offline de 1094 upgrades, 682 altas y seis retiros
previstos; 2054 paquetes finales, 258 holds y selecciones APT 1837 auto /
217 manual. `dpkg --audit`, `apt-get check`, verificador de rootfs, fsck final,
manifiesto ZIP y `unzip -t` pasaron. No hubo acceso ni flash al teléfono.
El ZIP de 5.908.942.990 bytes tuvo SHA-256
`f10e2725b856c8fd589bd49078211557f57322aa59854176013623ec29c9176f`;
es evidencia histórica, no un artefacto publicado ni byte-reproducible.

## Construir

1. Preparar los **22 inputs** de `inputs.json`: rutas locales y SHA-256.
   `stage-inputs.py` los verifica antes de crear la carpeta; no descarga ni
   extrae datos del Edge.
2. Docker, binfmt `qemu-aarch64` e imagen rootfs-builder fijada por digest en
   `build.sh`. Usar privilegios aprobados; no abrir permisos del socket Docker.
3. `port/build-eqs-rootfs.sh --consolidated NUEVA_CARPETA replacement` para
   el repuesto de Eduardo, o `stock` para pantalla original.
4. Revisar `build.log`, `build/rootfs-green.log`, `build/fsck-final.log` y
   `build/SHA256SUMS`; ZIP en `build/eqs-preview-20260910.zip`.

Contenedor sin red, código/inputs readonly y salida nueva. Sólo loop/LVM para
esa imagen regular; rechaza un VG Droidian existente/mapeado, filtra LVM al loop
propio y desmonta/desactiva al terminar o fallar. No contiene ADB/fastboot ni
actúa sobre el teléfono. No sobrescribe salidas anteriores.

## Contrato de la receta

| Componente | Integración |
|---|---|
| Arranque | Boot/vendor_boot/DTBO/vbmeta H29 exactos en ZIP y `/boot`; rescate A aparte. |
| Halium | Módulos nativos en LXC después de vendor_dlkm; mount super-modem readonly corregido. |
| GPU/medios | Seis blobs stock GPU, KGSL, audio/cámara/EVA y política cape. Sin Bronco. |
| Plasma | ARM64 eqs5, fechas localizadas, bus PAM único, portal, PAM/IPC, botones, gestos y rotación bloqueable. |
| Ventanas | 200 %, horizontal bloqueado, maximización genérica y timeout 1000 ms. |
| Teclado/fondo | OSK manual Maliit y fondo de bloqueo siguiendo el escritorio. |
| Cámara | Qt5 privado ABI exacto, launcher exclusivo y fallback si cambia Qt. |
| Bluetooth | VHCI/BNEP ABI H29, servicio probado, hook de dirección y UHID root-only. |
| Táctil | Perfil explícito `replacement` 2× o `stock` sin esa calibración. |
| Espacio | PV/LV/ext4 crecidos offline al tamaño de la unidad 256 GB; no resize al iniciar. |
| Mantenimiento | `current`, holds Plasma/kernel y `FLASH_BOOTIMAGE=no`. No Sid/next. |
| Privacidad | Base limpia, machine-id vacío, sin claves/red/IA del usuario. |

La base histórica debe fallar `verify-rootfs.py` por Plasma sin eqs5 (RED);
la imagen montada debe pasar después (GREEN). Se comprueba contenido, no sólo
parches en Git. Dpkg no inicia servicios. No se incluyen timers de captura,
reboots automáticos ni experimentos USB ADC/POR/swap. Loader stock administra ADSP.

## Inputs y reproducibilidad

- Base: userdata del ZIP limpio del 1 de septiembre, identificado por SHA.
- Arranque/rescate: `.work/eqs-h29/boot-bundle/`; fuentes eqs e initramfs en
  `port/kernel/`. Reproduce el **binario validado**, no declara equivalente un
  kernel recompilado con el perfil de desarrollo actual.
- Plasma: `port/plasma-mobile-wf/build-package.sh`, Qt 6.8.2, eqs5.
- Qt5: fuente/parches/tests en `port/qt5-wayland/README.md`.
- VHCI/BNEP: fuente/toolchain/CRC H29 descritos en `docs/BLUETOOTH.md`.
- GPU/RC: stock RETAR -16 local; hashes/transformación en
  `port/bringup/diagnostics/`. No se versionan blobs.

**Un clon Git solo no contiene estos binarios ni firmware.** Esta entrega
reproduce la **composición desde inputs conservados**, no promete build desde
cero ni ZIP byte-idéntico (UUID/LVM/ext4/timestamps). Conservar las rutas privadas
de `inputs.json`; el ZIP generado no necesita guardarse entre builds. Manifiesto
final: fuentes, paquetes, inputs, geometría y hashes.
Los paquetes kernel dpkg conservan etiquetas históricas; no reinstalarlos para
«alinearlos» con el kernel H29 realmente ejecutado.

## Verificación y uso

```sh
python3 port/image/test-image.py
bash -n port/image/build.sh port/image/build-in-container.sh
```

El test host cubre defaults, ajustes preservados, IPC requerido, rechazo de `/`,
enlace escapado y builder antiguo por defecto. `verify-rootfs.py` es read-only
contra la imagen montada; no es un instalador para el teléfono.

La [instalación limpia](INSTALL.md) destruye userdata. ZIP local, no publicado
por el commit/push. Herramientas grandes/cuentas quedan para reinstalación
selectiva en `port/shell/`, no se clonan datos privados. Ver
[release y evidencia](../../docs/RELEASE-20260910.md).
