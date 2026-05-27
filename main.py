import cv2
import mediapipe as mp
import math
import numpy as np
import time
import random
from collections import deque


# =========================
# CONFIGURACIÓN GENERAL
# =========================

CAMERA_WIDTH = 800
CAMERA_HEIGHT = 450

PINCH_THRESHOLD = 60

BACKGROUND_BRIGHTNESS = 0.72
VISUAL_INTENSITY = 1.15


# =========================
# CONFIGURACIÓN TRAIL / MARCADOR
# =========================

MAX_TRAIL_POINTS = 40
TRAIL_LIFETIME = 0.75
LINE_PARTICLES = 14


# =========================
# CONFIGURACIÓN GALAXIA 3D OPTIMIZADA
# =========================

MAX_GALAXY_PARTICLES = 190
GALAXY_SPAWN_RATE = 6
GALAXY_LIFETIME = 2.4

GALAXY_RADIUS = 185
FOCAL_LENGTH = 420

GALAXY_CONNECTION_DISTANCE = 58
CONNECTION_SAMPLE_STEP = 3
MAX_CONNECTIONS_PER_FRAME = 160

ROTATION_SENSITIVITY = 0.005


# =========================
# FUNCIONES BÁSICAS
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


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


# =========================
# TRAIL / MARCADOR
# =========================

def draw_soft_circle(canvas, center, radius, brightness):
    x, y = center

    cv2.circle(canvas, (x, y), radius + 7, (35, 35, 35), -1)
    cv2.circle(canvas, (x, y), radius + 3, (120, 120, 120), -1)
    cv2.circle(canvas, (x, y), radius, (brightness, brightness, brightness), -1)


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

    for i in range(1, len(valid_points)):
        p1, a1 = valid_points[i - 1]
        p2, a2 = valid_points[i]

        alpha = min(a1, a2)

        thickness_outer = max(1, int(14 * alpha))
        thickness_mid = max(1, int(7 * alpha))
        thickness_core = max(1, int(2 * alpha))

        b_outer = int(45 * alpha)
        b_mid = int(135 * alpha)
        b_core = int(255 * alpha)

        cv2.line(canvas, p1, p2, (b_outer, b_outer, b_outer), thickness_outer)
        cv2.line(canvas, p1, p2, (b_mid, b_mid, b_mid), thickness_mid)
        cv2.line(canvas, p1, p2, (b_core, b_core, b_core), thickness_core)

    for point, alpha in valid_points[::2]:
        x, y = point

        for _ in range(1):
            px = x + np.random.randint(-12, 13)
            py = y + np.random.randint(-12, 13)

            radius = np.random.randint(1, 3)
            brightness = int(np.random.randint(160, 256) * alpha)

            cv2.circle(canvas, (px, py), radius, (brightness, brightness, brightness), -1)


def draw_current_marker(canvas, point):
    draw_soft_circle(canvas, point, 5, 255)

    for _ in range(LINE_PARTICLES):
        px = point[0] + np.random.randint(-18, 19)
        py = point[1] + np.random.randint(-18, 19)

        radius = np.random.randint(1, 3)
        brightness = np.random.randint(170, 256)

        cv2.circle(canvas, (px, py), radius, (brightness, brightness, brightness), -1)


def remove_old_points(trail_points):
    now = time.time()

    while trail_points and now - trail_points[0][1] > TRAIL_LIFETIME:
        trail_points.popleft()


# =========================
# GALAXIA 3D
# =========================

