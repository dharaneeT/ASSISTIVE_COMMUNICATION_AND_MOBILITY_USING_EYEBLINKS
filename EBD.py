import cv2
import mediapipe as mp
import numpy as np
import time
from collections import deque
import socket

# ================== UDP SETUP ==================
ESP32_IP = "10.173.204.147"
ESP32_PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_command(cmd):
    """
    Send a single-character command to ESP32 via UDP.
    cmd: 'F' (forward), 'B' (backward), 'S' (stop)
    """
    try:
        sock.sendto(cmd.encode(), (ESP32_IP, ESP32_PORT))
        print(f"Sent {cmd}")
    except Exception as e:
        print(f"Error sending {cmd}: {e}")

# ================== EYE AND MORSE SETUP ==================
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]

MORSE_CODE_DICT = {
    '.-':'A','-...':'B','-.-.':'C','-..':'D','.':'E','..-.':'F',
    '--.':'G','....':'H','..':'I','.---':'J','-.-':'K','.-..':'L',
    '--':'M','-.':'N','---':'O','.--.':'P','--.-':'Q','.-.':'R',
    '...':'S','-':'T','..-':'U','...-':'V','.--':'W','-..-':'X',
    '-.--':'Y','--..':'Z','-----':'0','.----':'1','..---':'2',
    '...--':'3','....-':'4','.....':'5','-....':'6','--...':'7',
    '---..':'8','----.':'9'
}

MIN_BLINK_DURATION = 0.15
BLINK_COOLDOWN = 0.2
RESET_TIME = 3.0

morse_input = ''
typed_word = ''
blink_counter = 0
last_blink_detected_time = 0

eye_closed_start = None
last_blink_time = 0
ear_history = deque(maxlen=5)

BASELINE_FRAMES = 30
baseline_ear_values = []
EAR_CLOSE_THRESH = 0.21
EAR_OPEN_THRESH = 0.24

mode = 'MORSE'

# ================== MEDIAPIPE SETUP ==================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

cap = cv2.VideoCapture(0)

def calculate_EAR(eye):
    v1 = np.linalg.norm(eye[1] - eye[5])
    v2 = np.linalg.norm(eye[2] - eye[4])
    h = np.linalg.norm(eye[0] - eye[3])
    return (v1 + v2) / (2.0 * h)

def decode_morse(morse):
    return MORSE_CODE_DICT.get(morse.strip(), '?')

print("Calibrating... please keep your eyes open for a moment.")

# ================== MAIN LOOP ==================
last_command = None  # To prevent sending same command repeatedly

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    current_time = time.time()

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0]
        mesh_points = np.array([(lm.x * w, lm.y * h) for lm in landmarks.landmark])

        left_eye = mesh_points[LEFT_EYE_IDX]
        right_eye = mesh_points[RIGHT_EYE_IDX]
        left_ear = calculate_EAR(left_eye)
        right_ear = calculate_EAR(right_eye)
        avg_ear = (left_ear + right_ear) / 2

        ear_history.append(avg_ear)
        smooth_ear = np.mean(ear_history)

        for pt in np.concatenate([left_eye, right_eye]):
            cv2.circle(frame, tuple(pt.astype(int)), 1, (0, 255, 0), -1)

        # Calibration phase
        if len(baseline_ear_values) < BASELINE_FRAMES:
            baseline_ear_values.append(smooth_ear)
            EAR_CLOSE_THRESH = np.mean(baseline_ear_values) * 0.75
            EAR_OPEN_THRESH = EAR_CLOSE_THRESH + 0.03
        else:
            # Blink detection with hysteresis
            if smooth_ear < EAR_CLOSE_THRESH:
                if eye_closed_start is None:
                    eye_closed_start = current_time
            elif smooth_ear > EAR_OPEN_THRESH:
                if eye_closed_start is not None:
                    closed_time = current_time - eye_closed_start
                    if closed_time >= MIN_BLINK_DURATION and (current_time - last_blink_time) > BLINK_COOLDOWN:
                        blink_counter += 1
                        last_blink_detected_time = current_time
                        last_blink_time = current_time
                    eye_closed_start = None

        # Process actions after pause
        if blink_counter > 0 and (current_time - last_blink_detected_time) > RESET_TIME:
            command_to_send = None
            if mode == 'MORSE':
                if blink_counter == 2:
                    morse_input += '.'
                elif blink_counter == 3:
                    morse_input += '-'
                elif blink_counter == 4:
                    typed_word += decode_morse(morse_input)
                    morse_input = ''
                elif blink_counter == 5:
                    mode = 'CONTROL'
                    print("Switched to CONTROL MODE")
            elif mode == 'CONTROL':
                if blink_counter == 2:
                    print("STOP")
                    command_to_send = 'S'
                elif blink_counter == 3:
                    print("FORWARD")
                    command_to_send = 'F'
                elif blink_counter == 4:
                    print("BACKWARD")
                    command_to_send = 'B'
                elif blink_counter == 5:
                    mode = 'MORSE'
                    print("Switched to MORSE MODE")

            # Send command only if different from last
            if command_to_send and command_to_send != last_command:
                send_command(command_to_send)
                last_command = command_to_send

            blink_counter = 0

        # Display info
        cv2.putText(frame, f'MODE: {mode}', (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f'Morse Input: {morse_input}', (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f'Typed Word: {typed_word}', (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f'Blinks: {blink_counter}', (20, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 2)

    else:
        eye_closed_start = None

    cv2.imshow("Blink Morse & Control Interface", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()