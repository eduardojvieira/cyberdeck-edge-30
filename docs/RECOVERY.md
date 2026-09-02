# Primer flash y recuperación de `eqs`

## Estado del artefacto

El ZIP actual es **`eqs-dev` HOST-ONLY**: se construyó e inspeccionó en el host, pero nunca se flasheó ni arrancó en un Motorola Edge 30 Ultra. No demuestra arranque, pantalla, touch, red, carga, USB ni recuperación. No es la imagen diaria cifrada.

## Gate NO-GO

**No ejecutar `flash_all.sh`** hasta que estén completas las precondiciones de esta página, exista una recuperación stock concreta para esa unidad y Eduardo autorice expresamente el flash. El bootloader está abierto y debe permanecer abierto: **nunca relockear** con una imagen modificada.

No usar hub USB-C para fastboot, Rescue ni el primer flash. Usar un cable directo conocido entre el teléfono y el host.

## Inventario privado previo

Guardar fuera del repositorio y sin IMEI/serial en archivos versionados:

- variante exacta (`XT2241-1` o `XT2241-2`), canal y región;
- build y fingerprint Android stock exactos;
- slot activo y estado conocido de ambos slots A/B;
- firmware stock recuperable para esa combinación, sus hashes y las imágenes disponibles;
- copia de los datos que se quieran conservar.

La compatibilidad del firmware y de la herramienta de Motorola debe confirmarse sobre la unidad física. No se asume intercambiabilidad entre regiones, variantes ni slots.

La base de fuentes congelada es Android 14 `U1SQS34.52-21-1-10`, fingerprint `motorola/eqs_ge/eqs:14/U1SQS34.52-21-1-10/504bf-893e0:user/release-keys`. Es una base de fuentes, **no** prueba del firmware de esta unidad: si no coincide, sigue siendo NO-GO hasta demostrar compatibilidad.

## Preparación de recuperación

1. Tener `fastboot` conocido y comprobado en el host.
2. Instalar [Motorola Software Fix](https://en-us.support.motorola.com/app/softwarefix/) y probar sólo que reconoce la unidad; no iniciar Rescue durante esa comprobación.
3. Confirmar que la recuperación oficial identifica la unidad y ofrece el firmware correcto. Software Fix/Rescue es para Windows y su proceso borra datos; ver sus [requisitos y descarga](https://en-us.support.motorola.com/app/answers/detail/a_id/158726/) y su [guía destructiva](https://en-us.support.motorola.com/app/answers/detail/a_id/167770/).
4. Conservar una imagen Droidian anterior conocida, si existe, junto con su SHA-256, para rollback rápido.

Motorola advierte que desbloquear el bootloader reduce las protecciones del arranque; mantenerlo abierto es necesario para imágenes modificadas. Véase el [aviso legal de bootloader](https://en-us.support.motorola.com/euf/assets/docs/Bootloader-Legal_Agreement_and_Warning.pdf).

## Si Eduardo autoriza el primer flash

1. Extraer el ZIP en el host y verificar su SHA-256 contra `SHA256SUMS`/el manifiesto entregado; desde la raíz del repositorio, el manifiesto generado se comprueba con `sha256sum -c .work/eqs-rootfs/SHA256SUMS`.
2. Conectar el teléfono directamente, sin hub, y entrar en fastboot.
3. Desde el directorio extraído, ejecutar el `flash_all.sh` incluido. No sustituirlo por comandos de particiones manuales.

El flasher generado primero comprueba que el producto reportado sea `eqs`; luego escribe `boot`, `dtbo`, `vbmeta` y `vendor_boot` en **A y B**, flashea `userdata` y reinicia. Por tanto, **reemplaza `userdata` y borra los datos del teléfono**.

## Rollback

Ante un fallo, priorizar en este orden:

1. fastboot con una imagen Droidian anterior conocida y verificada para la misma unidad;
2. Software Fix/Rescue oficial, sólo después de confirmar que reconoce la unidad y el firmware aplicable.

No se documentan comandos stock por partición, EDL ni test points: dependen del firmware y de evidencia física que aún no existe. No afirmar recuperación completa, validez regional ni estado de slots hasta ensayarlo en el teléfono.
