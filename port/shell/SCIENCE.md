# Ciencia y VS Code en el Edge

Instalados y actualizados por SSH el **9–10 de septiembre de 2026**, sin
reflashear ni reiniciar la sesión. Son cambios sobre el teléfono actual, no
sobre la imagen H29 original. **Scilab 2026.1.0** se compiló para ARM64 y se
validó en el teléfono; la versión APT **2024.1.0 fue retirada** a pedido de Eduardo.

## Abrir las herramientas

| Aplicación | Versión comprobada | Comando / acceso |
|---|---|---|
| GNU Octave | 11.3.0 (Homebrew) | `octave --gui`, icono GNU Octave |
| Scilab | 2026.1.0 (compilación propia ARM64) | `scilab`, icono Scilab; `scilab-cli` para terminal |
| wxMaxima / Maxima | 26.08.0 / 5.50.0 (Homebrew) | `wxmaxima`, icono wxMaxima |
| SageMath | 10.8 | `sage`, también kernel SageMath de JupyterLab |
| Spyder | 6.1.7 | `spyder`, icono Spyder |
| Python científico aislado | 3.14.7 | `science-python`, mismo entorno de Spyder |
| JupyterLab | 4.6.3 | `jupyter-lab`, icono JupyterLab |
| Visual Studio Code | 1.137.0 | `code`, icono Visual Studio Code |

El Python aislado incluye NumPy 2.5.3, SciPy 1.18.0, SymPy 1.14.0, pandas
3.0.5 y Matplotlib 3.11.1. El Python del sistema **sigue en 3.13.5**; también
se instalaron sus paquetes científicos APT, sin sustituirlo ni usar `sudo pip`.
Los launchers de Maxima y wxMaxima usan el backend y Gnuplot de Homebrew.
Los paquetes APT originales, incluidos `maxima-share` y `gnuplot-qt`, siguen
disponibles como respaldo.

El icono JupyterLab abre Ghostty y solicita abrir el navegador; **Ctrl+C en esa terminal** detiene
el servidor. Sólo escucha en `127.0.0.1` por defecto y conserva autenticación
por token. No se instaló un servicio permanente ni se abrió un puerto a la LAN.

## Distribución y herramientas separadas

APT conserva las bibliotecas Python nativas. Sus versiones Octave 9.4,
wxMaxima 24.02.1 y Maxima 5.47 quedan disponibles mediante `/usr/bin/octave`,
`/usr/bin/wxmaxima` y `/usr/bin/maxima`. El selector Droidian ya era `current`:
cambiar de snapshot no ofrecía versiones nuevas de esos paquetes.

