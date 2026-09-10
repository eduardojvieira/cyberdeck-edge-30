# Instalación de la imagen consolidada eqs

**No ejecutar en el teléfono actual para conservar sus datos.** Esta imagen es
una instalación limpia experimental; el arranque H29 y los fixes individuales
tienen evidencia nativa, pero **esta imagen completa nueva no fue flasheada**.
No es daily cifrada ni una actualización in-place.

## Antes de escribir

- Sólo Motorola Edge 30 Ultra `eqs`, bootloader abierto, Android 14 RETAR
  `U1SQS34.52-21-1-16`, como la unidad XT2241-2 del proyecto.
- `userdata` debe tener **241246908416 bytes o más**. La imagen usa 224,52 GiB
  de ext4 dentro de LVM, compartidos por `/` y `/home`. No cambia GPT ni realiza
  crecimiento/reparación automática al iniciar. No sirve para un layout menor.
- El perfil táctil figura en `RELEASE.txt`: `replacement` tiene la calibración
  2× del módulo reemplazado de Eduardo. **No usarla para una pantalla original**;
  generar el perfil `stock` en ese caso. No se pueden distinguir sólo por el
  nombre `goodix_ts`.
- Cable directo, **sin hub**, batería cargada, backup propio comprobado, stock
  original y computadora con fastboot. B no es un backup y comparte userdata.
- Leer `INPUTS.json`, `PACKAGES.tsv`, `RELEASE.txt`, `LVM.txt` y `FILESYSTEM.txt`.
  Ejecutar `sha256sum --strict -c SHA256SUMS` y `bash flash-candidate.sh --check`.
  Estas dos comprobaciones no acceden al dispositivo.

## Secuencia manual, destructiva sólo con autorización nueva

**Flashear `userdata.img` reemplaza el sistema, `/home`, claves, programas y
datos actuales.** El archivo no contiene tus sesiones ni credenciales. No
ejecutar el viejo `flash_all.sh`: escribía A/B y usaba otro método de transferencia.

1. Identificar explícitamente `SERIAL` con `fastboot devices`. En AP Fastboot,
   `bash flash-candidate.sh --rescue-a SERIAL` instala el rescate A completo
   conocido. Sus controles rechazan otro modelo/bootloader o equipo bloqueado.
   Es una escritura de arranque/recovery, no una recuperación de datos.
2. Entrar a FastbootD usando `fastboot -s SERIAL reboot fastboot`. Confirmar
   `fastboot -s SERIAL getvar is-userspace` = `yes`, producto `eqs` y tamaño
   suficiente con `fastboot -s SERIAL getvar partition-size:userdata`.
   **Detenerse si difiere algo**; no sustituir por telnet ni forzar otra partición.
3. Con backup y consentimiento de pérdida de datos ya resueltos, transferir:
   `fastboot -s SERIAL flash userdata userdata.img`.
   Esperar éxito completo. **No hacer factory reset después**: destruiría LVM.
4. Volver a AP Fastboot: `fastboot -s SERIAL reboot bootloader`. Comprobar
   `is-userspace=no`, seleccionar A si hiciera falta y ejecutar
   `bash flash-candidate.sh --flash-a SERIAL`. El helper escribe solamente
   boot/vendor_boot/DTBO/vbmeta de A, comprueba intentos y no reinicia solo.
5. Sólo si todos los pasos terminaron correctamente: `fastboot -s SERIAL reboot`.
   No relockear. Si no arranca, volver al rescate y recoger evidencia; no repetir
   flash idéntico ni hacer wipe para diagnosticar.

La transferencia de userdata por FastbootD y el rescate están basados en los
ensayos anteriores del proyecto; **la secuencia de esta release completa aún
requiere validación física autorizada**. Conservar el celular que ya funciona.

## Primer inicio y límites

- Cambiar el PIN de plantilla **1234 antes de conectar una red**.
- Plasma sobre Wayfire/HWC, escala 200 %, horizontal bloqueado, ventanas
  maximizadas, Inicio/Recientes por gestos, control manual **Teclado táctil**.
- La cámara abre por su launcher corregido; comprobar preview y fotos en ambas
  orientaciones y cámaras. Auxiliares y calidad máxima siguen pendientes.
- Bluetooth carga los módulos H29 exactos; no reutilizarlos con otro kernel.
- El hub USB necesita PD para una conexión fiable desde cero. No se activan
  experimentos ADC/POR, swaps de alimentación ni capturas/reinicios programados.
- SSH entrante no se aprovisiona; no hay claves de acceso incluidas. La rootfs
  sigue siendo una preview sin LUKS. No guardar secretos laborales allí.
  El initramfs de desarrollo conserva el canal USB de emergencia sin autenticación;
  no equivale a una imagen diaria endurecida.
- APT queda en `current`, no `next`; Plasma/kernel se protegen con holds y
  `FLASH_BOOTIMAGE=no`. Simular upgrades antes de aplicar, nunca quitar protecciones
  para resolver dependencias a ciegas. La corrección privada de Qt5 se desactiva
  ante un cambio de ABI y requiere reconstrucción, no bloquea APT.
- Herramientas personales/grandes se documentan aparte en `port/shell/`; esta
  base no clona Homebrew, entornos Python, logins, plugins privados ni `/home`.

## Recuperación

El rescate A restaura el kernel stock y la recovery diagnóstica del proyecto,
**no Android entero**. Permite inspeccionar la raíz `ro,noload` y recuperar logs.
Para regresar a Android se necesita el firmware completo firmado correspondiente
y el procedimiento de `docs/RECOVERY.md`; no mezclar imágenes de Bronco.
