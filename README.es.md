<p align="center">
  <a href="README.md">English</a> ·
  <strong>Español</strong> ·
  <a href="README.pt-BR.md">Português (Brasil)</a>
</p>

<p align="center">
  <img src="docs/assets/cyberdeck.svg" alt="Cyberdeck Edge 30 Ultra — Droidian y Plasma Mobile 6. Ilustración del concepto." width="100%">
</p>

# Cyberdeck Edge 30 Ultra

**De teléfono a máquina de trabajo.** Un port de **Droidian + Plasma Mobile 6**
para el Motorola Edge 30 Ultra (`eqs`): Linux nativo, terminal, aplicaciones de
escritorio y herramientas de desarrollo en un dispositivo de bolsillo.

<p align="center">
  <a href="#estado">Estado</a> ·
  <a href="#arquitectura">Arquitectura</a> ·
  <a href="#construir-e-instalar">Construir e instalar</a> ·
  <a href="#documentación">Documentación</a> ·
  <a href="#contribuir">Contribuir</a>
</p>

> [!IMPORTANT]
> **El teléfono ya arranca y ejecuta Plasma. El port sigue siendo experimental.**
> La validación corresponde a una unidad **XT2241-2 RETAR de 256 GB**.
> No es una ROM oficial ni una imagen universal lista para instalar:
> hay funciones pendientes, inputs binarios locales y una instalación limpia
> que todavía necesita validación física.

## Para qué existe

- **Terminal y redes:** SSH, tmux, Git, edición y diagnóstico de sistemas.
- **Desarrollo de bolsillo:** shell personalizada, editores, herramientas CLI
  y entornos científicos ARM64.
- **Escritorio táctil:** Plasma Mobile con rotación horizontal bloqueable,
  ventanas maximizadas y control manual del teclado en pantalla.

La pantalla interna es la única pantalla. USB-C se reserva para periféricos,
datos y alimentación; no se trabaja en monitores externos ni Motorola Ready For.

## Estado

**Última comprobación documentada: 11 de septiembre de 2026.**
Kernel **H29**, Plasma Mobile **6.3.3 +eqs5**, Wayfire/HWC, libhybris, Maliit y
XWayland. Firmware base Android 14: `U1SQS34.52-21-1-16`. El bootloader permanece abierto.

| Área | Evidencia y límites |
| :--- | :--- |
| 🟢 Arranque nativo | Droidian, systemd como PID 1 y raíz UFS/LVM comprobados; conjunto H29 recuperable. |
| 🟢 Plasma y navegación | Inicio, Recientes, Cerrar y gestos adaptados a Wayfire; mejoría de uso confirmada. |
| 🟢 Escritorio | Escala 200 %, cuatro escritorios, maximización genérica y margen de resize de 1000 ms para Ghostty y otros clientes lentos. |
| 🟢 Rotación y bloqueo | Conserva horizontal 90°/270°; fondo de bloqueo sigue al escritorio. Fechas y textos de bloqueo localizados con `+eqs5`. |
| 🟢 Wi-Fi y SSH | Acceso nativo utilizado para instalar y verificar el sistema. No equivale a una prueba de autonomía de ocho horas. |
| 🟢 Almacenamiento | `/` y `/home` comparten ext4 de **224,52 GiB**; crecimiento y reinicio comprobados sin cambiar GPT/PV/LV. |
| 🟡 Táctil de repuesto | Calibración libinput 2× confirmada **sólo para el repuesto de esta unidad**; no aplicarla a todos los `eqs`. |
| 🟡 Teclado virtual | Interruptor **Teclado táctil** y `osk on/off` funcionan; el control es manual, no autodetección USB. |
| 🟡 Audio y cámaras | Módulos/política stock corregidos; principal y frontal producen preview. Fix horizontal instalado; confirmación visual, fotos, auxiliares y calidad máxima pendientes. |
| 🟡 Bluetooth | Inicialización y escaneo tras reiniciar comprobados; perfiles no exhaustivamente validados. |
| 🟡 Hub USB-C | Hub y receptor RF funcionan con PD. **Conectar desde cero sin alimentación externa sigue fallando**; un swap permitió mantener una conexión ya iniciada. |
| 🟡 GPU en aplicaciones | Wayfire usa Adreno 730. Ghostty/Zed habituales usan software; la prueba aislada de Zed acelerado aún no está integrada. |
| 🔴 Daily cifrada | Pendiente. La preview no tiene LUKS y no debe tratarse como un equipo de trabajo endurecido. |

