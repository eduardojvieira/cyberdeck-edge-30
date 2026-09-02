# Droidian + Plasma Mobile 6 para Motorola Edge 30 Ultra

Port incremental de Droidian con Plasma Mobile 6 para el Motorola Edge 30 Ultra (`eqs`, XT2241-1/XT2241-2), pensado para usar la pantalla interna como una computadora Linux portátil.

## Estado actual

Bring-up inicial validado sólo en host. Existe un artefacto `eqs-dev` estructuralmente empaquetado, pero no fue flasheado ni arrancado en el teléfono.

- [x] Los paquetes arm64 `adaptation-motorola-eqs` y `adaptation-motorola-eqs-configs` construyen dos veces de forma reproducible, con payload mínimo y dependencias de arranque verificadas en host.
- [x] La configuración Kconfig de `eqs` resuelve desde las fuentes locales fijadas.
- [x] Los dos DTB base y los ocho DTBO de `eqs` construyen en una receta host aislada.
- [x] `dt-images-dev` genera y valida en host el blob DTB multi-árbol y `dtbo.img` con el flujo Qualcomm canónico de LineageOS.
- [x] `Image-dev-thinlto` construye un `Image` host-only con ThinLTO y CFI, en un solo job de build y linker.
- [x] `modules-dev-display` compila en host los módulos in-tree, MMRM y display Qualcomm; no demuestra panel, HWC, Plasma ni ejecución en el teléfono.
- [x] `modules-dev-touch` compila en host la cadena display y touch Goodix de `eqs`; no demuestra panel, touch, HWC, Plasma ni ejecución en el teléfono.
- [x] `modules-dev-functional` compila en host la cadena display/touch más Wi-Fi, carga y UTAG; no demuestra asociación Wi-Fi, carga, PD, USB ni ejecución en el teléfono.
- [ ] `Image` con la configuración exacta sigue pendiente: el enlace LTO completo se detuvo por presión de memoria antes de producir el artefacto.
- [x] `eqs-dev` empaqueta en host kernel, 333 módulos y contenedores Android reproducibles; no constituye evidencia HIL ni una imagen Droidian completa.

Para repetir el gate seguro de device trees, con Docker y las referencias locales presentes:

```sh
port/kernel/build-host-artifacts.sh
```

El comando deja staging y salida en `.work/eqs-kernel/`, ignorado por Git. Sólo genera DTB/DTBO; no genera `boot.img`, `dtbo.img`, `vendor_boot.img` ni paquetes Debian, y no puede flashear el teléfono. `port/kernel/build-host-artifacts.sh Image` queda disponible para un host con memoria suficiente, pero no se ejecutará como gate normal.

Para generar los contenedores de device tree de desarrollo con el merge Qualcomm canónico:

```sh
port/kernel/build-host-artifacts.sh dt-images-dev
```

Este target sólo deja `.work/eqs-kernel/dt-images-dev/dtb.img` y `dtbo.img`, sus hashes y el dump de `mkdtboimg`. Compila localmente las herramientas fijadas de DTC y libufdt, ejecuta `merge_dtbs.py` de LineageOS y comprueba los metadatos Qualcomm. Es evidencia host-only: no crea `boot.img` ni `vendor_boot.img`, no valida AVB ni demuestra que Android bootloader, kernel o hardware acepten esos blobs.

Para la evidencia de desarrollo del kernel existe un target separado:

```sh
port/kernel/build-host-artifacts.sh Image-dev-thinlto
```

Usa ThinLTO con CFI, `make -j1` y `ld.lld --threads=1`. Es el perfil entregado de `eqs-dev` host-only: no recorta el contenido del SO ni del runtime, pero tampoco aporta evidencia HIL. Full LTO sigue sin construir y es un gate de promoción para daily/release, no un cambio de funcionalidad del artefacto de desarrollo.

Para comprobar la primera cadena de módulos de pantalla en host:

```sh
port/kernel/build-host-artifacts.sh modules-dev-display
```

Compila módulos in-tree, MMRM y display Qualcomm solamente; no prueba panel, HWC, Plasma ni comportamiento en ejecución.

