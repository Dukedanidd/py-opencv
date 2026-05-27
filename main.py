import cv2
import mediapipe as mp


# =========================
# 1. ABRIR CÁMARA
# =========================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo abrir la cámara.")
    exit()


# =========================
# 2. CONFIGURAR MEDIAPIPE
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
# 3. LOOP PRINCIPAL
# =========================

while True:
    success, frame = cap.read()

    if not success:
        print("No se pudo leer el frame.")
        break

    # Voltear imagen para que funcione como espejo
    frame = cv2.flip(frame, 1)

    # Obtener tamaño real del frame
    height, width, _ = frame.shape

    # MediaPipe necesita RGB, OpenCV usa BGR
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Procesar imagen con MediaPipe
    result = hands.process(rgb_frame)

    # Si detecta una mano
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:

            # Dibujar esqueleto completo de la mano
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Convertir landmarks normalizados a pixeles
            points = []

            for landmark in hand_landmarks.landmark:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                points.append((x, y))

            # Puntos importantes
            thumb_tip = points[4]   # punta del pulgar
            index_tip = points[8]   # punta del índice

            # Calcular centro aproximado de la palma
            palm_points = [0, 5, 9, 13, 17]

            center_x = sum(points[i][0] for i in palm_points) // len(palm_points)
            center_y = sum(points[i][1] for i in palm_points) // len(palm_points)

            hand_center = (center_x, center_y)

            # Dibujar puntos importantes
            cv2.circle(frame, thumb_tip, 10, (255, 255, 255), -1)
            cv2.circle(frame, index_tip, 10, (255, 255, 255), -1)
            cv2.circle(frame, hand_center, 10, (0, 0, 255), -1)

            # Texto para identificar
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
                (0, 0, 255),
                2
            )

    # Mostrar ventana
    cv2.imshow("Hand Galaxy", frame)

    # Salir con Q
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break


# =========================
# 4. CERRAR TODO
# =========================

cap.release()
cv2.destroyAllWindows()