🟢 Comprobado en la unidad de prueba · 🟡 Parcial o condicionado · 🔴 Pendiente

## Arquitectura

**Droidian arranca nativamente; no es un chroot ni un escritorio remoto.**
La integración gráfica reutiliza los servicios y controladores Android del dispositivo:

```text
               Plasma Mobile 6
                      │
                 Wayfire / HWC
                      │
        Halium · libhybris · Android en LXC
                      │
      Kernel eqs H29 + firmware de Motorola
                      │
         Snapdragon 8+ Gen 1 · Adreno 730
```

KWin no actúa como compositor y Phosh no forma parte de la experiencia objetivo.
Waydroid es una incorporación **opcional para aplicaciones Android**, separada
del contenedor que necesita Halium para el hardware.

## Construir e instalar

### Primero: código, teléfono e imagen no son lo mismo

| Artefacto | Situación |
| :--- | :--- |
| Teléfono de desarrollo | H29 + Plasma `+eqs5`, fixes instalados y evidencia nativa documentada. |
| Receta de este repositorio | Fija el paquete `+eqs5`; requiere sus **22 inputs locales** con SHA-256. |
| ZIP construido el 10 de septiembre | Preview de 1,76 GiB con `+eqs4`; inspeccionada en host, **no validada como instalación limpia en el teléfono**. |
| ZIP nuevo con `+eqs5` | **Todavía no construido.** No hay una descarga binaria pública en este repositorio. |

Se construye desde una **base limpia**, nunca exportando la raíz viva,
`/home`, cuentas o credenciales del teléfono. El ZIP del 1 de septiembre es
histórico y **no representa el port actual**.

```sh
git clone https://github.com/eduardojvieira/cyberdeck-edge-30.git
cd cyberdeck-edge-30

# Sólo después de preparar Docker, binfmt ARM64 y los inputs locales.
# La ruta de salida no debe existir. Este comando no flashea el teléfono.
port/build-eqs-rootfs.sh --consolidated "$PWD/.work/eqs-image-new" stock
```

- **Pantalla original:** perfil `stock`. **Repuesto calibrado de la unidad de
  desarrollo:** `replacement`. El nombre Goodix no permite distinguirlos.
- La geometría actual es para la unidad de **256 GB**, no para un layout menor.
- El builder conserva el **binario H29 probado**; recompilar otro kernel con
  el mismo `uname -r` no demuestra equivalencia.
- Los builders/flashers históricos no reproducen el sistema actual. No usar
  `--historical` como atajo para instalarlo.

**Leer antes de empezar:** [inputs y construcción](port/image/README.md) ·
[release, hashes y evidencia](docs/RELEASE-20260910.md) ·
[instalación y rescate](port/image/INSTALL.md).

> [!WARNING]
> La instalación limpia **destruye `userdata`**. Prepará una recuperación probada,
> verificá variante y firmware, y usá un cable directo: **nunca flashees mediante
> un hub USB-C ni relockees el bootloader con una imagen modificada**.
> El slot B no es un respaldo. Un fallo gráfico no se diagnostica borrando datos.
> La preview usa un PIN de plantilla: cambialo antes de conectar cualquier red.

## Software instalado en el teléfono

