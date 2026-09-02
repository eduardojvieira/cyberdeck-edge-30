# Repositorios de referencia

Se conservaron doce de los quince repositorios inspeccionados. Los clones son locales, superficiales e ignorados por Git; sirven para comparar fuentes y empaquetado, pero no son todavía entradas de una release.

## Resultado

| Repositorio | Decisión | Rama y commit inspeccionados | Motivo |
|---|---|---|---|
| `eqs-development/android_device_motorola_eqs` | Conservar | `lineage-21` · `d2c017af5ae8` | Árbol específico de `eqs`: firmware Android 14, particiones, AVB, overlays y lista de blobs. |
| `eqs-development/android_device_motorola_sm8475-common` | Conservar | `lineage-21` · `9ef36ec87005` | Configuración compartida de SM8475, boot, módulos, touch, USB, carga y políticas Android. |
| `eqs-development/android_kernel_motorola_sm8475` | Conservar | `lineage-21` · `bd42a1bb7281` | Kernel Android 5.10 correspondiente a la plataforma; debe estudiarse junto con módulos y devicetrees. |
| `eqs-development/android_kernel_motorola_sm8475-modules` | Conservar | `lineage-21` · `9f8d247d4576` | Drivers externos requeridos por el common tree, incluidos display, touch y carga. |
| `eqs-development/android_kernel_motorola_sm8475-devicetrees` | Conservar | `lineage-21` · `f02ca5e3e17f` | Fuentes para DTB/DTBO del conjunto SM8475. |
| `eqs-development/android_device_motorola_bronco` | Conservar | `lineage-21` · `702a35b9c78d` | Referencia chica que conecta el hardware Android de Bronco con su port Droidian; sólo para comparar diferencias con `eqs`. |
| `droidian-devices/linux-android-lenovo-bronco` | Conservar | `droidian` · `3d1ed931716f` | Blueprint activo del paquete kernel, initramfs Halium y bootimage Droidian. No contiene un `eqs_defconfig`. |
| `droidian-devices/adaptation-droidian-bronco` | Conservar | `droidian` · `7207ca1614eb` | Blueprint activo del source package de adaptación API32 y su paquete de configuraciones. |
| `LineageOS/android_vendor_lineage` | Conservar | `lineage-21.0` · `85fbbf9a6601` | Aporta el `merge_dtbs.py` canónico que combina DTB Qualcomm por metadatos de placa y verifica overlays. |
| `LineageOS/android_external_dtc` | Conservar | `lineage-21.0` · `fd8c8a25dac5` | Fuente de `fdtget`, `fdtput`, `fdtoverlay` y `fdtoverlaymerge` exigidas por ese flujo. |
| `aosp-mirror/platform_system_libufdt` | Conservar | `android-platform-14.0.0_r28` · `4cc0d8f7e5d2` | Fuente de `ufdt_apply_overlay` real y `mkdtboimg.py` para el contenedor DTBO de desarrollo. |
| `droidian-images/droidian` | Conservar | `101.20251130` · `d5b764309d9c` | Receta oficial de imagen; sus submódulos fijan `rootfs-templates` `d2212f43e8de` y el template fastboot `b846fa1fa3ec`. |
| `eqs-development/android_device_motorola_zeekr` | Eliminar | `lineage-21` · `3fc1df64595c` | Otro dispositivo; sus diferencias físicas ya están mejor cubiertas por `eqs`, common y Bronco. |
| `eqs-development/proprietary_vendor_motorola_zeekr` | Eliminar | `lineage-20` · `8b66d4e42b9f` | Blobs propietarios de otro teléfono: no son reutilizables ni seguros para `eqs`. |
| `eqs-development/android_kernel_motorola_sm8450` | Eliminar | `lineage-20` · `42fc85e57688` | SoC incorrecto y repositorio archivado; el árbol SM8475 es la referencia aplicable. |

## Cómo usar las referencias

- `eqs-development` aporta la configuración física de `eqs` y el conjunto coherente kernel–módulos–devicetrees.
- Los repos Droidian de Bronco aportan estructura Debian, empaquetado de bootimage e integración Halium.
- El árbol Android de Bronco se conserva únicamente para reconocer qué partes del port Droidian son genéricas de SM8475 y cuáles son específicas del ThinkPhone.
- El submódulo `drivers/lindroid-drm` del kernel Bronco quedó inicializado en `c4b22e21a4cd`; es una pista de la ruta gráfica actual de Droidian, no una decisión cerrada para `eqs`.
- LineageOS y AOSP se usan únicamente como herramientas host fijadas para el merge y validación de DT; no aportan binarios, firmware ni imágenes para `eqs`.
- El build de rootfs usa el checkout Droidian fijado y el builder `quay.io/droidian/rootfs-builder@sha256:749133320ea6d913989005ac8519630059dac465dd91d7be95066255b0ba434e`; no se sigue `next`.

No copiar imágenes, módulos, DTB/DTBO, firmware ni overlays de Bronco o Zeekr. Tampoco copiar en bloque sus reglas udev, `build.prop`, audio, térmica, telefonía, Phosh, Waydroid o el marcador de cifrado: cada pieza necesita justificación y prueba en `eqs`.

## Ubicación y tamaño

Los doce clones retenidos viven bajo `reference/repos/`. Todos fueron clonados con `--depth 1 --single-branch`; el submódulo Lindroid también es superficial.

## Preflight de checkout limpio

Antes de cualquier build de kernel o adaptación en un checkout limpio, ejecutar:

```sh
reference/bootstrap-build-sources.sh
```

El script sólo crea o verifica los ocho inputs fijados de `eqs`/SM8475, LineageOS y AOSP que usan esos builds; un clon existente debe estar limpio y en el commit exacto. No incorpora Bronco ni Zeekr. Droidian no forma parte de este preflight: `port/build-eqs-rootfs.sh` lo bootstrappea automáticamente en su commit fijado.

## Actualización deliberada

Actualizar un clon cambia la evidencia sobre la que se hizo este análisis. Hacerlo sólo para una comparación concreta y actualizar la tabla con el nuevo commit:

```bash
git -C reference/repos/<organizacion>/<repositorio> pull --ff-only
git -C reference/repos/droidian-devices/linux-android-lenovo-bronco \
  submodule update --init --depth 1
```

Antes de usar código en el port, registrar el commit completo, revisar su licencia y trasladar únicamente el cambio necesario a un repositorio propio.
