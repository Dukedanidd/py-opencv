# py-opencv

Proyecto experimental desarrollado en Python con OpenCV y MediaPipe para crear efectos visuales interactivos usando la cámara web y el seguimiento de la mano en tiempo real.

El programa detecta la mano del usuario, identifica la distancia entre el pulgar y el dedo índice, y genera distintos efectos visuales dependiendo del gesto realizado.

## Características

- Seguimiento de mano en tiempo real con MediaPipe.
- Captura de video mediante OpenCV.
- Detección de gesto tipo pinch entre pulgar e índice.
- Modo de trazo visual cuando los dedos están cerca.
- Modo de galaxia 3D cuando los dedos están separados.
- Partículas animadas con profundidad simulada.
- Rotación de la galaxia según el movimiento de la mano.
- Efecto glow para mejorar la apariencia visual.
- Visualización de FPS y cantidad de partículas en pantalla.

## Tecnologías utilizadas

- Python
- OpenCV
- MediaPipe
- NumPy

## Funcionamiento general

El sistema utiliza la cámara web para detectar una mano. A partir de los landmarks de MediaPipe, calcula la distancia entre la punta del pulgar y la punta del dedo índice.

Dependiendo de esa distancia, el programa cambia entre dos modos principales:

### Modo cerrado

Cuando el pulgar y el índice están cerca, se activa un marcador visual que deja un rastro brillante en pantalla.

### Modo galaxia 3D

Cuando el pulgar y el índice están separados, se genera una galaxia de partículas en 3D. La galaxia se mueve y rota de acuerdo con el desplazamiento de la mano.

## Requisitos

Antes de ejecutar el proyecto, instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

En caso de no tener el archivo `requirements.txt`, puedes instalar las librerías principales con:

```bash
pip install opencv-python mediapipe numpy
```

## Ejecución

Para correr el proyecto:

```bash
python main.py
```

El programa abrirá una ventana con la cámara web y los efectos visuales.

## Controles

- Acerca el pulgar y el índice para activar el modo de trazo.
- Separa el pulgar y el índice para activar el modo galaxia 3D.
- Mueve la mano para rotar y desplazar la galaxia.
- Presiona `q` para cerrar el programa.

## Estructura del proyecto

```text
py-opencv/
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Configuración principal

Dentro de `main.py` se pueden modificar algunos valores para ajustar el comportamiento del programa:

```python
CAMERA_WIDTH = 800
CAMERA_HEIGHT = 450
PINCH_THRESHOLD = 60
MAX_GALAXY_PARTICLES = 190
GALAXY_RADIUS = 185
```

Algunos parámetros permiten cambiar la resolución, la sensibilidad del gesto, la cantidad de partículas, el tamaño de la galaxia y la intensidad visual.

## Objetivo del proyecto

Este proyecto fue creado como práctica de visión por computadora e interacción visual usando Python. Su propósito es explorar cómo combinar detección de manos, animaciones generativas y efectos gráficos en tiempo real.

## Autor

Desarrollado por [Dukedanidd](https://github.com/Dukedanidd).
