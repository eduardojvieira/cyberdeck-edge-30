# ONLYOFFICE en el Edge

Instalado por SSH el **10 de septiembre de 2026**, sin reflashear:
**ONLYOFFICE Desktop Editors 9.4.0-129, Linux ARM64**. Abrir el icono
**ONLYOFFICE** o ejecutar `desktopeditors` / `onlyoffice-desktopeditors`.
No necesita cuenta ni servidor para trabajar con archivos locales.

Se utilizó el [DEB ARM64 oficial de la versión 9.4.0](https://github.com/ONLYOFFICE/DesktopEditors/releases/tag/v9.4.0),
comprobando el SHA-256 contra el digest de GitHub antes de instalar:

```text
onlyoffice-desktopeditors_arm64.deb
SHA256: ce141a103051e220a89839dd5dc8511172ae5b989e8de9bda0e07c34b0b7702c
```

## Integración y comprobaciones

- APT agregó 12 paquetes: la aplicación y sus dependencias de fuentes,
  codecs y utilidades. Los inventarios antes/después verifican **cero cambios
  o eliminaciones de paquetes preexistentes**; los holds del port siguen iguales.
- La aplicación ocupa aproximadamente **1,3 GiB** en `/opt/onlyoffice/desktopeditors`.
  No se instalaron las fuentes Microsoft opcionales.
- Se observaron ventanas reales para un documento `.docx`, una hoja `.xlsx`
  y una presentación `.pptx`, todas a **1200 × 479**, maximizadas por las
  reglas existentes. No requirió wrapper, cambios en Qt,
  flags gráficos adicionales ni reiniciar Plasma. El `.desktop` original
  pasó `desktop-file-validate` y se regeneró la caché KDE.
- Las pruebas usaron perfiles privados y unidades systemd temporales que
  se cerraron al terminar. **Edición/guardado y revisión visual de los píxeles
  quedan pendientes**: las capturas por HWC y raíz X11 fallaron en este port.
- El paquete oficial inicia sus procesos CEF con `--no-sandbox`; no se agregó
  ese parámetro como workaround. No considerar la aplicación aislada del
  resto de los archivos del usuario; evitar documentos o conexiones no confiables.

## Actualizaciones sin Sid

Se agregó el [repositorio oficial de Desktop Editors](https://helpcenter.onlyoffice.com/desktop/installation/desktop-install-ubuntu.aspx)
con `Architectures: arm64`, HTTPS y una clave exclusiva mediante `Signed-By`.
Sólo `onlyoffice-desktopeditors` recibe prioridad **500**; los demás paquetes
de ese origen tienen prioridad **-1**. El índice firmado se actualizó bien y
APT ofrece la versión instalada. No se agregó Debian Sid.

```sh
sudo apt update
apt-get -s --only-upgrade install onlyoffice-desktopeditors
# Revisar la simulación antes de aplicar:
sudo apt-get --only-upgrade install onlyoffice-desktopeditors
```

La suite se llama `squeeze` en el servidor del proveedor; **no cambia la base
de Droidian a Debian Squeeze**. Configuración instalada:

- `/etc/apt/sources.list.d/onlyoffice.sources`
- `/etc/apt/preferences.d/50-onlyoffice`
- `/usr/share/keyrings/onlyoffice-archive-keyring.gpg`
- Fingerprint: `E09CA29F6E178040EF22B4098320CA65CB2DE8E5`.

No ejecutar `apt purge` como rollback inocuo: el `postrm` del proveedor borra
configuración y datos locales de ONLYOFFICE bajo `/home/*`. Para retirar sólo
el paquete, usar `apt remove` después de guardar documentos y conservar los
perfiles; no hacer `autoremove` a ciegas.

Evidencia privada: `~/.local/state/eqs-onlyoffice-20260910/` en el teléfono y
`.work/onlyoffice/` en la PC: inventarios, paquete, firma, simulación, logs y
perfiles de prueba. No se activaron cuentas, nubes, IA ni plugins adicionales.
