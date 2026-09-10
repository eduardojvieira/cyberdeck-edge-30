# GPU: compositor acelerado, Zed OpenGL demostrado en prueba aislada

**9 de septiembre de 2026.** Wayfire usa Adreno 730 por GLES. Zed habitual
todavía usa llvmpipe; una instancia descartable ya seleccionó Adreno y renderizó
su primer frame sin emulación. **No se instaló el experimento en el lanzador
normal**, ni se reemplazaron los drivers o reinició Plasma.

## Dos fallos comprobados

Prueba nativa con Zed **1.19.2**, commit
`df181c6f58d02677b385fa947d6bfde6d3530078`, wgpu **29.0.4** y glow **0.17.0**
según su [Cargo.lock](https://github.com/zed-industries/zed/blob/df181c6f58d02677b385fa947d6bfde6d3530078/Cargo.lock).
El diagnóstico anterior correspondía a Zed 1.18.1; no confundir ambas ejecuciones.
Driver nativo: `OpenGL ES 3.2 V@0615.74`, Adreno 730; kernel H29 intacto.

| Cambio aislado | Resultado real |
|---|---|
| Ninguno | Adreno falla al crear el dispositivo: `Parent device is lost`; Zed elige llvmpipe. |
| Resolver `glBufferStorage` mediante `glBufferStorageEXT` | Crea el dispositivo; falla la superficie EGL con `BadAttribute`. |
| Además convertir atributos EGL de 64 a 32 bits y usar la llamada legacy | Selecciona Adreno, renderiza un frame, informa `is_software_emulated: false`. |

**Búferes.** Un contexto GLES independiente, con pbuffer de 1 × 1 y asignaciones
de sólo 512 bytes, comprobó que el símbolo core `glBufferStorage` devuelto por
EGL no reserva memoria: tamaño 0, mapeo nulo y `GL_INVALID_VALUE`. La función
`glBufferStorageEXT` sí reserva y mapea, incluso con flags persistente/coherente
`0xc2`; `glBufferData` también funciona. No es falta de soporte para ese mapeo.
[La extensión oficial define el nombre EXT](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_buffer_storage.txt).
[wgpu convierte un mapeo nulo en `DeviceError::Lost`](https://github.com/gfx-rs/wgpu/blob/v29.0.4/wgpu-hal/src/gles/device.rs).

**Superficie.** [wgpu llama a EGL 1.5 con atributos del ancho de un puntero](https://github.com/gfx-rs/wgpu/blob/v29.0.4/wgpu-hal/src/gles/egl.rs).
El código upstream de [libhybris EGL](https://github.com/libhybris/libhybris/blob/master/hybris/egl/egl.c)
inspeccionado (blob `0051d3755edfc2dc2a239c462dc332786ca849fe`) convierte el
puntero a `EGLint *`, no sus elementos. En ARM64 son anchos diferentes. El
control nativo convirtió los elementos y llamó a `eglCreateWindowSurface`:
desapareció `BadAttribute`, **sin cambiar el modo de buffering ni ocultar errores**.
El blob inspeccionado no identifica por sí solo la fuente del paquete instalado.

## Límites y próximo cambio

El control fue un pequeño módulo `LD_AUDIT`, compilado nativamente con
`-Wall -Wextra -Werror`, aplicado **sólo al proceso de prueba**. No usarlo como
variable de sesión ni copiarlo a `/etc/ld.so.preload`. Es una herramienta para
aislar las causas, no un arreglo de producción validado para otros clientes,
X11, procesos hijos o futuras versiones. Las instancias descartables terminaron;
no se enviaron órdenes de cierre a las aplicaciones del usuario.

La instancia GPU también ajustó la ventana a 1200 × 479 lógicos / 2400 × 958
físicos, escala 200%. Primer frame y log de GPU **no prueban** calidad visual,
entrada, edición sostenida, suspensión ni ausencia de errores en otros shaders.
Vulkan/Turnip no se habilitó. Ghostty sigue usando su OpenGL por software aislado.

Siguiente paso: corregir selección de la función GLES y conversión EGL en la
dependencia correspondiente, preparar una biblioteca/build privado para Zed y
verificar aperturas repetidas, píxeles, edición y reversión antes de activarlo
en el lanzador habitual. No hace falta flashear ni cambiar el compositor.

Evidencia privada de esta sesión:

- Host: `.work/eqs-gpu-userspace/`, fuentes upstream, `probe-gles-buffer.py`,
  resultados antes/después y `egl-buffer-audit.c` (versión con ambas correcciones).
- Teléfono: `~/.local/state/eqs-gpu.0KlZPw/zed-gl-{baseline,buffer-fixed,platform-fixed}/data/logs/Zed.log`.
- El perfil descartable usa `--user-data-dir`: sus ajustes van en
  `DATA/config/settings.json`, no en `XDG_CONFIG_HOME/zed/`. Las pruebas nuevas
  deshabilitaron auto-update allí; el perfil normal no se modificó.
