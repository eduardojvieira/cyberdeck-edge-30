# Waydroid + Google Play en H29

Instalado por SSH el **11 de septiembre de 2026** sobre el teléfono de Eduardo,
sin reflashear, reiniciar el teléfono ni actualizar paquetes existentes.
Es una incorporación **opcional al teléfono**, no al ZIP limpio del 10 de septiembre.

## Uso

Abrir **Google Play Store** desde el cajón de Plasma. El launcher generado por
Waydroid inicia la sesión Android cuando hace falta; Plasma sigue siendo el escritorio.

```sh
waydroid status
waydroid app launch com.android.vending
waydroid session stop                 # cierra Android, no Droidian
```

El usuario debe iniciar sesión en Google personalmente. Si aparece el aviso de
dispositivo no certificado, seguir la [guía oficial de registro](https://docs.waydro.id/faq/google-play-certification).
Se dejó `~/Waydroid-Google-Play.txt`, modo 600, con el GSF Android ID y las
instrucciones. Ese archivo/identificador no se incluye en Git ni en imágenes.
El registro **no garantiza Play Integrity, banca ni DRM**; nunca relockear H29.

### Acceso de Play Store en Plasma (12 de septiembre)

El [generador de Droidian Waydroid `c5380c1`](https://github.com/droidian/waydroid/blob/c5380c1/tools/services/user_manager.py)
crea los accesos Android con `NoDisplay=true`. Play estaba instalado, pero su
acceso quedaba oculto. Además, `app_settings` no es un identificador válido de
acción para `desktop-file-validate`; se normalizó a `app-settings`.

Después del primer arranque Android, ejecutar **como usuario, sin sudo, desde
una terminal de Plasma**. Se reutiliza el acceso generado, sin duplicar iconos:

```sh
(
    set -eu
    app="$HOME/.local/share/applications/waydroid.com.android.vending.desktop"
    test -f "$app"
    backup=$(mktemp -d "$HOME/.cache/eqs-waydroid-launcher.XXXXXX")
    cp -p "$app" "$backup/"
    sed -i 's/app_settings/app-settings/g' "$app"
    desktop-file-edit --set-key=NoDisplay --set-value=false "$app"
    desktop-file-validate "$app"
    kbuildsycoca6 --noincremental
    printf 'Backup: %s\n' "$backup"
)
```

El generador conserva el acceso de la app si ya existe: el cambio sobrevivió
al cierre y nuevo arranque de la sesión Android. Si se elimina/recrea ese
archivo, habrá que repetirlo. Para revertir, restaurar el `.desktop` del backup
y volver a ejecutar `kbuildsycoca6 --noincremental`.

**Verificado en el teléfono:** visibilidad con `Gio.DesktopAppInfo.should_show()`
(antes `false`, después `true`), validación del `.desktop` y apertura mediante
`kstart --application waydroid.com.android.vending`, incluso desde sesión Android
detenida. `sys.boot_completed=1`, Play en primer plano, ventana Wayfire mapeada y
captura Android de la pantalla de acceso en español. También se comprobó
`kstart --application Waydroid`; el fallo general de arranque reportado no se
reprodujo y no se modificó el motor Android. Por SSH se necesita el entorno real de Plasma,
incluido `XDG_MENU_PREFIX=plasma-`, para probar la resolución de accesos de KDE.

No se reinstaló ni reinicializó Android; tampoco se reiniciaron el teléfono o
Wayfire. Login Google y confirmación de interacción táctil: usuario.

**Pendiente:** Wayfire registró dos vistas mapeadas del mismo proceso de Play,
también al abrirla desde una sesión Android detenida (`waydroid.open_windows=2`).
Android mostró una sola actividad visible y una captura correcta. La comprobación
de una única vista no pasó; falta determinar la causa y el impacto en la interfaz.

## Conjunto instalado

| Componente | Versión/origen |
|---|---|
| Waydroid | Droidian `1.5.4-1+git20250824231602.c5380c1.next.production` |
| Vendor | `waydroid-vendor-33`, `13.0.0+lineage20250809+git20250824233201.fe6e10a.next.production`; proporciona también `waydroid-vendor-32` |
| System | GAPPS ARM64 oficial, LineageOS 20 / Android 13, `20260403` |
| Dependencia de imagen | `waydroid-system-custom=2+git20231006194425.823b006.trixie.production` |
| Red | `ethtool=1:6.14.1-1` y NAT/bridge del kernel H29 existente |

La simulación y la comparación dpkg final dieron **14 paquetes nuevos, cero
actualizaciones y cero eliminaciones**. No se agregaron repositorios ni se hizo
`autoremove`/`full-upgrade`. `auto_adb=False` evita la conexión ADB automática.

El ZIP de sistema fue obtenido del [canal oficial GAPPS ARM64](https://ota.waydro.id/system/lineage/waydroid_arm64/GAPPS.json),
1.326.285.880 bytes, SHA-256 verificado en PC y teléfono:

```text
c5e557605887664ab1da6c17ff0032317735a0425b8055ee9073fdbcd00899c2
```

Se extrajo únicamente `system.img` en `/etc/waydroid-extra/images/` y se enlazó
allí `vendor.img` al archivo del paquete en `/usr/share/waydroid-extra/images/`.
El par preinstalado hace que `waydroid init` omita la descarga OTA: **`-s GAPPS`
por sí solo no convierte una imagen vanilla**. La configuración detecta
`HALIUM_12` por el VNDK 31 del entorno existente; no se modificaron esas propiedades.

## Ajustes de integración

| Archivo/ajuste | Motivo y límite |
|---|---|
| `eqs-waydroid-binder` → `/usr/local/sbin/` | Reutiliza `allocBinderNodes` de Waydroid para los tres `anbox-*`; no remonta binderfs ni reemplaza el Binder del HAL nativo. |
| `eqs-waydroid-gpu` → `/usr/local/sbin/` | El KGSL nativo es root:render 0660; los UIDs Android no pertenecen a ese grupo. Crea un nodo privado dentro de `/dev/eqs-waydroid` root 0700 y lo mapea al contenedor con permiso 0666, sin abrir el dispositivo del host a todos. |
| `20-eqs-binder.conf` → `/etc/systemd/system/waydroid-container.service.d/` | Ejecuta ambas preparaciones antes de iniciar el servicio; luego de regenerar config con `init`/`upgrade`, reiniciar **sólo** este servicio. |
| `waydroid-net-checksum.patch` | H29 no tiene `xt_CHECKSUM`; el script tiene `set -e` dentro de `start`. Deshabilita TX offload sólo en `waydroid0` cuando falla esa regla. Errores de NAT/filtros o de ethtool siguen siendo fatales. |
| `nfcd.service` deshabilitado | NFC aún no está portado. Su `binder-wait` indefinido bloqueaba el D-Bus de Waydroid al intentar restaurarlo durante el cierre. Rehabilitar sólo con un HAL NFC funcional. |

El script de red original quedó en
`/usr/lib/waydroid/data/scripts/waydroid-net.sh.distrib`, mediante **dpkg-divert
local**. Hash original `6c3eb1334bb1eeabda391d44f1b0ad580e62700bd1485bd633fdbee70f8f2fbc`;
parcheado `590d09c5e7b8886197003cb34b66c250cc49af33500c6195c04549fad1f79126`.
No se cambiaron las alternativas globales iptables ni se vació el firewall.

Los helpers se instalan con modo **0755** y dueño root; el drop-in con **0644**.
No ejecutarlos desde el checkout como una instalación automática: requieren
Waydroid ya inicializado y el Binder/KGSL de H29. Conservar configuración y
script de red anteriores antes de aplicar los ajustes.

## Evidencia y límites

- **Teléfono:** Binder/KGSL preparados dos veces sin alterar identidad, dueño o
  modo de los nodos nativos. Hashes de boot/vendor_boot/DTBO/vbmeta y wayfire.ini
  iguales; mismo boot ID, Wayfire original sigue ejecutándose.
- Dos arranques Android completos (`sys.boot_completed=1`), cierre de sesión
  con salida 0 y reapertura desde el `.desktop` real de Google Play Store.
- Play Store y GMS presentes; actividad de Play Store sin autenticar en primer
  plano de Android, ventana mapeada por Wayfire. Login/descarga de apps: usuario.
- DHCP, DNS y ping desde Android comprobados; TX checksumming desactivado en
  el bridge. SurfaceFlinger informa **Adreno 730 / OpenGL ES 3.2**, no SwiftShader.
- Se vio el launcher Android mediante captura. La captura HWC del host falla;
  capturar el display Android principal puede bloquearse con las ventanas de
  apps separadas. No equivale a haber verificado visualmente toda la tienda.
- Hay avisos de arranque pendientes de depurar: un reinicio inicial del composer
  (`Binder threadpool cannot be shrunk after starting`), estado de init de
  SurfaceFlinger `stopping` aunque responde, y hook post-stop upstream `/dev/null`
  con salida 126. No se certifica suspensión, estabilidad prolongada ni todas
  las APIs/periféricos Android. Cámaras, micrófono, NFC y cuentas no se probaron.

Pruebas reproducibles:

```sh
# Host: sólo funciones de red con comandos simulados; nunca toca interfaces.
python3 port/waydroid/test-net.py RUTA_AL_WAYDROID_NET_PARCHEADO

# EXCLUSIVAMENTE en el teléfono autorizado, después de instalar los helpers.
sudo python3 check-prepare.py
```

La prueba de red falla con el script original y pasa con el parche: incluye
fallos obligatorios de NAT y de ethtool. La prueba nativa verifica idempotencia,
separación Binder y aislamiento de permisos KGSL. No ejecutar el checker nativo
como parte de un recorrido indiscriminado de tests sobre la PC.

## Mantenimiento y retiro

Google actualiza sus apps dentro de Android; **la imagen GAPPS se mantiene aparte
de APT**. Aquí `system_ota=None` porque se usa imagen local. Revisar una nueva
imagen oficial y su hash antes de reemplazarla, con Waydroid detenido, conservando
la anterior y los datos. No volver a inicializar/borrar datos para actualizar apps.

Una actualización de Waydroid deja el nuevo script upstream en `.distrib`:
revisar/rebasar el parche, correr el test y reiniciar sólo Waydroid. La copia
local no incorpora automáticamente futuras correcciones upstream.

Para dejarlo inactivo: `waydroid session stop` y
`sudo systemctl disable --now waydroid-container.service waydroid-notification-server.service`.
No se necesita borrar datos. Para retirar una adaptación, conservar sus backups
y revisar el diff; no eliminar genéricamente `/dev`, imágenes de arranque ni LVM.
Evidencia privada: `.work/eqs-waydroid-20260911/` en PC y
`/var/lib/eqs-waydroid-20260911/` en el teléfono.
