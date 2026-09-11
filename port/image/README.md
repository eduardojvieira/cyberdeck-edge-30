# Imagen limpia con los arreglos acumulados

`build.sh` compone una **preview**, no una copia del teléfono ni una daily.
Reutiliza el arranque H29 probado; no recompila otro kernel durante la
consolidación. La imagen nueva requiere una validación física propia.

**Receta actualizada el 11 de septiembre:** fija Plasma `+eqs5`, con fechas
sensibles al idioma y textos españoles del bloqueo. El paquete se comprueba
con Qt 6.8.2; **el ZIP del 10 de septiembre conserva `+eqs4` y no fue modificado**.
Hace falta una nueva construcción/validación para obtener un ZIP con este cambio.

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
cero ni ZIP byte-idéntico (UUID/LVM/ext4/timestamps). Conservar `inputs/` privado
junto al ZIP. Manifiesto final: fuentes, paquetes, inputs, geometría y hashes.
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
