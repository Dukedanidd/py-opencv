import cv2

# Aqui abro la camara
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo abrir la cámara.")
    exit()

# Aqui leo la imagen de la camara
while True:
    success, frame = cap.read()
    # Aqui volteo la imagen para que se vea como en mirror
    frame = cv2.flip(frame, 1)

    # Si no se pudo leer el frame, salgo del bucle
    if not success:
        print("No se pudo leer el frame.")
        break

    # Muestro la imagen en la ventana
    cv2.imshow("Hand Galaxy", frame)

    # Leo la tecla que se presiona
    key = cv2.waitKey(1) & 0xFF

    # Si la tecla es q, salgo del bucle
    if key == ord("q"):
        break

# Cierro la camara
cap.release()
cv2.destroyAllWindows()