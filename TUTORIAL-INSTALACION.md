# Instalar Kali-Bspwm-Ice desde Git

Guía en español de W4lterSec para seguir la instalación y preparar un tutorial.
Esta edición utiliza texto y comandos. Las capturas y vídeos reales se añadirán después.

## Preparar Kali

Necesitas Kali Linux con una sesión X11, una conexión a Internet y un usuario
normal que pueda utilizar sudo. Comienza desde Xfce; la selección de bspwm se
hace después de instalar. La instalación está destinada a Kali, no a cualquier
distribución Linux ni a Windows directamente.

Si utilizas VirtualBox, crea primero una instantánea con la VM apagada. Comprueba
que tienes espacio y conectividad: la instalación puede descargar muchos paquetes,
incluidos Firefox ESR y Burp Suite si faltan. Anota la versión de Kali, el hipervisor
y la resolución para acompañar después las evidencias del tutorial.

## Descargar el proyecto

Abre una terminal en Kali. Si Git no está instalado:

```bash
sudo apt update
sudo apt install git
```

Clona el repositorio y entra en su carpeta:

```bash
git clone https://github.com/W4lterSec/Kali-Bspwm-Ice.git
cd Kali-Bspwm-Ice
git rev-parse HEAD
```

Guarda el identificador que muestra el último comando para indicar la revisión
exacta utilizada en tu grabación. Si la carpeta ya existe, revísala antes de volver
a clonar; no la borres si contiene cambios tuyos.

## Revisar e instalar

Lee `README.md`, `THIRD_PARTY_NOTICES.md`, `install.sh` y `setup.py` antes de
instalar. El instalador instala dependencias con APT, descarga Oh My Zsh y
Powerlevel10k y guarda una copia de la configuración que va a sustituir.
Ejecuta como usuario normal, sin anteponer sudo:

```bash
bash install.sh
```

Acepta la solicitud de sudo únicamente en la terminal de tu Kali. No grabes tu
contraseña. El acabado predeterminado es Glass y la escala es automática.

Para elegir otro acabado y una escala explícita desde el inicio, utiliza en su
lugar una única instalación con los parámetros deseados, por ejemplo:

```bash
bash install.sh --style solid --scale 150
```

Los estilos válidos son `glass`, `solid` y `light`. Las escalas son `auto`, `100`,
`125`, `150` y `200`. La escala cambia el tamaño de la interfaz; no crea modos de
vídeo ni fuerza una resolución nueva.

## Entrar en bspwm

Cuando la terminal indique que la instalación ha terminado:

1. Guarda tu trabajo y cierra la sesión de Xfce.
2. En la pantalla de acceso selecciona la sesión **bspwm**.
3. Entra con tu usuario habitual de Kali.
4. Comprueba que aparecen los ocho indicadores de escritorio.

Super es la tecla Windows. Atajos para comenzar:

| Atajo | Acción |
| --- | --- |
| Super + Enter | Abrir una terminal Kitty |
| Super + D | Abrir el menú de aplicaciones Rofi |
| Super + 1…8 | Cambiar de escritorio |
| Super + Shift + 1…8 | Enviar una ventana a otro escritorio |
| Super + flechas | Cambiar el foco entre ventanas |
| Super + W | Cerrar la ventana seleccionada |
| Super + Alt + Q | Cerrar la sesión de bspwm |

La lista completa está en el README. Esta edición conserva los atajos originales
de la configuración base, incluidos los atajos 9 y 0 aunque utiliza ocho escritorios.

## Elegir el acabado y el tamaño

Abre Kitty con Super + Enter. Desde la carpeta del repositorio:

```bash
bash personalizar.sh glass auto
```

Otros ejemplos de selección, para ejecutar uno cuando quieras cambiar el aspecto:

```bash
bash personalizar.sh solid 150
bash personalizar.sh light 100
bash personalizar.sh glass 200
```

Abre una terminal nueva para comprobar cambios de tamaño de texto de Kitty.
Glass aplica transparencia uniforme del 90 % con Picom; Solid y Light son opacos.
Si el compositor consume demasiados recursos en tu VM, prueba Light.

## Comprobar que funciona

Desde la carpeta del repositorio:

```bash
bash doctor.sh
python3 -m unittest discover -s tests -v
python3 ~/.local/share/kali-dragon-ice/scripts/check-graphics.py
```

Las pruebas automáticas comprueban configuración, recursos y montaje/restauración
en carpetas temporales. No sustituyen la comprobación gráfica en Kali:

- Abre tres terminales, cambia el foco y redimensiónalas.
- Cambia entre los ocho escritorios y abre Rofi.
- Comprueba que las ventanas se mantienen estables al cambiar de foco.
- Revisa volumen, IP local, CPU, memoria y tráfico de red.
- Espera diez minutos para comprobar la rotación del fondo.
- Cierra y abre la sesión para comprobar que la configuración persiste.

Sin túnel conectado, el indicador VPN debe mostrar OFF. Las IP son las de las
interfaces de Kali; antes de publicar capturas o registros revisa qué datos muestran.

## Volver a la configuración anterior

Guarda tu trabajo, cierra bspwm y entra en Xfce. Desde la carpeta del repositorio:

```bash
bash uninstall.sh
```

El desinstalador restaura la configuración anterior a la instalación más reciente.
Conserva los paquetes APT instalados y los archivos retirados. Las copias se guardan
en `~/.local/state/kali-dragon-ice/`. Para recuperar el estado completo de una VM,
utiliza la instantánea previa del hipervisor.

## Orden propuesto para grabar el tutorial

1. Presentar la versión de Kali y la instantánea inicial.
2. Clonar el repositorio y registrar la revisión.
3. Mostrar el comando de instalación y el resultado final.
4. Elegir bspwm en la pantalla de acceso.
5. Demostrar terminales, menú, escritorios y estilos.
6. Ejecutar el diagnóstico y explicar cualquier limitación observada.
7. Mostrar cómo se vuelve a Xfce y dónde están las copias de configuración.

Utiliza resultados de tu propia instalación. Si un paso falla, documenta el error
y su solución antes de presentarlo como completado. Las capturas y vídeos se
añadirán al repositorio cuando estén preparados.