[Octave](https://formulae.brew.sh/formula/octave),
[wxMaxima](https://formulae.brew.sh/formula/wxmaxima) y
[Maxima](https://formulae.brew.sh/formula/maxima) se instalaron desde bottles
Linux ARM64 de Homebrew, conservando APT. Los cuatro launchers de usuario
(`octave`, `octave-cli`, `wxmaxima`, `maxima`) eligen las rutas `opt` de Brew;
los dos iconos reemplazan solamente los accesos del usuario, no los paquetes.
Se agregó `librsvg` para que GTK de Brew pueda cargar iconos SVG.

El candidato APT de Sage 9.5 requería Python <3.12; Spyder entraba en conflicto
con Qt5 GLES de Droidian. No se forzó ninguna eliminación, downgrade ni
repositorio de otra distro.

[Miniforge oficial ARM64](https://github.com/conda-forge/miniforge/releases/tag/26.7.2-0)
queda en `~/.local/opt/miniforge3`; el entorno **science** está en `envs/science`.
No se ejecutó `conda init` ni se activa `base` automáticamente.
[Sage admite conda-forge en Linux aarch64](https://doc.sagemath.org/html/en/installation/conda.html)
y [Spyder recomienda un entorno conda separado](https://docs.spyder-ide.org/current/installation.html#conda-environment).
`science.yml` registra las dependencias pedidas; el inventario exacto y export
explícito de esta instalación quedan en el directorio privado de evidencia.

VS Code se obtuvo del [canal oficial Linux ARM64 de Microsoft](https://code.visualstudio.com/docs/setup/linux).
Se verificó el SHA-256 contra su API de actualización antes de instalarlo:

```text
code_1.137.0-1788902074_arm64.deb
Commit: 645f29cc3176500b4b5762ba887cf2a7f0ffdf2c
SHA256: 8bff558a659d351328f5a1e319802073b59dac42f95cc0f9b2ef1b0c27387431
```

Su paquete agregó `/etc/apt/sources.list.d/vscode.sources`, restringido a ARM64
y `Signed-By: /usr/share/keyrings/microsoft.gpg`. Una actualización de índices
sólo de ese origen terminó correctamente; APT ofrece la versión instalada.
No se instalaron extensiones ni se copiaron cuentas/credenciales de VS Code.

## Adaptaciones gráficas, sólo por aplicación

- **Octave 11.3:** el llvmpipe de Brew produjo `SIGILL` al dibujar. Un core de
  la prueba aislada mostró una instrucción SVE; H29 no expone SVE en
  `/proc/cpuinfo`. `GALLIUM_DRIVER=softpipe` en `octave` y `octave-cli` evita
  ese camino JIT. Se verificaron cálculo, ventana principal y exportación de
  un gráfico seno a PNG. Es renderizado **por CPU**, no aceleración GPU.
- **Brew científico:** los launchers quitan los preloads y plugins Qt de
  Droidian sólo de sus procesos. wxMaxima recibe explícitamente el Maxima de
  Brew; no se sobrescribe la configuración de cálculo del usuario.
- **VS Code:** `--ozone-platform=wayland --disable-gpu`, sin `--no-sandbox`.
  Se comprobaron `Seccomp: 2` y `NoNewPrivs: 1` en su renderer. El icono y el
  manejador de enlaces `vscode:` usan el mismo launcher.
- **Spyder:** su PyQt5 de conda no trae plugin Wayland; usa `xcb`/XWayland.
  El launcher evita heredar plugins Qt y preloads de Droidian.
- **Scilab:** JOGL abortaba en `XGetVisualInfo` al consultar EGL/libhybris para
  X11. Seleccionar Mesa + renderizado por software únicamente en su launcher
  permitió abrir la consola gráfica de 2024 y también los gráficos de 2026.
  La compilación nueva usa un prefijo privado; el paquete 2024 se retiró después.

Estas adaptaciones no cambian el renderer de Plasma ni habilitan aceleración
GPU para los editores. El avance experimental de Zed está en [GPU.md](../../docs/GPU.md).
Las GUIs científicas son de escritorio; usar horizontal con teclado/mouse.

## Verificación y mantenimiento

Pasaron cálculos reales de NumPy/SciPy/SymPy/pandas, Octave, Scilab CLI y Maxima;
Sage verificó primalidad, factorización y determinante. Matplotlib produjo un
PNG inspeccionado y un kernel Jupyter ejecutó NumPy correctamente. JupyterLab
respondió HTTP 200 con autenticación, rechazó el API anónimo y enumeró Python3
y SageMath; el servidor de prueba se cerró.

Se observaron ventanas reales de VS Code, Spyder, Scilab y wxMaxima a
**1200 × 479**. El 10 de septiembre también se verificaron la ventana principal
de Octave 11.3, su cálculo y un gráfico 2D exportado a PNG e inspeccionado;
wxMaxima 26.08 ejecutó una hoja que comprobó integración simbólica y registró
Maxima 5.50 como backend. Las instancias de prueba tenían perfiles privados y
unidades systemd temporales con limpieza de todo su cgroup; se cerraron al final.
No se completó el asistente de Octave en el perfil del usuario. Interacción
prolongada, legibilidad de las GUIs y gráficos 3D quedan pendientes.

`python3 port/shell/test-science.py` verifica argumentos y aislamiento de los
launchers. Los `.desktop` pasaron el validador y la resolución nativa de Gio;
se regeneró la caché KDE sin reiniciar Plasma. La instalación APT no actualizó
ni eliminó paquetes existentes; la retirada posterior de Scilab 2024 se detalla
más abajo. Se conservan los holds del port. En la actualización
Brew del día 10, los inventarios APT antes/después son idénticos y ninguna
fórmula Brew preexistente cambió de versión. Se agregaron 194 fórmulas con sus
dependencias; las pruebas de linkage de los tres programas pasaron.

- **APT / VS Code:** sus paquetes se mantienen desde los repositorios ya
  configurados; revisar la simulación antes de aceptar cambios en Qt o Halium.
- **Octave / wxMaxima / Maxima:** `brew update` actualiza las fórmulas;
  `brew outdated octave wxmaxima maxima` muestra novedades. Revisar
  `brew upgrade --dry-run octave wxmaxima maxima` antes de ejecutar el mismo
  comando sin `--dry-run`. Probar cálculo y gráficos después: `opt` sigue la
  versión instalada, pero una actualización de Mesa/Qt también puede cambiar
  su comportamiento. No exportar variables gráficas Brew globalmente.
- **Science:** `~/.local/opt/miniforge3/bin/conda update -n science --all --dry-run`
  muestra los cambios; quitar `--dry-run` sólo después de revisarlos. No usar
  APT para reemplazar este Spyder/Sage ni mezclar `pip` global con conda.
- Python para un IDE: `~/.local/opt/miniforge3/envs/science/bin/python`.

Launchers y `.desktop` homónimos de `port/shell/` van en `~/.local/bin/` y
`~/.local/share/applications/`. `science.yml` también está instalado como
`~/.config/science/environment.yml`. Inventarios, logs y la lista de archivos
nuevos están en `~/.local/state/eqs-gpu.0KlZPw/`. Para revertir los launchers,
retirar sólo los archivos enumerados allí; preservar notebooks, proyectos y
configuraciones que se creen después. No ejecutar un `autoremove` ciego.

## Scilab 2026.1 ARM64: instalado y probado

La [descarga oficial de Scilab 2026.1.0](https://www.scilab.org/download)
para Linux es x86_64, no utilizable directamente en este ARM64. Se compiló
la [fuente oficial 2026.1.0](https://gitlab.com/scilab/scilab/-/tree/2026.1.0),
commit `983e9a1bd6ef77a0e132ed8c954d0a54d29abe2b`, en un contenedor Debian
trixie ARM64 de la PC, con compiladores cruzados GCC/G++/GFortran 14.2,
pruebas ARM64 emuladas y dependencias aisladas. No se agregó Debian Sid.

El runtime ocupa aproximadamente **1,4 GiB** en `~/.local/opt/scilab-2026.1.0`. El launcher
`scilab` ejecuta únicamente ese prefijo; `scilab-cli` delega al mismo launcher
con `-nwni`. El icono usa el ejecutable y el PNG privados de 2026, sin depender
del paquete APT ni cambiar Plasma o reiniciar la sesión.

**Verificación nativa:** cálculo matricial, determinante, autovalores, UMFPACK,
KINSOL con callbacks `init/iter/done`, escritura/lectura XLSX y Parquet pasaron
con código 0. También se observaron consola, gráfico, SciNotes, editor Xcos y
su paleta. El PNG exportado se inspeccionó visualmente. En la prueba final
todas esas ventanas ocuparon 1200 × 479. En la primera, el gráfico quedó a
610 × 479: no se modificaron reglas de ventanas y no se garantiza todavía
que esa geometría sea consistente en todos los arranques.

El build conserva el rótulo upstream `scilab-branch-2026.1`: el tag fuente no
estampa los metadatos de un binario oficial. Los tres primeros campos de
`getversion("scilab")` son **2026, 1, 0**; el commit de arriba identifica la fuente real.
Modelica y la compilación de ayuda offline están desactivados. El paquete original
omitía las traducciones; el catálogo español se agregó al teléfono el 11 de
septiembre (ver abajo). No se validó toda la suite
Xcos ni la compilación de extensiones ATOMS. Es renderizado por CPU, no GPU.

**Actualizaciones:** APT no mantiene este prefijo y ya no hay Scilab 2024 instalado.
Para actualizar 2026 hace falta reconstruir y repetir las pruebas antes de
cambiar el selector. No usar `apt full-upgrade` ni paquetes Sid para sustituir
las dependencias privadas.

Artefacto privado de esta instalación:

```text
scilab-2026.1.0-eqs-arm64.tar.gz
SHA256: 5a4bcadf8ad90b1adaecf78668c7ceca2b590b5ce7162aec55b051f014f6df9b
```

`share/build-info/` del runtime conserva identidad de fuente, manifiesto de dependencias,
hashes de toolchain, parche, receta y pruebas. Logs y artefactos completos:
`.work/scilab-2026/` en la PC y
`~/.local/state/eqs-scilab-2026-20260910/` en el teléfono. El paquete verificado
contiene 178 ELF AArch64, sin enlaces rotos ni rutas dinámicas `/work/`;
`ldd` nativo no encontró bibliotecas ausentes ni mezcla con Scilab APT.

**Retirada de 2024, 10 de septiembre:** se quitaron sólo `scilab`, `scilab-cli`,
`scilab-data`, `scilab-full-bin`, `scilab-include` y `scilab-minimal-bin`:
**125 MB liberados**, sin `purge`, `autoremove`, upgrades ni pérdida de datos
del usuario. Se marcaron manuales 63 dependencias compartidas que el runtime
privado utiliza; no son holds y pueden actualizarse por APT. `dpkg --audit`
quedó limpio y no cambiaron los demás paquetes ni los holds.

Después de retirarlos pasaron nuevamente `ldd`, la suite CLI y la apertura
nativa de consola, gráfico, SciNotes y Xcos. Los inventarios y logs están en
`~/.local/state/eqs-remove-scilab2024-20260910/`. No restaurar el antiguo launcher
APT: su ejecutable ya no existe. Para recuperar 2026 se conserva el archivo
verificado de arriba; preservar proyectos y configuraciones al restaurar su
prefijo privado. No ejecutar un `autoremove` ciego.

### Traducción española (11 de septiembre)

El build conservaba libintl pero `--disable-build-localization` había omitido
los catálogos. Se compilaron los `.po` españoles de **la misma fuente 2026.1**,
siguiendo su `Makefile.am`, sin cambiar ejecutables ni bibliotecas:

```sh
# Desde scilab/ de la fuente fijada; OUT es un staging nuevo, no el runtime vivo.
: "${OUT:?Definir una ruta nueva de staging}"
mkdir -p "$OUT/locale/es_ES/LC_MESSAGES"
msgcat --use-first -o "$OUT/scilab-es.po" modules/*/locales/es_ES*.po
msgfmt --check --statistics -o "$OUT/locale/es_ES/LC_MESSAGES/scilab.mo" "$OUT/scilab-es.po"
ln -s es_ES "$OUT/locale/es"
ln -s es_ES "$OUT/locale/es_AR"
```

El árbol `locale/` se instaló en el `share/` del prefijo privado. SHA-256 del
`.mo`: `653ecdeaddc7168db24b7b211e2a6272132f7b77a004ded2f13cf7fcc834443f`.
Test **nativo** con `LANG=es_AR.UTF-8 LANGUAGE=es_AR:es`:
`assert_checkequal(gettext("File"),"Archivo")` pasó, `getlanguage()` devolvió
`es_AR` y desapareció el aviso de localización. La traducción upstream es
**parcial: 2781 mensajes traducidos y 4250 sin traducir**. El tar original
documentado arriba no incluye esta adición; staging en
`.work/eqs-locale-20260911/scilab/`. No se tradujo ni reconstruyó la ayuda offline.

### Correcciones necesarias para compilar

El primer `configure` se detuvo por XLNT. En el intento del 10 de septiembre
se completaron las dependencias privadas: **XLNT 1.6.1, Arrow/Parquet 19.0.0,
Temurin 17, JavaFX ARM64, JCEF ARM64 y JOGL/GlueGen ARM64**. XLNT y Flexdock
compilaron; las pruebas C++/Fortran de las dependencias ejecutaron correctamente
en el contenedor ARM64 emulado. Esto **no es evidencia de ejecución en el teléfono**.

La compilación llegó al enlace final y reveló tres problemas concretos:

- Dos llamadas de KINSOL pasaban `NULL` como `va_list`, incompatible con la
  ABI Linux ARM64. Una sobrecarga comparte el callback sin fabricar varargs;
  la recompilación del objeto corregido pasó.
- Definir `F77` sin `--with-gfortran` omitía la detección GNU de upstream y
  producía objetos Fortran sin PIC. Se agregó detección explícita y `-fPIC`.
- Los nombres absolutos del compilador cruzado no coinciden con los casos
  `gcc/g++` de `configure`: faltaban `NDEBUG` coherente en C++ y
  `--no-as-needed` para dependencias circulares. El nuevo build declara esos
  flags, valida la configuración efectiva y recompila desde `make clean`.

El build limpio, `make install`, el empaquetado, las pruebas del contenedor
y las pruebas nativas terminaron correctamente. Los fallos previos se conservaron
en logs separados; `scilab-build.exit` y `package-runtime.exit` contienen `0`.

### Investigación previa ARM64 — 10 de septiembre de 2026

**No se encontró un Scilab posterior a 2024.1 ya empaquetado y verificable
para Linux ARM64 en los canales revisados.** No es un bloqueo del snapshot
Droidian: [Debian sid también sigue en 2024.1](https://packages.debian.org/sid/scilab).
El [cask de Homebrew 2026.1](https://formulae.brew.sh/cask/scilab) es sólo macOS;
conda-forge y la receta `scilab-bin` de Nix consultadas siguen en 6.1.1 y no
ofrecen Linux ARM64. No mezclar repositorios de otra distro para resolverlo.

La pista útil es la [receta fuente de Flathub 2026.0.1](https://github.com/flathub/org.scilab.Scilab/blob/5e78fc19d273b05a0d23757c0704dde84e8ad764/org.scilab.Scilab.yaml),
commit `5e78fc19d273b05a0d23757c0704dde84e8ad764`. Publica sólo x86_64, pero
permite reutilizar la integración de bibliotecas, Java y rutas de ejecución.
No basta con quitar su restricción de arquitectura:

- [JCEF 135.0.20](https://github.com/jcefmaven/jcefmaven/releases/tag/135.0.20)
  sí publica el artefacto nativo Linux ARM64; se verificaron nombre y tamaño
  por API, no su ejecución.
- Los JAR nativos oficiales JOGL/GlueGen 2.5.0 `linux-aarch64` se descargaron:
  sus ocho bibliotecas `.so` tienen cabecera ELF AArch64. No se ejecutaron.
- JavaFX 17.0.13 ARM64 no está en las rutas Maven usadas por la receta.
  [Gluon ofrece SDK Linux aarch64](https://gluonhq.com/products/javafx/), aunque
  clasifica esa plataforma como provista sin soporte. El SDK 17.0.13 respondió
  403; el 17.0.20 respondió 200 y anuncia 60.978.022 bytes. Su integración con
  Scilab todavía no estaba probada durante esa investigación.
- El `configure.ac` de Scilab 2026.0.1 y 2026.1.0 acepta **JDK major 17**,
  no 21, pese a que el error dice «at least 17». La receta Flathub también
  desactiva Modelica y UMFPACK: no presentarla sin cambios como soporte completo.

**Ruta finalmente utilizada:** fuente 2026.1.0 y dependencias ARM64 privadas,
con las pruebas nativas indicadas arriba. No fue necesario usar 2026.0.1 como
candidato intermedio ni agregar opciones que desactiven el sandbox JCEF.
La investigación inicial no había compilado otro Scilab; la instalación
posterior sí completó ese trabajo y mantiene 2024.1 como respaldo.

Manifiestos, respuestas de API, comprobaciones HTTP y JAR inspeccionados están
en `.work/scilab-research/`. Tavily no autorizó la consulta; se usaron búsqueda
web nativa, documentación oficial y código fuente.

## Revertir sólo la actualización Brew

Las versiones APT no se eliminaron. Retirar los **seis accesos nuevos** enumerados
en `~/.local/state/eqs-science-upgrade-20260910/new-launcher-files.txt` devuelve
la selección a los anteriores; después ejecutar `kbuildsycoca6 --noincremental`.
No borrar configuraciones, notebooks ni fórmulas/dependencias indiscriminadamente.
Ese directorio privado conserva inventarios, resultados, logs y candidatos.

## SMath Studio (30 de septiembre)

Instalado **1.5.0.9678** desde el [paquete Mono oficial](https://www.smath.com/en-US/view/SMathStudio/download),
en `~/.local/opt/smath-studio-1.5.0.9678/`. El acceso **SMath Studio** y
`smath-studio` abren `Solver.exe` con Mono ARM64 nativo: no usa Wine, Waydroid
ni emulación x86. También está en **EQS Ingeniería**. El otro ejecutable,
`SMathStudio_Desktop.exe`, es la interfaz de terminal, no la GUI.

El GDI+ del sistema falló en medición de texto con Pango. Una configuración
privada de fuentes abrió una ventana vacía una vez, pero no solucionó las
pruebas posteriores con hojas. La solución verificada usa **libgdiplus 6.2
compilado con X11 y texto Cairo**, dentro del directorio de SMath, con las
bibliotecas existentes de Homebrew. `mono.config` cambia sólo los mapas GDI+
de una copia de `/etc/mono/config`; `fonts.conf` usa fuentes del sistema y una
caché privada. El wrapper limita estos cambios al proceso SMath: **no modifica
Mono, Fontconfig, Pango, GLib ni el escritorio globalmente**. No se aisló el
bug nativo exacto y no se afirma una corrección upstream.

### Reconstruir esta integración en el Edge

Requiere el Homebrew ARM64 ya instalado y sus bibliotecas/cabeceras Cairo,
Fontconfig, FreeType, GLib, X11, PNG, JPEG, TIFF y GIF. No actualizar la pila
móvil para resolver estas dependencias. Primero simular y revisar APT:

```sh
set -e
sudo apt-get --no-remove --no-upgrade --no-install-recommends install \
  mono-runtime mono-libraries libgdiplus
mkdir -p ~/.local/opt/smath-studio-1.5.0.9678 ~/.local/bin ~/.local/share/applications
# Descargar fuera del repositorio; comprobar antes de extraer.
curl -fL https://www.smath.com/en-US/files/Download/NKnL7/SMathStudioDesktop.1_5_0_9678.Mono.tar.gz \
  -o SMathStudioDesktop.1_5_0_9678.Mono.tar.gz
echo '8cc386d9d5b66befb102b3aca77c23543939bebdce82b137e1cba91df0d005a2  SMathStudioDesktop.1_5_0_9678.Mono.tar.gz' | sha256sum -c -
tar -xzf SMathStudioDesktop.1_5_0_9678.Mono.tar.gz -C ~/.local/opt/smath-studio-1.5.0.9678
curl -fL https://dl.winehq.org/mono/sources/libgdiplus/libgdiplus-6.2.tar.gz -o libgdiplus-6.2.tar.gz
echo '683adb7d99d03f6ee7985173a206a2243f76632682334ced4cae2fcd20c83bc9  libgdiplus-6.2.tar.gz' | sha256sum -c -
tar -xzf libgdiplus-6.2.tar.gz
(
  cd libgdiplus-6.2 || exit
  # configure interpreta --without-pango como activar Pango y --with-x11
  # como desactivar X11. Omitir ambos; ocultar Pango sólo a esta compilación.
  printf '#!/bin/sh\ncase "$*" in *pango*) exit 1;; esac\nexec /home/linuxbrew/.linuxbrew/bin/pkg-config "$@"\n' > pkg-config-no-pango
  chmod 700 pkg-config-no-pango
  export PATH=/home/linuxbrew/.linuxbrew/bin:/usr/bin:/bin
  export PKG_CONFIG_PATH=/home/linuxbrew/.linuxbrew/lib/pkgconfig:/home/linuxbrew/.linuxbrew/share/pkgconfig
  export CPPFLAGS=-I/home/linuxbrew/.linuxbrew/include
  export LDFLAGS='-L/home/linuxbrew/.linuxbrew/lib -Wl,-rpath,/home/linuxbrew/.linuxbrew/lib'
  ./configure --prefix="$HOME/.local/opt/smath-studio-1.5.0.9678/gdiplus" \
    --without-libexif CC=/usr/bin/gcc PKG_CONFIG="$PWD/pkg-config-no-pango" &&
  make -j4 && make install
)
# La salida debe decir: Text = cairo; X11 = yes.
python3 - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
root = Path.home() / '.local/opt/smath-studio-1.5.0.9678'
tree = ET.parse('/etc/mono/config')
for mapping in tree.findall('dllmap'):
    if mapping.get('dll') in ('gdiplus', 'gdiplus.dll', 'gdi32', 'gdi32.dll'):
        mapping.set('target', str(root / 'gdiplus/lib/libgdiplus.so.0'))
tree.write(root / 'mono.config', encoding='unicode')
PY
install -m644 port/shell/smath-fonts.conf ~/.local/opt/smath-studio-1.5.0.9678/fonts.conf
install -m755 port/shell/smath-studio ~/.local/bin/
install -m644 port/shell/smath-studio.desktop ~/.local/share/applications/
python3 port/shell/test-engineering-apps.py
smath-studio ~/.local/opt/smath-studio-1.5.0.9678/examples/EuclideanGCD.sm
```

El hash del archivo SMath es del artefacto HTTPS descargado; no se verificó
una firma/digest separado del fabricante. El hash de libgdiplus coincide con
la [fórmula Homebrew](https://formulae.brew.sh/formula/mono-libgdiplus).
La compilación privada omite EXIF; no garantiza fallback tipográfico idéntico
a Pango. No se usa `brew install mono-libgdiplus`: su bottle Linux no tenía
el punto de entrada X11 requerido por WinForms. Los dos paquetes Brew de esa
prueba se retiraron; el inventario Brew original quedó idéntico.

La ventana abrió `EuclideanGCD.sm` en español a 1200×540 y permaneció activa
45 segundos, sin un crash nativo. Esto comprueba apertura/renderizado inicial,
**no edición prolongada, exactitud de todas las funciones, plugins o uso táctil**.
La CLI de automatización devuelve un error de licencia: no se evitó ese control
ni se informa como prueba de cálculo aprobada. El fabricante indica
[uso personal gratuito y planes para organizaciones](https://smath.com/en-US);
revisar la licencia antes de usarlo profesionalmente.

Los accesos y la instalación son del teléfono vivo, **no de las recetas de
imagen**. [KiCad, Fritzing y Arduino](TOOLBOX.md#engineering-apps-september-30)
completan el toolbox de electrónica. Para revertir, retirar sólo los accesos
SMath y su directorio privado después de conservar las hojas personales;
no borrar proyectos ni ejecutar `autoremove` indiscriminadamente.
