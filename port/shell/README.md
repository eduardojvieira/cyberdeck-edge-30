# Shell de la PC en el Edge

Perfil instalado por SSH el **8 de septiembre de 2026**, sobre H29 existente.
No modifica la imagen de arranque. Las herramientas personales no se clonan
en la rootfs limpia; el control OSK sí está integrado en la [receta consolidada](../image/README.md). QMLKonsole sigue disponible; Plasma/Wayfire y la PC no se modificaron.

## Qué se conserva de la PC

- Fish, prompt Starship **Gentleman**, navegación vi con atajos Emacs en inserción.
- `Ctrl+R` con fzf, `z` con zoxide, `fzfbat`, `fzfnvim` y editor Neovim.
- `bat` → `batcat`, `fd` → `fdfind`, `ls --color=auto` nativo de Debian.
- JetBrainsMono Nerd Font regular/negrita; QMLKonsole conserva tamaño 10.
- Ghostty con los colores Tokyo Night usados por la terminal de la PC.

No se copiaron credenciales, historial, variables universales de Fish, Atuin,
Fisher, Homebrew, Herdr automático, Carapace ni integraciones exclusivas de la PC.
Homebrew se instaló por separado el 9 de septiembre, como se detalla abajo.
El prompt tiene un timeout de comandos de 500 ms, no el de una hora del origen.

La cuenta conserva `/bin/bash`. `interactive.bash` se agrega **una sola vez** al
final de `.bashrc`: abre Fish en terminales interactivas nuevas, pero no en
comandos SSH, scripts ni un Bash abierto desde Fish. Rescate: `bash --norc`.

## Archivos instalados

| Origen | Destino en el teléfono |
|---|---|
| `config.fish` | `~/.config/fish/config.fish` |
| `starship.toml` | `~/.config/starship.toml` |
| `interactive.bash` | Bloque delimitado al final de `~/.bashrc` |
| `ghostty.conf` | `~/.config/ghostty/config.ghostty` |
| `ghostty` | `~/.local/bin/ghostty`, modo 755 |
| `com.mitchellh.ghostty.desktop` | `~/.local/share/applications/` |
| `osk` | `~/.local/bin/osk`, modo 755 |
| `eqs-osk.desktop` | `~/.local/share/applications/` |
| `eqs-osk-reset.desktop` | `~/.config/autostart/` |
| `homebrew.fish` | `~/.config/fish/conf.d/20-eqs-homebrew.fish` |
| `brew-browser`, `antigravity` | `~/.local/bin/`, modo 755 |
| `com.zerologic.brew-browser.desktop`, `antigravity.desktop`, `dev.zed.Zed.desktop` | `~/.local/share/applications/` |

El `.desktop` corresponde al usuario **droidian** y usa la ruta absoluta del
wrapper: el PATH gráfico no incluye `~/.local/bin`. `DBusActivatable=false`
evita que el menú saltee el wrapper. No reemplazarlo por `/usr/bin/ghostty`.

Las fuentes se copiaron desde `/usr/share/fonts/TTF/` de la PC a
`~/.local/share/fonts/eqs-shell/` y se registraron con `fc-cache`.
En `~/.config/qmlkonsolerc`, sección `[General]`, se estableció
`fontFamily=JetBrainsMono Nerd Font` sin alterar el tamaño existente.

## Teclado táctil temporal

Abrir la aplicación **Teclado táctil** en el cajón de aplicaciones oculta Maliit;
abrirla otra vez lo habilita. No es un interruptor del panel de ajustes rápidos.
Desde terminal: `osk off`, `osk on` o `osk` para alternar. No se detecta
automáticamente el teclado USB: es un control manual para toque o mouse.

El ajuste nativo es `org.maliit.keyboard.maliit stay-hidden`. El toggle de Plasma
instalado apunta a KWin, ausente en esta sesión Wayfire. No se mata Maliit ni se
modifica el teclado independiente del bloqueo. Al iniciar una sesión gráfica
nueva se restablece a habilitado; inicialmente se dejó habilitado.