| Conjunto | Herramientas y documentación |
|---|---|
| Terminal | Fish/Starship, fzf, zoxide, Neovim, Ghostty 1.3.1 y Hollywood/tmux aislado. [Shell](port/shell/README.md). |
| Desarrollo | Homebrew ARM64, mise, uv, GitHub CLI, Brew Browser como única GUI de Brew; GitUI, Lazygit, Yazi, ncdu, Mosh y Restic. |
| Editores/agentes | VS Code, Antigravity/CLI, Zed, Herdr, Codex y Pi con configuración portable; sin copiar almacenes de credenciales, logins remotos pendientes. |
| Ciencia | Octave 11.3, wxMaxima 26.08/Maxima 5.50, Python científico, SageMath, Spyder, JupyterLab y Scilab **2026.1** ARM64. Scilab APT 2024 fue retirado y 2026 revalidado. [Ciencia](port/shell/SCIENCE.md). |
| Oficina | ONLYOFFICE 9.4 ARM64 con repositorio oficial limitado a esa app. [Oficina](port/shell/OFFICE.md). |
| Android (11–12 de septiembre) | Waydroid + Android 13 GAPPS/Google Play instalados sin flash; arranque Android, red y apertura desde KDE comprobados. Acceso de Play Store habilitado en Plasma; login del usuario pendiente. Integración experimental, no incluida en el ZIP limpio. [Uso, ajustes y límites](port/waydroid/README.md). |

Estas herramientas están en el teléfono; la imagen base no clona Homebrew,
entornos grandes, cuentas ni configuraciones privadas. Launchers, versiones,
pruebas y mantenimiento quedan documentados para reinstalación selectiva.

## Idioma y rendimiento

<details>
<summary><strong>Español de Argentina, incluida la pantalla de bloqueo</strong></summary>

Sistema y formatos de Plasma configurados en **`es_AR.UTF-8`**, con
`LANGUAGE=es_AR:es`. Instalados `chromium-l10n`, `firefox-l10n-es-ar`,
`qt6-translations-l10n`, `qttranslations5-l10n`, `hunspell-es` y el paquete
español oficial de VS Code. Chromium prioriza `es-AR,es` para las páginas.
No se cambió la distribución del teclado ni se hizo un upgrade de la distribución.