class GalaxyParticle3D:
    def __init__(self, spread):
        # Esfera más uniforme y redonda.
        # Esta técnica evita que se formen esquinas o grupos raros.
        u = random.uniform(-1, 1)
        theta = random.uniform(0, 2 * math.pi)

        sphere_radius = GALAXY_RADIUS * (random.random() ** (1 / 3)) * spread

        circle = math.sqrt(1 - u * u)

        self.x = sphere_radius * circle * math.cos(theta)
        self.y = sphere_radius * circle * math.sin(theta)
        self.z = sphere_radius * u

        # Movimiento suave, más orbital que explosivo.
        tangent_angle = theta + math.pi / 2
        speed = random.uniform(0.08, 0.55) * spread

        self.vx = math.cos(tangent_angle) * speed
        self.vy = math.sin(tangent_angle) * speed
        self.vz = random.uniform(-0.25, 0.25) * speed

        self.created_at = time.time()
        self.life_time = random.uniform(1.5, GALAXY_LIFETIME)

        self.size = random.randint(1, 3)
        self.orbit_speed = random.uniform(-0.012, 0.012)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        self.vx *= 0.99
        self.vy *= 0.99
        self.vz *= 0.99

        cos_a = math.cos(self.orbit_speed)
        sin_a = math.sin(self.orbit_speed)

        new_x = self.x * cos_a - self.z * sin_a
        new_z = self.x * sin_a + self.z * cos_a

        self.x = new_x
        self.z = new_z

    def alpha(self):
        age = time.time() - self.created_at
        return max(0, 1 - age / self.life_time)

    def is_alive(self):
        return self.alpha() > 0


def rotate_3d(x, y, z, angle_x, angle_y):
    cos_x = math.cos(angle_x)
    sin_x = math.sin(angle_x)

    y2 = y * cos_x - z * sin_x
    z2 = y * sin_x + z * cos_x

    cos_y = math.cos(angle_y)
    sin_y = math.sin(angle_y)

    x3 = x * cos_y + z2 * sin_y
    z3 = -x * sin_y + z2 * cos_y

    return x3, y2, z3


def project_3d_to_2d(x, y, z, center):
    z_shifted = z + FOCAL_LENGTH + 260

    if z_shifted < 100:
        z_shifted = 100

    scale = FOCAL_LENGTH / z_shifted

    screen_x = int(center[0] + x * scale)
    screen_y = int(center[1] + y * scale)

    return screen_x, screen_y, scale


def spawn_galaxy_particles_3d(particles, pinch_distance):
    if len(particles) >= MAX_GALAXY_PARTICLES:
        return

    spread = np.interp(
        pinch_distance,
        [PINCH_THRESHOLD, 230],
        [0.75, 1.65]
    )

    spread = clamp(spread, 0.75, 1.65)

    for _ in range(GALAXY_SPAWN_RATE):
        if len(particles) < MAX_GALAXY_PARTICLES:
            particles.append(GalaxyParticle3D(spread))


def draw_galaxy_halo(canvas, center, particle_count):
    if particle_count <= 0:
        return

    strength = clamp(particle_count / MAX_GALAXY_PARTICLES, 0.0, 1.0)

    radius_1 = int(GALAXY_RADIUS * 0.65)
    radius_2 = int(GALAXY_RADIUS * 0.42)

    brightness_1 = int(18 * strength)
    brightness_2 = int(28 * strength)

    cv2.circle(canvas, center, radius_1, (brightness_1, brightness_1, brightness_1), 1)
    cv2.circle(canvas, center, radius_2, (brightness_2, brightness_2, brightness_2), 1)


