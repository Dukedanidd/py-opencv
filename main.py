import cv2
import mediapipe as mp
import math
import numpy as np
import time
from collections import deque


# =========================
# CONFIGURACIÓN
# =========================

CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540

PINCH_THRESHOLD = 60

MAX_TRAIL_POINTS = 45
TRAIL_LIFETIME = 0.85

LINE_PARTICLES = 18
BACKGROUND_BRIGHTNESS = 0.68
VISUAL_INTENSITY = 1.25


# =========================
# FUNCIONES
# =========================

def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def midpoint(point1, point2):
    return (
        (point1[0] + point2[0]) // 2,
        (point1[1] + point2[1]) // 2
    )


def smooth_point(previous, current, factor=0.35):
    if previous is None:
        return current

    x = int(previous[0] * (1 - factor) + current[0] * factor)
    y = int(previous[1] * (1 - factor) + current[1] * factor)

    return (x, y)


def draw_soft_circle(canvas, center, radius, brightness):
    x, y = center
    color = (brightness, brightness, brightness)

    cv2.circle(canvas, (x, y), radius + 8, (40, 40, 40), -1)
    cv2.circle(canvas, (x, y), radius + 4, (120, 120, 120), -1)
    cv2.circle(canvas, (x, y), radius, color, -1)


def draw_trail(canvas, trail_points):
    now = time.time()

    valid_points = []

    for point, timestamp in trail_points:
        age = now - timestamp

        if age <= TRAIL_LIFETIME:
            alpha = 1 - (age / TRAIL_LIFETIME)
            valid_points.append((point, alpha))

    if len(valid_points) < 2:
        return

    # Dibujar líneas entre puntos consecutivos, pero con grosor/brillo según edad
    for i in range(1, len(valid_points)):
        p1, a1 = valid_points[i - 1]
        p2, a2 = valid_points[i]

        alpha = min(a1, a2)

        thickness_outer = max(1, int(18 * alpha))
        thickness_mid = max(1, int(9 * alpha))
        thickness_core = max(1, int(3 * alpha))

        b_outer = int(50 * alpha)
        b_mid = int(140 * alpha)
        b_core = int(255 * alpha)

        cv2.line(canvas, p1, p2, (b_outer, b_outer, b_outer), thickness_outer)
        cv2.line(canvas, p1, p2, (b_mid, b_mid, b_mid), thickness_mid)
        cv2.line(canvas, p1, p2, (b_core, b_core, b_core), thickness_core)

    # Partículas alrededor del trazo, no en una línea perfecta
    for point, alpha in valid_points[::2]:
        x, y = point

        for _ in range(2):
            px = x + np.random.randint(-14, 15)
            py = y + np.random.randint(-14, 15)

            radius = np.random.randint(1, 4)
            brightness = int(np.random.randint(150, 256) * alpha)

            cv2.circle(canvas, (px, py), radius, (brightness, brightness, brightness), -1)


def draw_current_marker(canvas, point):
    draw_soft_circle(canvas, point, 5, 255)

    for _ in range(LINE_PARTICLES):
        px = point[0] + np.random.randint(-22, 23)
        py = point[1] + np.random.randint(-22, 23)

        radius = np.random.randint(1, 4)
        brightness = np.random.randint(160, 256)

        cv2.circle(canvas, (px, py), radius, (brightness, brightness, brightness), -1)


def remove_old_points(trail_points):
    now = time.time()

    while trail_points and now - trail_points[0][1] > TRAIL_LIFETIME:
        trail_points.popleft()


# =========================
# CÁMARA
# =========================

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

if not cap.isOpened():
    print("No se pudo abrir la cámara.")
    exit()


# =========================
# MEDIAPIPE
# =========================

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.65,
    min_tracking_confidence=0.65
)


# =========================
# ESTADO
# =========================

trail_points = deque(maxlen=MAX_TRAIL_POINTS)
last_draw_point = None


# =========================
# LOOP PRINCIPAL
# =========================

while True:
    success, frame = cap.read()

    if not success:
        print("No se pudo leer el frame.")
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))

    height, width, _ = frame.shape

    canvas = np.zeros((height, width, 3), dtype=np.uint8)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    gesture_mode = "SIN MANO"
    pinch_distance = 0

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]

        points = []

        for landmark in hand_landmarks.landmark:
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            points.append((x, y))

        thumb_tip = points[4]
        index_tip = points[8]

        raw_draw_point = midpoint(thumb_tip, index_tip)
        draw_point = smooth_point(last_draw_point, raw_draw_point, factor=0.45)
        last_draw_point = draw_point

        pinch_distance = calculate_distance(thumb_tip, index_tip)

        if pinch_distance < PINCH_THRESHOLD:
            gesture_mode = "CERRADO"

            trail_points.append((draw_point, time.time()))

            draw_trail(canvas, trail_points)
            draw_current_marker(canvas, draw_point)

        else:
            gesture_mode = "ABIERTO"

            remove_old_points(trail_points)
            draw_trail(canvas, trail_points)

            cv2.circle(canvas, thumb_tip, 6, (220, 220, 220), -1)
            cv2.circle(canvas, index_tip, 6, (220, 220, 220), -1)
            cv2.line(canvas, thumb_tip, index_tip, (90, 90, 90), 1)

    else:
        remove_old_points(trail_points)
        draw_trail(canvas, trail_points)
        last_draw_point = None

    cv2.putText(
        canvas,
        f"Modo: {gesture_mode}",
        (25, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        canvas,
        f"Distancia: {int(pinch_distance)}",
        (25, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (220, 220, 220),
        2
    )

    # Glow más barato que antes
    glow = cv2.GaussianBlur(canvas, (0, 0), 6)

    visual_layer = cv2.addWeighted(
        canvas,
        1.0,
        glow,
        0.65,
        0
    )

    dark_frame = cv2.addWeighted(
        frame,
        BACKGROUND_BRIGHTNESS,
        np.zeros_like(frame),
        1 - BACKGROUND_BRIGHTNESS,
        0
    )

    final_output = cv2.addWeighted(
        dark_frame,
        1.0,
        visual_layer,
        VISUAL_INTENSITY,
        0
    )

    cv2.imshow("Hand Galaxy", final_output)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()