Waydroid reinició con configuración efectiva `es-rAR`; sus launchers también
quedaron traducidos. Login SSH nuevo y entorno de activación KDE verificados.
Tras reiniciar, Plasma ya tenía `es_AR`, pero sus relojes seguían formateando
las fechas en inglés y el bloqueo contenía textos sin traducir. Instalado
[`+eqs5`](port/plasma-mobile-wf/README.md#date-and-lockscreen-language-september-11):
15 casos nativos pasan leyendo los recursos compilados y el catálogo español
contiene «Contraseña», «Cargando» y «Descargando».
**Activo tras recargar sólo Plasma con el teléfono desbloqueado**: comprobados
visualmente «viernes, 11 de septiembre de 2026» y «Descargando» en el bloqueo.
Wayfire y el arranque no cambiaron. La barra pasa la prueba nativa; su captura
posterior al desbloqueo queda pendiente. Scilab tiene ahora
[catálogo español parcial](port/shell/SCIENCE.md#traducción-española-11-de-septiembre).
Estos ajustes están en el **teléfono**, no en el ZIP del 10 de septiembre.
Respaldos privados: `/var/lib/eqs-locale-20260911/` y
`~/.cache/eqs-locale-20260911/` del Edge.
El paquete anterior y el log de instalación de `+eqs5` están en
`/var/lib/eqs-locale-clock-20260911/`.

</details>

<details>
<summary><strong>Geekbench 7 CPU — resultado público y condiciones de la prueba</strong></summary>

**Geekbench 7.0.0 Preview para Linux/AArch64**, ejecutado nativamente en
Droidian H29, completó la prueba y subió el
[resultado público 322037](https://browser.geekbench.com/v7/cpu/322037)
con autorización de Eduardo. Salida `0`; ejecución completa, incluida la subida:
**6 min 47 s**. Equipo cargando, gobernador `walt`, sin modificar frecuencias
ni protecciones térmicas. Es una pasada, no una media ni una prueba GPU.

La enumeración OpenCL de libhybris hacía fallar incluso `--help`; se evitó
sólo para este proceso con `OCL_ICD_VENDORS` apuntando a una carpeta vacía.
No se cambió el ICD del sistema. Logs privados en
`~/.cache/eqs-geekbench7-20260911/` del Edge; **no publicar el enlace de claim**.
El visor público devolvió HTTP 403 a las herramientas de lectura, por lo que
no se transcribieron puntuaciones sin verificar. No comparar con Geekbench 6.

</details>

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

## Documentación

El README de referencia es [la versión en inglés](README.md). Las guías técnicas
enlazadas conservan su idioma original; estas traducciones cubren la portada.

| Si querés… | Empezá por… |
| :--- | :--- |
| Entender cómo llegamos a un arranque nativo | [Plan de bring-up](docs/BRINGUP-PLAN.md) y [historial del port](docs/HISTORY-20260910.md) |
| Construir, inspeccionar o recuperar una imagen | [Builder](port/image/README.md), [instalación](port/image/INSTALL.md), [recuperación](docs/RECOVERY.md) y [release del 10/9](docs/RELEASE-20260910.md) |
| Trabajar en el escritorio | [Parches de Plasma/Wayfire](port/plasma-mobile-wf/README.md) |
| Investigar un periférico | [Bluetooth](docs/BLUETOOTH.md), [GPU](docs/GPU.md), [audio/cámara H27–H28](docs/H27-NAVIGATION-AUDIO-CAMERA.md) y [USB/H29](docs/H29-CAMERA-ROTATION-BROWSER.md) |
| Revisar el preview de cámara | [Override Qt5 aislado](port/qt5-wayland/README.md) |
| Reinstalar herramientas | [Shell](port/shell/README.md), [ciencia](port/shell/SCIENCE.md), [oficina](port/shell/OFFICE.md) y [Waydroid](port/waydroid/README.md) |
| Comparar fuentes y dispositivos | [Referencias fijadas](reference/README.md) |

## Lo que sigue

- [ ] Construir el ZIP `+eqs5` y validar físicamente la instalación limpia y su recuperación.
- [ ] Conectar hub y teclado sin PD desde cero, sin comandos manuales.
- [ ] Confirmar preview horizontal, fotos guardadas y cámaras auxiliares.
- [ ] Integrar GPU en las aplicaciones que hoy usan llvmpipe.
- [ ] Completar audio, perfiles Bluetooth, suspensión, hotplug, térmica y autonomía.
- [ ] Producir una daily LUKS con aprovisionamiento seguro y upgrades gráficos ensayados.
- [ ] Reconstruir todos los inputs binarios desde un clon nuevo.

## Contribuir

Los aportes más útiles son pequeños: **un fallo reproducible, un log sanitizado,
un parche acotado y una prueba que demuestre qué cambió**.

Al reportar un problema, indicá variante, firmware, perfil de pantalla, versión
Plasma/kernel y último paso comprobado. Separá siempre pruebas host de pruebas
reales en el teléfono. No adjuntes IMEI, serial, claves, tokens, redes guardadas
ni imágenes de tu sistema personal.

<details>
<summary><strong>Checks rápidos en la PC — sin teléfono ni sudo</strong></summary>

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

Las regresiones C++/initramfs necesitan sus fuentes fijadas: ver sus documentos.
**No ejecutes todos los tests indiscriminadamente.** `test-wallpaper-sync.py`
y `port/waydroid/check-prepare.py` son comprobaciones nativas del Edge;
el segundo prepara dispositivos y requiere autorización sobre el teléfono.

</details>

También se aceptan traducciones a otros idiomas. Partí de `README.md`, agregá
`README.<idioma>.md` y actualizá el selector en todas las versiones. Conservá
las mismas advertencias, versiones, comandos y estado de validación.

### Créditos

Este trabajo se apoya en **Droidian, KDE/Plasma Mobile, Wayfire, Halium,
libhybris, LineageOS, AOSP y los mantenedores de `eqs-development`**. Los ports
del ThinkPhone/Bronco aportaron referencias, no binarios intercambiables con `eqs`.
Fuentes y commits de referencia: [inventario](reference/README.md).

Port comunitario e independiente, sin afiliación oficial con Motorola, Droidian
ni KDE. Se conservan los avisos y licencias de cada componente; no se declara una
licencia única para todo el árbol. Firmware propietario, binarios de compilación,
logs y respaldos permanecen fuera de Git.

---

<p align="center"><strong>Un teléfono que ya no se conforma con ser un teléfono.</strong></p>