Para comprobar la cadena de touch Goodix en host:

```sh
port/kernel/build-host-artifacts.sh modules-dev-touch
```

Compila MMRM, display Qualcomm, `mmi_annotate`, `mmi_info`, `mmi_relay`, `sensors_class`, `touchscreen_mmi` y `goodix_brl_mmi`; es evidencia de compilación, no de panel, touch, HWC, Plasma ni comportamiento en ejecución.

Para comprobar la cadena funcional mínima en host:

```sh
port/kernel/build-host-artifacts.sh modules-dev-functional
```

Repite display/touch y agrega Wi-Fi QCA6490, carga Motorola/QTI y `utags`; es compilación únicamente, sin prueba de asociación Wi-Fi, carga, PD, USB, panel, touch, HWC, Plasma ni HIL.

Para producir el artefacto de desarrollo estructuralmente flasheable y sus paquetes Debian:

```sh
port/kernel/build-dev-packages.sh
```

El comando ejecuta primero los gates canónicos de DT y módulos ThinLTO+CFI, instala 333 módulos arm64, prepara el vendor ramdisk con la lista Motorola fijada, y genera `boot.img`, `vendor_boot.img`, `dtbo.img`, `vbmeta.img` y los paquetes `linux-image-motorola-eqs` / `linux-bootimage-motorola-eqs` bajo `.work/eqs-kernel/eqs-dev-packages/`. Ensambla dos veces y exige hashes idénticos. Es **eqs-dev HOST-ONLY**: no prueba que el bootloader, firmware, pantalla, touch, Wi-Fi, carga, USB, Plasma ni el teléfono acepten o ejecuten esos artefactos; tampoco flashea nada. La imagen diaria/release requiere Full LTO y HIL separados.

Para construir y revisar los paquetes mínimos de adaptación:

```sh
port/build-adaptation-packages.sh
```

Construye dos copias limpias arm64 con la imagen Droidian fijada, exige igualdad byte a byte y deja los `.deb`, `SHA256SUMS` y `MANIFEST.txt` en `.work/eqs-adaptation/`. El chequeo verifica dependencias, payload, labels `hw`/`utags`/`utagsBackup` contra fuentes locales eqs/SM8475 y desempaqueta ambos paquetes en una raíz vacía. No puede configurar sus dependencias Droidian externas en esa raíz y no es evidencia HIL.

La rootfs/imagen fastboot de desarrollo con Plasma Mobile 6 y Wayfire ya fue generada e inspeccionada en host:

```sh
port/build-eqs-rootfs.sh --inspect-existing
```

El ZIP actual es `droidian-UNOFFICIAL-plamo_wf_experimental-phone-motorola_eqs-api32-arm64-101.20251130_20260901.zip` (1.623.173.400 bytes, SHA-256 `a934c89c3760478a7e13bb7927492e1e1347218fac226127587e4622db7d8986`). El manifiesto, la inspección y el listado de 1.378 paquetes instalados están bajo `.work/eqs-rootfs/` y no se versionan. Desde la raíz del repositorio, `sha256sum -c .work/eqs-rootfs/SHA256SUMS` verifica el ZIP generado. Se validaron Droidian 101/AArch64, los cuatro `.deb` locales, `droidian-plamo-wf-full`, Plasma Mobile Wayfire/HWC, Wayfire y libhybris, y la ausencia de Phosh/Phoc.

El script fija Droidian `101.20251130`, `plamo_wf_experimental`, API 32 y el builder por digest; conserva el pin de snapshot durante la adaptación y dentro de la rootfs, reconstruye por defecto los cuatro `.deb` locales, los indexa en el `apt/` interno oficial y ejecuta `debos --disable-fakemachine`. Para iterar sobre paquetes ya comprobados se puede usar `--reuse-packages`; `--inspect-existing` reutiliza el ZIP existente y no necesita qemu-binfmt.