El código fijado de Maliit conecta `stayHiddenChanged` con `InputMethod::hide`
en [`inputmethod_p.h`](https://github.com/droidian/maliit-keyboard/blob/6e6a89ff5c64e722f09eab082c93ccc48abf6bf1/src/plugin/inputmethod_p.h#L288-L292),
además de bloquear `show()`. La indicación anterior de cambiar el foco era
incorrecta: la conexión no estaba en el archivo inspeccionado inicialmente.

`python3 port/shell/test-osk.py` pasa en host y ARM64. También se verificaron
dos lanzamientos reales del icono, los estados GSettings y el comando exacto
del autostart, sin reiniciar Maliit ni el teléfono. No se ensayó un nuevo login.
Respaldo: `~/.local/state/eqs-osk.Q97gi4/`. Para retirar esta función, ejecutar
`osk on` y apartar únicamente los tres archivos OSK de la tabla.

## Paquetes y mantenimiento

Versiones nativas verificadas el 8 de septiembre: Fish **4.0.2**, Starship **1.22.1**, fzf
**0.60.3**, zoxide **0.9.7**, bat **0.25.0**, fd **10.2.0**, Neovim **0.10.4**,
Git **2.50.1**, Ghostty **1.3.1**. Las dos operaciones APT instalaron **37 paquetes
nuevos**, incluidos dependencias; cero actualizaciones o eliminaciones.
No se ejecutó un upgrade general ni se modificaron fuentes/holds.

Ghostty no figura en el APT configurado. Se usó el paquete comunitario Debian
Trixie ARM64 de [mkasberg/ghostty-ubuntu, 1.3.1-0-ppa2](https://github.com/mkasberg/ghostty-ubuntu/releases/tag/1.3.1-0-ppa2),
enlazado desde la [documentación de Ghostty](https://ghostty.org/docs/install/binary).
**No es un binario oficial de Ghostty ni un paquete de Droidian.** Se inspeccionaron
sus scripts de mantenimiento y se verificó el SHA-256 contra el digest del asset
de GitHub; eso comprueba integridad respecto de esa publicación, no equivale a
una firma upstream ni a una auditoría del binario.

```text
ghostty_1.3.1-0.ppa2_arm64_trixie.deb
Package-Version: 1.3.1-0~ppa2
SHA256: 73f384e62c419d7a7809d686bf579fea5e23f52742b34f70c74d6adf0e72f8ab
```

Se instaló el archivo local mediante `apt-get --no-install-recommends --no-upgrade
--no-remove install ./archivo.deb`, después de revisar la simulación. No se añadió
un PPA ni se ejecutó el instalador remoto del proveedor. **Ghostty no se actualizará
automáticamente desde ese proveedor**: una versión nueva requiere revisar el
paquete, dependencias y esta adaptación. Esas herramientas proceden del APT
de Droidian; las incorporaciones del 9 de septiembre se mantienen por separado.
El teléfono ya tenía el selector `current`; esta instalación no lo cambió.
Se retiró la nueva alternativa global `x-terminal-emulator` que creó el paquete
(antes no existía), para no dejar `/usr/bin/ghostty` sin wrapper como predeterminado.
Abrir Ghostty desde su icono o con `ghostty` dentro de la shell configurada.

## Herdr, Codex y Pi

Instalados por usuario el 8 de septiembre, sin sudo ni cambios APT:

| Herramienta | Versión | Origen ARM64 |
|---|---|---|
| Herdr | 0.9.0 | [Release oficial](https://github.com/herdrdev/herdr/releases/tag/v0.9.0) |
| Codex CLI | 0.153.4 | [Paquete completo oficial](https://github.com/openai/codex/releases/tag/rust-v0.153.4) |
| Pi | 0.85.1 | [Bundle oficial](https://github.com/earendil-works/pi/releases/tag/v0.85.1) |
| Node / npm | 24.20.0 / 11.19.0 | [Node LTS oficial](https://nodejs.org/en/download/archive/v24.20.0) |
| Codegraph | 1.3.1 | [Release oficial](https://github.com/colbymchenry/codegraph/releases/tag/v1.3.1) |
| Engram | 1.20.0 | [Release oficial](https://github.com/Gentleman-Programming/engram/releases/tag/v1.20.0) |

Binarios en `~/.local/opt/`, enlaces en `~/.local/bin/`. Se verificaron SHA-256
contra los assets oficiales/SHASUMS de Node. Node 25.9.0 de la PC ya no tiene
mantenimiento: se usó 24 LTS, compatible con Pi; las otras cinco versiones
coinciden con sus ejecutables en la PC. Homebrew y mise se incorporaron al día siguiente.

Se copiaron selectivamente las configuraciones de `~/.codex`, `~/.pi`,
`~/.agents/skills` y `~/.config/herdr/config.toml`, incluidos modelos, atajos,
hooks, skills y agentes. **No son un clon completo de esos directorios:** no se
trasladaron historiales, bases de conversaciones/memoria, sockets ni almacenes
de credenciales. Las configuraciones personales quedan fuera de Git.

Adaptaciones necesarias, no diferencias ocultas:

- Rutas de Eduardo → `/home/droidian`; Codegraph apunta al launcher ARM64.
- Los 15 plugins instalados de la PC aparecen en `codex plugin list --json`.
  Los namespaces reservados a la aplicación se registraron como catálogos
  locales `pc-bundled`, `pc-runtime` y `pc-curated`; Ponytail conserva su origen.
  **13 habilitados**, browser/CUA conservados pero deshabilitados, junto con
  el MCP `node_repl` de la aplicación de escritorio. Copiar archivos no porta
  sus servicios ni garantiza las integraciones remotas de los otros plugins.
- Se retiró el alias `agents.max_threads`: coexistía con
  `max_concurrent_threads_per_session` y Codex rechazaba esa configuración.
  Se conserva el valor canónico de la PC, 96, y sus modelos. También conserva
  sus permisos amplios; no se ejecutaron prompts/agentes durante la instalación.
- Pi conserva 21 agentes y sus 10 entradas de paquetes (incluida la referencia
  duplicada a Gentle Engram). Se instalaron 256 dependencias desde el lockfile,
  usando `--legacy-peer-deps`, como hace [Pi upstream](https://github.com/earendil-works/pi/blob/v0.85.1/packages/coding-agent/src/core/package-manager.ts).
  No se copiaron `node_modules` x86. Los scripts de instalación se omitieron;
  los launchers ARM64 de esbuild/ast-grep funcionan, este último con su fallback.

**Falta autenticar las cuentas.** En Ghostty: `codex login --device-auth`.
En Pi: abrir `pi`, usar `/login` y elegir OpenAI Codex. Context7/Tavily también
necesitan su autorización/configuración de credenciales cuando corresponda;
no se copió el header privado de Context7. No hay una prueba de generación ni
de todos los backends remotos. [Configuración oficial de Codex](https://learn.chatgpt.com/docs/config-file/config-basic).

Verificado nativamente: versiones; TUI Herdr y estado de su servidor en una
sesión aislada, cerrada al terminar; Pi RPC con 85 comandos y sin errores de
extensiones; handshake/listado MCP de Engram y Codegraph; Codex con TOML válido,
sin el warning de agentes duplicados. Autenticación pendiente confirmada por
los chequeos de ambos clientes. El primer ensayo Herdr falló por la longitud
del socket en el directorio de pruebas; con una ruta temporal corta pasó.

Respaldo/inventario privado: `~/.local/state/eqs-agent-tools.ysjSn0/`.
No se actualizarán por APT. Usar los comandos de actualización de cada herramienta
según su instalador, o revisar una nueva release ARM64 antes de reemplazar su
directorio/enlace. Para revertir, cerrar sus sesiones y retirar sólo los enlaces,
directorios y archivos enumerados en los manifiestos del respaldo; no borrar
configuraciones completas si ya tienen cambios, sesiones o credenciales nuevas.

## Particularidad gráfica de Ghostty

En H29, el arranque directo falla al crear el contexto OpenGL. El wrapper usa
**Mesa/llvmpipe OpenGL 4.5 por software**, únicamente para Ghostty; no cambia la
GPU, bibliotecas ni variables globales de Plasma. [Mesa documenta la selección
de renderizado por software](https://docs.mesa3d.org/envvars.html).

El comando configurado usa `env -u` antes de Fish para no transmitir los overrides
gráficos a las aplicaciones del usuario. `env=VARIABLE=` en Ghostty 1.3.1 **no
eliminó los valores heredados** en la prueba real. Se fuerza la integración Fish
porque el ejecutable inicial es `env`. Se conserva `epoll`, como en la PC.

No se fuerza `maximize=true`: también en la prueba del 9 de septiembre mostraba
una ventana del tamaño correcto, pero no arrancaba la terminal. La corrección
compartida está en [la configuración de Wayfire](../plasma-mobile-wf/README.md#maximized-window-sizing):
`core/transaction_timeout = 1000`. Con 100 ms, Ghostty confirmaba tarde el buffer
y terminaba en 800 × 479 aunque el área disponible era 1200 × 479. Tres aperturas
independientes y una de la calculadora KDE llenaron el área con el nuevo límite;
las tres terminales ejecutaron su comando y salieron normalmente.

**Límite:** renderizar por CPU puede consumir más batería y ser menos fluido.
QMLKonsole sigue siendo el respaldo. Teclado físico/táctil, fluidez y consumo en
una sesión sostenida requieren prueba del usuario; un proceso activo no prueba
todo eso. No se sustituyó el compositor ni se intentó portar otro renderer.

## Verificación

```sh
python3 port/shell/test-shell.py
python3 port/shell/test-hollywood.py
python3 port/shell/test-science.py
ghostty +validate-config --config-file="$PWD/port/shell/ghostty.conf"
desktop-file-validate port/shell/com.mitchellh.ghostty.desktop
```

Los diez grupos de checks pasan en host y ARM64: salida no interactiva limpia,
dependencias opcionales, cancelación y nombres de archivos con espacios/saltos de
línea, atajos/init reales, preservación de Bash explícito, prompt a 40/80 columnas
y aislamiento del entorno del comando Ghostty. El validador Ghostty se ejecuta
si está instalado; `+validate-config` acepta `--config-file`, no el flag gráfico
`--config-default-files`.

También cubren Homebrew no interactivo, argumentos de los launchers nuevos y
el rechazo de los bypasses de sandbox WebKit heredados de Droidian.

También se comprobó SSH interactivo en Fish, SSH no interactivo sin ruido,
QMLKonsole nuevo con proceso Fish y Ghostty nativo con OpenGL 4.5, recursos,
fuentes e integración Fish. Una PTY de prueba aceptó 1000 líneas UTF-8/truecolor;
el tiempo de escritura no es un benchmark de renderizado. `grim` rechazó la
captura de pantalla; **no se saltó el bloqueo ni se validaron píxeles**.
El lanzamiento final desde el `.desktop` produjo Fish sin los cuatro overrides
gráficos en su entorno; Wayfire informó ventanas mapeadas de 360 × 739, iguales
al área de trabajo, con los cuatro bordes colocados (`tiled-edges=15`).

## Hollywood (9 de septiembre)

Ejecutar **`hollywood`** en Ghostty; **Ctrl+C** lo cierra. Abre cuatro paneles,
con cambios cada 30 segundos. Para una pantalla más angosta: `hollywood -s 2`.

La versión APT 1.21 perdía `-s` al relanzarse mediante Byobu. Además faltaban
los programas de casi todos los paneles: no era un terminfo ausente de Ghostty.
El launcher entra directamente en un servidor tmux privado, sin cargar la
configuración ni alterar las sesiones de trabajo. Cerrar/desconectar la terminal
destruye ese servidor. Ctrl+C se intercepta allí para evitar el `pkill` amplio
del script upstream.

Se conserva `/usr/bin/hollywood` sin modificar. Su búsqueda relativa de widgets
se usa mediante un enlace en `~/.local/opt/hollywood/bin/hollywood`, con enlaces
en `../lib/hollywood/` a ocho widgets instalados: `apg`, `bmon`, `cmatrix`,
`errno`, `hexdump`, `htop`, `stat`, `tree`. Dependencias adicionales: `apg bmon
cmatrix htop tree moreutils ccze`; no se agregó un demonio atop ni reproducción
de audio. [Código upstream](https://github.com/dustinkirkland/hollywood/blob/master/bin/hollywood).

Archivos del repo: `hollywood` → `~/.local/bin/hollywood` y
`hollywood.tmux.conf` → `~/.config/hollywood/tmux.conf`. Los widgets son enlaces
a los archivos homónimos de `/usr/lib/hollywood/`, no copias modificadas.

**Verificado:** cuatro paneles vivos con texto en PTY ARM64 100 × 28; cierre de
servidor con Ctrl+C y al desconectar; lanzamiento real en Ghostty a 1200 × 479 y limpieza al
cerrarlo. El check de argumentos/aislamiento también pasa. El teléfono estaba
bloqueado: la legibilidad visual sostenida sigue pendiente de Eduardo.

## Ciencia y VS Code (9 de septiembre)

Instalados Octave, Scilab, wxMaxima, Python científico, SageMath, Spyder,
JupyterLab y **VS Code oficial ARM64**. Sage/Spyder usan un entorno Miniforge
independiente: APT ofrecía dependencias incompatibles con el Python/Qt nativo.
No se reemplazaron esos componentes ni se ejecutó un upgrade general.
[Comandos, versiones, mantenimiento, pruebas y límites](SCIENCE.md).

## Respaldo y reversión

Respaldo privado de esta instalación: `~/.local/state/eqs-shell.58woDK/`.
Conserva `.bashrc` y `qmlkonsolerc` anteriores, inventarios y hashes. No incluirlo
en Git. Antes de volver a instalar, respaldar el estado **actual**, no reutilizar
este directorio ni pisar personalizaciones posteriores.

Para volver a Bash, desde `bash --norc`, retirar únicamente el bloque entre
`# BEGIN EQS FISH` y `# END EQS FISH`; restaurar `.bashrc` completo sólo si no se
editó después. Restaurar la familia de fuente previa desde el backup si se desea.
No hace falta desinstalar Fish para usar Bash.

Para retirar Ghostty: cerrar sus sesiones normalmente, apartar sus tres archivos
de usuario indicados en la tabla y revisar `sudo apt-get -s remove ghostty` antes
de aplicar la eliminación. No ejecutar `autoremove` ni borrar paquetes compartidos.
El paquete administra una desviación de terminfo; dejar que `dpkg` la revierta.

## Herramientas independientes y editores (9 de septiembre)

Instalados por SSH sobre H29, **sin reflashear ni reiniciar**. No están integrados
en el builder de rootfs. Versiones verificadas en ARM64:

| Herramienta | Versión / ubicación | Mantenimiento |
|---|---|---|
| Homebrew | 6.0.22, `/home/linuxbrew/.linuxbrew` | `brew update` |
| mise / uv | 2026.9.3 / 0.12.11 | Homebrew |
| GitHub CLI / Neovim / ripgrep | 2.100.0 / 0.12.5 / 15.2.0 | Homebrew |
| Lazygit / GitUI | 0.65.0 / 0.28.1 | Homebrew |
| Yazi / ncdu | 26.9.1 / 2.9.2 | Homebrew |
| Mosh / Restic | 1.4.0 (fórmula `1.4.0_42`) / 0.19.1 | Homebrew |
| Brew Browser | 0.7.2, `~/.local/opt/brew-browser-0.7.2-eqs1` | Reconstrucción local |
| Antigravity CLI | 1.1.28, `~/.local/bin/agy` | `agy update` |
| Antigravity 2.0 | 2.12.2, `~/.local/opt/antigravity-2.12.2` | Descarga oficial ARM64 |
| Zed | 1.18.1, `~/.local/zed.app` | Actualizador nativo; `rsync` instalado |

Se eligió **Antigravity 2.0, la aplicación de agentes**, no el producto separado
Antigravity IDE. Zed y las dos descargas Antigravity provienen de sus proveedores,
no de paquetes comunitarios homónimos. No se copiaron credenciales ni se ejecutaron
prompts de agentes; el login y el uso de servicios remotos quedan para Eduardo.
En Ghostty, la CLI de Antigravity se abre con **`agy`**.

Discover, su backend Flatpak y el remoto **Flathub del sistema ya estaban instalados**.
Se reutilizan; no se añadió otro remoto ni se instalaron Cork, Bold Brew, Nix o
contenedores en el teléfono. Brew Browser es la única GUI de Homebrew agregada.

### Usar y actualizar

Abrir una terminal nueva carga `20-eqs-homebrew.fish`. La integración sólo corre
en Fish interactivo: mantiene `~/.local/bin` por delante y conserva Node 24.20.0,
Ghostty, Codex y Pi existentes. No se seleccionó otro runtime con mise.

```sh
brew update
brew outdated
brew upgrade       # sólo paquetes Homebrew; nunca usar sudo con brew
agy update
```

Mise y uv se actualizan con Homebrew, no con un segundo instalador. Los editores
figuran en el menú de Plasma; sus entradas usan rutas absolutas porque el PATH
gráfico no incluye necesariamente `~/.local/bin`. No usar «actualizar todo» en
Discover para el sistema base sin revisar las advertencias APT del README principal.
Las herramientas nuevas no solucionan el mantenimiento del kernel/Plasma/Droidian.

### Utilidades de terminal

Segunda tanda instalada con `brew install lazygit yazi ncdu gitui mosh restic`:
seis herramientas y cinco dependencias nuevas, todas desde bottles oficiales ARM64.
Las 18 fórmulas anteriores y el inventario APT quedaron sin cambios.

```sh
gitui       # desde un repositorio Git
lazygit     # alternativa para el mismo trabajo
yazi        # archivos desde la terminal
ncdu -r ~   # uso de espacio, sin permitir borrados desde ncdu
```

Mosh está disponible, pero falta probarlo contra un servidor con `mosh-server`.
Restic está instalado **sin copias programadas ni destino configurado**. No se
abrieron puertos ni se copiaron credenciales. Yazi no incluye la pila opcional de
previsualización multimedia (FFmpeg, Poppler, etc.).

Prueba nativa en un repositorio temporal: las cuatro TUI mostraron el archivo y
salieron con `q`/código 0; ncdu exportó el inventario. Restic creó, verificó y
restauró una copia cifrada descartable, y rechazó una contraseña incorrecta.
No se usaron repositorios ni datos reales del usuario. Los diez grupos de
`python3 port/shell/test-shell.py` pasaron en host y ARM64; falta la prueba visual
del usuario en Ghostty. Inventarios y prueba repetible privados:
`~/.local/state/eqs-tui.0foAu9/` (`tui-smoke.py`, `smoke.log`).

GitUI imprime un sufijo `nightly`, pero la fórmula usa el tag estable `v0.28.1`:
es la etiqueta por defecto del [build upstream sin `GITUI_RELEASE`](https://github.com/gitui-org/gitui/blob/v0.28.1/build.rs).
En la prueba con tmux desacoplado, Yazi tardó unos cinco segundos en salir:
su [cierre espera el sondeo del terminal](https://github.com/sxyazi/yazi/blob/v26.9.1/yazi-actor/src/app/quit.rs)
con [timeout de cinco segundos](https://github.com/sxyazi/yazi/blob/v26.9.1/yazi-emulator/src/probe.rs).
No fue necesario parchearlo ni cambiar su configuración.

### Compatibilidad y evidencia

- En la primera tanda se añadieron **62 paquetes APT** de dependencias, cero
  versiones preexistentes actualizadas o eliminadas. `dpkg --audit` limpio; hold de Plasma, boot ID,
  procesos Wayfire/Plasma/Maliit y hashes de Fish/Wayfire/Ghostty conservados.
- Brew Browser y Antigravity necesitan renderizado por software, limitado a sus
  launchers. Zed prueba Adreno, falla y selecciona automáticamente **llvmpipe Vulkan**;
  su log confirma el primer frame. No hay aceleración gráfica validada para ellos.
- Wayfire confirmó las tres ventanas mapeadas/maximizadas a **1200 × 479**,
  conservando escala 200% y rotación bloqueada. Apariencia, teclado, fluidez,
  consumo y autenticación requieren prueba del usuario: `grim` rechazó la captura.
- Droidian exportaba bypasses WebKit en `/etc/profile.d/zz-droidian.sh`. El launcher
  Brew Browser los neutraliza **sólo para esa aplicación**: proceso WebKit con
  `NoNewPrivs=1`, `Seccomp=2` y namespace de PID verificados. Regresión RED→GREEN
  incluida en `test-shell.py`. Antigravity también conserva sandbox de Chromium;
  no se agregó `--no-sandbox`. Sus listeners observados fueron sólo loopback.
- Homebrew informa Landlock no disponible en este kernel: sus post-install pueden
  ejecutarse sin sandbox. El prefijo separado **no es una barrera de seguridad**.
- Después de instalar las utilidades de terminal quedaban aproximadamente **4.2 GiB libres**
  en la raíz compartida de 16 GiB; `brew linkage --test` pasó para las seis herramientas.
  La [ampliación posterior del 9 de septiembre](../../docs/RECOVERY.md#ampliación-del-filesystem-9-de-septiembre)
  dejó **unos 200 GiB disponibles**, con inventario de paquetes y hashes protegidos
  conservados, y un nuevo arranque de H29/Plasma verificado por SSH.

### Origen y reconstrucción de Brew Browser

Fuentes: [Homebrew Linux](https://docs.brew.sh/Homebrew-on-Linux),
[Brew Browser v0.7.2](https://github.com/msitarzewski/brew-browser/releases/tag/v0.7.2),
[Zed ARM64](https://zed.dev/docs/linux), [Antigravity](https://antigravity.google/download).
El manifiesto nativo de la CLI ofrecía 1.1.28 aunque la página aún decía 1.1.25.
Se verificó SHA-512 de la CLI y SHA-256 de Zed contra los manifiestos oficiales.
El SHA-256 de la GUI Antigravity registra el archivo HTTPS descargado, no una firma.

Brew Browser se compiló del commit `a872efcb365ae87ea61b7c920e93c6b6f95de6e8`:
su release no incluía Linux ARM64. Host aislado con Rust 1.98.1/Trixie, GCC 14
cross, GTK3/WebKit2GTK 4.1 ARM64; no se compiló en el teléfono. Imagen de build:
`rust@sha256:bf5a9aa29062a6cb03c49bd59a46eb55e3cc770caf598a221a7866e500be3082`.
Conservar `Cargo.lock` y `package-lock.json`; `npm ci --ignore-scripts`,
`npm run check`, `npm test` (**57 pruebas**) y `npm run build` pasaron.

Para el build Rust, configurar linker/CC/CXX `aarch64-linux-gnu-*`,
`PKG_CONFIG_ALLOW_CROSS=1` y
`PKG_CONFIG_LIBDIR=/usr/lib/aarch64-linux-gnu/pkgconfig:/usr/share/pkgconfig`.
Desde `src-tauri`, usar `TAURI_CONFIG` con el contenido de
[`brew-browser-tauri.json`](brew-browser-tauri.json) y ejecutar:

```sh
cargo build --release --locked --target aarch64-unknown-linux-gnu \
  --features tauri/custom-protocol --bin brew-browser
```

El override permite altura mínima 300 y arranque maximizado; no modifica upstream.
SHA-256 del binario ARM64 instalado:
`ce2815d5f91220e4452ea684205365a3bd363dabe16bb40be62b33087872a9b9`.
El icono proviene de `src-tauri/icons/128x128.png`. Mantener el launcher local
al reemplazar el binario y repetir las pruebas nativas; no hay un paquete APT
ni un actualizador Linux validado para esta compilación.

Respaldo/inventarios privados: `~/.local/state/eqs-dev-packages.yhjqRR/`.
Los archivos descargados se conservaron en `.work/dev-packages/` del host y se
retiraron los tarballs temporales del teléfono. Para revertir, cerrar sólo estas
apps y retirar sus entradas/launchers y directorios nuevos; no restaurar configs
completas encima de cambios posteriores, borrar credenciales ni hacer `autoremove`.
