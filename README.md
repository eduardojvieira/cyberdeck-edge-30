# Droidian + Plasma Mobile 6 para Motorola Edge 30 Ultra

Port para **Motorola Edge 30 Ultra `eqs`**, actualmente probado en la unidad
XT2241-2 RETAR de Eduardo, con Android 14 base `U1SQS34.52-21-1-16` y bootloader
abierto. **Droidian y Plasma funcionan en el teléfono.** No cambiar de interfaz
ni flashear binarios de ThinkPhone/Bronco: sólo son referencias de código.

## Estado al 10 de septiembre de 2026

El teléfono usa **H29**, Plasma Mobile **6.3.3 +eqs4**, Wayfire/HWC, libhybris,
Maliit y XWayland. Plasma 6.5 no es requisito. El ZIP inicial de septiembre 1
**no representa lo que funciona hoy**.

| Área | Estado y límite |
|---|---|
| Arranque | Droidian nativo, systemd PID 1 y raíz UFS/LVM comprobados; H29 recuperable. |
| Plasma | Bus/portal, PAM/IPC, Inicio/Recientes/Cerrar y gestos adaptados a Wayfire; Eduardo confirmó la mejoría de uso. |
| Pantalla | 200 %, cuatro escritorios, maximización genérica y plazo de resize de 1000 ms para Ghostty y otros clientes lentos. |
| Rotación | Bloqueo conserva horizontal 90°/270°; usuario confirmó funcionamiento. Fondo de bloqueo sigue la imagen del escritorio. |
| Táctil reemplazado | Calibración libinput 2× confirmada por Eduardo. Es específica de su repuesto, no de todo eqs. |
| Teclado virtual | Icono **Teclado táctil**, `osk on/off`; manual y temporal, confirmado. No autodetecta teclado USB. |
| Audio/cámara | Módulos/política stock corregidos; principal/frontal producen preview. Fix Qt5 horizontal instalado, pendiente de confirmación visual/fotos. Auxiliares/calidad máxima pendientes. |
| Bluetooth | VHCI/BNEP, dirección y UHID corregidos; inicialización/escaneo tras reiniciar comprobados. Perfiles no exhaustivamente validados. |
| Wi-Fi/SSH | SSH nativo utilizado para instalar/verificar cambios. No equivale a autonomía de 8 horas. |
| USB-C | Hub/receptor RF funcionan con PD. Mantenerlos al retirar PD fue posible tras swap; **conectar desde cero sin PD sigue fallando**. |
| GPU | Wayfire usa Adreno 730. Ghostty/Zed habitual usan software; Zed acelerado aislado aún no integrado. |
| Disco | `/` y `/home` comparten ext4 de **224,52 GiB**, sin cambiar GPT/PV/LV. Crecimiento y reinicio comprobados. |
| Seguridad | Preview, no daily cifrada. Bootloader abierto: nunca relockear ni incluir secretos en imágenes. |

## Imagen con los arreglos reunidos

La [release consolidada](docs/RELEASE-20260910.md) separa teléfono probado,
imagen inspeccionada en host y validación física pendiente. El builder usa una
**base limpia** y los inputs H29/Plasma/Qt/módulos fijados, no el sistema privado
del teléfono.

Archivo generado: `.work/eqs-image-20260910-r4/build/eqs-preview-20260910.zip`
(1,76 GiB). SHA-256, verificaciones y límites en la release enlazada arriba.

```sh
# Docker, binfmt ARM64 e inputs locales de port/image/inputs.json preparados.
# La carpeta NO debe existir. No flashea ni accede al teléfono.
port/build-eqs-rootfs.sh --consolidated "$PWD/.work/eqs-image-new" replacement
```

`replacement` incluye el arreglo del repuesto de Eduardo. Usar **`stock`** para
pantalla original; el nombre Goodix no permite distinguirlas automáticamente.
La geometría corresponde a la unidad de 256 GB; no sirve para un layout menor.

- [Reconstrucción, inputs y límites](port/image/README.md).
- [Instalación limpia y rescate](port/image/INSTALL.md): **destruye userdata**,
  no es una actualización del teléfono actual. No ejecutarla para conservar datos.
- Builder/flasher antiguos y Halium2 son históricos; el builder inicial exige
  ahora `--historical` explícito. No usarlos para reproducir H29.
- ZIP, firmware, logs y respaldos quedan fuera de Git. Commit/push publican
  código y documentación en el **repositorio privado**, no una release binaria.

## Software instalado en el teléfono