def draw_galaxy_3d(canvas, particles, center, angle_x, angle_y):
    for particle in particles:
        particle.update()

    particles[:] = [p for p in particles if p.is_alive()]

    projected_points = []

    for particle in particles:
        rx, ry, rz = rotate_3d(
            particle.x,
            particle.y,
            particle.z,
            angle_x,
            angle_y
        )

        sx, sy, scale = project_3d_to_2d(rx, ry, rz, center)

        # Si queda muy fuera de pantalla, no lo dibujamos.
        if sx < -80 or sx > CAMERA_WIDTH + 80 or sy < -80 or sy > CAMERA_HEIGHT + 80:
            continue

        alpha = particle.alpha()

        depth_boost = clamp(scale, 0.35, 1.5)
        brightness = int(235 * alpha * depth_boost)
        brightness = clamp(brightness, 0, 255)

        size = int(particle.size * depth_boost)
        size = clamp(size, 1, 5)

        projected_points.append({
            "x": sx,
            "y": sy,
            "scale": scale,
            "alpha": alpha,
            "brightness": brightness,
            "size": size
        })

    draw_galaxy_halo(canvas, center, len(projected_points))

    # Conexiones optimizadas.
    # No compara todos contra todos.
    connections = 0
    sampled_points = projected_points[::CONNECTION_SAMPLE_STEP]

    for i in range(len(sampled_points)):
        if connections >= MAX_CONNECTIONS_PER_FRAME:
            break

        p1 = sampled_points[i]

        # Solo revisamos algunos vecinos siguientes.
        for j in range(i + 1, min(i + 14, len(sampled_points))):
            if connections >= MAX_CONNECTIONS_PER_FRAME:
                break

            p2 = sampled_points[j]

            dx = p1["x"] - p2["x"]
            dy = p1["y"] - p2["y"]

            d2 = dx * dx + dy * dy
            max_d2 = GALAXY_CONNECTION_DISTANCE * GALAXY_CONNECTION_DISTANCE

            if d2 < max_d2:
                d = math.sqrt(d2)
                alpha = min(p1["alpha"], p2["alpha"])
                depth_avg = (p1["scale"] + p2["scale"]) / 2

                intensity = int(
                    115 * alpha * depth_avg * (1 - d / GALAXY_CONNECTION_DISTANCE)
                )
                intensity = clamp(intensity, 0, 155)

                cv2.line(
                    canvas,
                    (p1["x"], p1["y"]),
                    (p2["x"], p2["y"]),
                    (intensity, intensity, intensity),
                    1
                )

                connections += 1

    # Nodos. Esto sí dibuja casi todos, porque es barato.
    for p in projected_points:
        cv2.circle(
            canvas,
            (p["x"], p["y"]),
            p["size"],
            (p["brightness"], p["brightness"], p["brightness"]),
            -1
        )

        if p["scale"] > 0.85 and p["alpha"] > 0.4:
            halo = int(p["brightness"] * 0.25)

            cv2.circle(
                canvas,
                (p["x"], p["y"]),
                p["size"] + 3,
                (halo, halo, halo),
                -1
            )


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

galaxy_particles = []

galaxy_center = None
last_hand_point = None

angle_x = 0.0
angle_y = 0.0

fps_last_time = time.time()
fps_counter = 0
fps_value = 0


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
        draw_point = smooth_point(last_draw_point, raw_draw_point, factor=0.4)
        last_draw_point = draw_point

        pinch_distance = calculate_distance(thumb_tip, index_tip)

        if galaxy_center is None:
            galaxy_center = draw_point
        else:
            galaxy_center = smooth_point(galaxy_center, draw_point, factor=0.12)

        if last_hand_point is not None:
            dx = draw_point[0] - last_hand_point[0]
            dy = draw_point[1] - last_hand_point[1]

            angle_y += dx * ROTATION_SENSITIVITY
            angle_x += dy * ROTATION_SENSITIVITY

        last_hand_point = draw_point

        if pinch_distance < PINCH_THRESHOLD:
            gesture_mode = "CERRADO"

            trail_points.append((draw_point, time.time()))

            draw_trail(canvas, trail_points)
            draw_current_marker(canvas, draw_point)

        else:
            gesture_mode = "GALAXIA 3D"

            remove_old_points(trail_points)
            draw_trail(canvas, trail_points)

            spawn_galaxy_particles_3d(
                galaxy_particles,
                pinch_distance
            )

            cv2.circle(canvas, thumb_tip, 5, (220, 220, 220), -1)
            cv2.circle(canvas, index_tip, 5, (220, 220, 220), -1)
            cv2.line(canvas, thumb_tip, index_tip, (90, 90, 90), 1)

    else:
        remove_old_points(trail_points)
        draw_trail(canvas, trail_points)
        last_draw_point = None
        last_hand_point = None

    if galaxy_center is None:
        galaxy_center = (width // 2, height // 2)

    draw_galaxy_3d(
        canvas,
        galaxy_particles,
        galaxy_center,
        angle_x,
        angle_y
    )

    # FPS simple
    fps_counter += 1
    now = time.time()

    if now - fps_last_time >= 1:
        fps_value = fps_counter
        fps_counter = 0
        fps_last_time = now

    cv2.putText(
        canvas,
        f"Modo: {gesture_mode}",
        (25, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        (255, 255, 255),
        2
    )

    cv2.putText(
        canvas,
        f"Particulas: {len(galaxy_particles)} | FPS: {fps_value}",
        (25, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        (210, 210, 210),
        2
    )

    # Glow más ligero
    glow = cv2.GaussianBlur(canvas, (0, 0), 4)

    visual_layer = cv2.addWeighted(
        canvas,
        1.0,
        glow,
        0.45,
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