Este host tiene `qemu-aarch64` registrado en `binfmt_misc` para ejecutar la segunda etapa arm64; esa configuración de host puede perderse tras un reinicio y se exige sólo al construir. Aunque el ZIP e inspección existan, sigue siendo evidencia host-only: aún **no se sabe si arranca** en `eqs` ni si funcionan pantalla, HWC, Plasma, USB, red, carga o cualquier otra función de hardware. La plantilla upstream de desarrollo usa el PIN `1234`; cambiarlo antes de conectar una red y preparar cifrado/imagen daily siguen siendo tareas separadas.

La receta exige `openssh-client` para SSH saliente y rechaza `openssh-server`. El build final conservó el snapshot `101.20251130` durante la adaptación y la instalación de paquetes runtime.

## Base técnica

- Dispositivo: Motorola Edge 30 Ultra `eqs`.
- Arquitectura: arm64.
- Sistema objetivo: Droidian con Plasma Mobile 6.
- Adaptación esperada: Halium API32 sobre el firmware Android 14 exacto de la unidad y región. La base de fuentes es `U1SQS34.52-21-1-10` (`motorola/eqs_ge/eqs:14/U1SQS34.52-21-1-10/504bf-893e0:user/release-keys`), no evidencia del firmware físico: una unidad distinta sigue NO-GO hasta demostrar compatibilidad.
- Pantalla: interna; no se trabaja en monitores externos por ahora.
- USB-C: carga y periféricos cuando la adaptación y el hardware lo demuestren.

Wayfire, wlroots-HWC, libhybris y los paquetes concretos son la ruta actual esperada en Droidian, pero son detalles a validar durante el port, no un contrato fijo del proyecto.

## Primer hito útil

Una primera imagen es útil cuando cumple:

- [ ] Droidian arranca en `eqs`.
- [ ] Plasma Mobile 6 inicia en la pantalla interna.
- [ ] Funcionan pantalla y touch.
- [ ] Funciona Wi-Fi.
- [ ] Hay terminal y SSH saliente.
- [ ] Funciona un teclado USB.
- [ ] El equipo reinicia y se recupera sin reflashear todo.

## Después, de a poco

1. Touchpad y mouse.
2. Ethernet, SD y almacenamiento USB.
3. Carga mientras se usan periféricos.
4. Suspensión, teclado virtual, escala y atajos.
5. Cifrado e imagen diaria sin herramientas de depuración.
6. Carcasa y montaje definitivo.

## No ahora

No forman parte del bring-up inicial: monitor externo, Motorola Ready For, telefonía, cámara, NFC, huella, Waydroid, aplicaciones Android, otros entornos gráficos o una carcasa definitiva.

## Límites de seguridad y recuperación

- Registrar el modelo, región y firmware Android 14 exactos antes de modificar el teléfono.
- El bootloader ya está desbloqueado; nunca relockearlo con imágenes modificadas.
- Seguir el [procedimiento de primer flash y recuperación](docs/RECOVERY.md); no falta documentación, falta completar y comprobar sus precondiciones físicas.
- No flashear ni probar hardware sin autorización explícita.
- Nunca flashear a través de un hub USB-C.
- No guardar claves, tokens ni datos personales en el repositorio o en imágenes de desarrollo.
- Una afirmación sobre arranque, carga, USB, térmica, suspensión o recuperación requiere evidencia física en el dispositivo.

## Próximos pasos

1. Completar y comprobar en la unidad las precondiciones de [recuperación](docs/RECOVERY.md) antes de cualquier flash.
2. Ejecutar la compilación daily/release con Full LTO en un host con memoria suficiente.
3. Probar en Android stock el hub, carga y periféricos antes de cualquier prueba de port en el teléfono.

## Referencias upstream

- [Droidian](https://github.com/droidian-images/droidian)
- [Plasma Mobile Wayfire de Droidian](https://github.com/droidian/plasma-mobile-wf)
- [LineageOS: device tree de eqs](https://github.com/LineageOS/android_device_motorola_eqs)
- [LineageOS: SM8475 common](https://github.com/LineageOS/android_device_motorola_sm8475-common)
- [LineageOS: kernel SM8475](https://github.com/LineageOS/android_kernel_motorola_sm8475)
- [Clones locales y evaluación individual](reference/README.md)