| Conjunto | Herramientas y documentación |
|---|---|
| Terminal | Fish/Starship, fzf, zoxide, Neovim, Ghostty 1.3.1 y Hollywood/tmux aislado. [Shell](port/shell/README.md). |
| Desarrollo | Homebrew ARM64, mise, uv, GitHub CLI, Brew Browser como única GUI de Brew; GitUI, Lazygit, Yazi, ncdu, Mosh y Restic. |
| Editores/agentes | VS Code, Antigravity/CLI, Zed, Herdr, Codex y Pi con configuración portable; sin copiar almacenes de credenciales, logins remotos pendientes. |
| Ciencia | Octave 11.3, wxMaxima 26.08/Maxima 5.50, Python científico, SageMath, Spyder, JupyterLab y Scilab **2026.1** ARM64. Scilab APT 2024 fue retirado y 2026 revalidado. [Ciencia](port/shell/SCIENCE.md). |
| Oficina | ONLYOFFICE 9.4 ARM64 con repositorio oficial limitado a esa app. [Oficina](port/shell/OFFICE.md). |
| Android (11 de septiembre) | Waydroid + Android 13 GAPPS/Google Play instalados sin flash; dos arranques y red comprobados, login del usuario pendiente. Integración experimental, no incluida en el ZIP limpio. [Uso, ajustes y límites](port/waydroid/README.md). |

Estas herramientas están en el teléfono; la imagen base no clona Homebrew,
entornos grandes, cuentas ni configuraciones privadas. Launchers, versiones,
pruebas y mantenimiento quedan documentados para reinstalación selectiva.

## Actualizaciones sin reflashear

Teléfono y receta consolidada usan `Acquire::Droidian::Version "current";`.
`101.20251130` identifica la base de construcción, no una obligación permanente.

```sh
sudo apt update
apt-mark showhold
sudo apt -s upgrade
```

Revisar firmas, downgrades y cambios Qt/Plasma/Halium antes de aplicar. No mezclar
Sid, quitar holds a ciegas ni automatizar `full-upgrade`. PackageKit ya había
sustituido el Plasma parcheado por upstream por prioridad 1002: el hold importa.
La imagen protege Plasma/kernel y deshabilita escrituras de boot por triggers
con `FLASH_BOOTIMAGE=no`; no garantiza cualquier upgrade. El launcher de cámara
vuelve a Qt del sistema si cambia su versión y requiere reconstrucción.
[Detalle de mantenimiento](docs/HISTORY-20260910.md#mantenimiento-apt-de-h29).

## Documentación y verificaciones

- [Consolidación y evidencia](docs/RELEASE-20260910.md).
- [Historial completo del trabajo](docs/HISTORY-20260910.md).
- [Bring-up y bootloops](docs/BRINGUP-PLAN.md), [recuperación y ext4](docs/RECOVERY.md).
- [Navegación/audio/cámaras H27–H28](docs/H27-NAVIGATION-AUDIO-CAMERA.md).
- [H29 y diagnóstico USB](docs/H29-CAMERA-ROTATION-BROWSER.md).
- [Plasma](port/plasma-mobile-wf/README.md), [Qt5 cámara](port/qt5-wayland/README.md),
  [Bluetooth](docs/BLUETOOTH.md), [GPU](docs/GPU.md).

Checks rápidos sin teléfono ni sudo:

```sh
python3 port/image/test-image.py
python3 port/kernel/test-eqs-config.py
python3 port/kernel/test-module-inventory.py
python3 port/test-bluetooth-address.py
python3 port/qt5-wayland/test-launcher.py
python3 port/shell/test-osk.py
python3 port/shell/test-hollywood.py
python3 port/shell/test-science.py
git diff --check
```

Las regresiones C++/initramfs necesitan las fuentes fijadas; ver sus documentos.
No ejecutar todos los `test-*` indiscriminadamente: `test-wallpaper-sync.py` es
una comprobación **nativa** de la sesión gráfica del Edge, no de la PC.

## Pendientes, sin declararlos resueltos

- [ ] Validar físicamente la **nueva imagen limpia** y su recuperación completa.
- [ ] Conectar hub/teclado sin PD desde cero, sin comandos.
- [ ] Confirmar preview horizontal, fotos guardadas y cámaras auxiliares.
- [ ] Integrar GPU para aplicaciones que hoy usan llvmpipe.
- [ ] Completar audio, perfiles Bluetooth, suspensión, hotplug, térmica y autonomía.
- [ ] Daily LUKS, aprovisionamiento seguro y upgrades gráficos ensayados.
- [ ] Reconstrucción de todos los inputs binarios desde un clon nuevo.

Nunca flashear sin autorización ni mediante hub. **B no es respaldo**; no borrar
userdata ni aceptar factory reset para diagnosticar un fallo gráfico.
