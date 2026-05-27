import cv2
import mediapipe as mp
import math


# =========================
# CONFIGURACIÓN
# =========================

PINCH_THRESHOLD = 60


# =========================
# FUNCIONES
# =========================

def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    return distance


# =========================
# ABRIR CÁMARA
# =========================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo abrir la cámara.")
    exit()


# =========================
# CONFIGURAR MEDIAPIPE
# =========================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


# =========================
# LOOP PRINCIPAL
# =========================

while True:
    success, frame = cap.read()

    if not success:
        print("No se pudo leer el frame.")
        break

    # Voltear la imagen para que funcione como espejo
    frame = cv2.flip(frame, 1)

    # Obtener tamaño del frame
    height, width, _ = frame.shape

    # MediaPipe usa RGB, OpenCV usa BGR
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Procesar frame con MediaPipe
    result = hands.process(rgb_frame)

    # Si se detecta una mano
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:

            # Dibujar esqueleto completo de la mano
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Convertir landmarks normalizados a coordenadas en pixeles
            points = []

            for landmark in hand_landmarks.landmark:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                points.append((x, y))

            # Puntos importantes
            thumb_tip = points[4]   # Punta del pulgar
            index_tip = points[8]   # Punta del índice

            # Calcular centro aproximado de la palma
            palm_points = [0, 5, 9, 13, 17]

            center_x = sum(points[i][0] for i in palm_points) // len(palm_points)
            center_y = sum(points[i][1] for i in palm_points) // len(palm_points)

            hand_center = (center_x, center_y)

            # Calcular distancia entre pulgar e índice
            pinch_distance = calculate_distance(thumb_tip, index_tip)

            # Detectar gesto
            if pinch_distance < PINCH_THRESHOLD:
                gesture_mode = "CERRADO"
                mode_color = (0, 255, 0)
            else:
                gesture_mode = "ABIERTO"
                mode_color = (0, 0, 255)

            # Dibujar línea entre pulgar e índice
            cv2.line(frame, thumb_tip, index_tip, (255, 255, 255), 3)

            # Dibujar puntos importantes
            cv2.circle(frame, thumb_tip, 10, (255, 255, 255), -1)
            cv2.circle(frame, index_tip, 10, (255, 255, 255), -1)
            cv2.circle(frame, hand_center, 10, (255, 0, 0), -1)

            # Mostrar información en pantalla
            cv2.putText(
                frame,
                f"Distancia: {int(pinch_distance)}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Modo: {gesture_mode}",
                (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                mode_color,
                2
            )

            cv2.putText(
                frame,
                "Pulgar",
                (thumb_tip[0] + 10, thumb_tip[1]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "Indice",
                (index_tip[0] + 10, index_tip[1]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "Centro",
                (hand_center[0] + 10, hand_center[1]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2
            )

    # Mostrar ventana
    cv2.imshow("Hand Galaxy", frame)

    # Salir con Q
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break


# =========================
# CERRAR TODO
# =========================

cap.release()
cv2.destroyAllWindows()