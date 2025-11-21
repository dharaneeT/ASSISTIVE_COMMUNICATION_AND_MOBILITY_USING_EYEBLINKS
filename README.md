Blink-Based Morse Code & ESP32 Control System

This project enables hands-free communication and control using eye blinks detected through a webcam.
It supports two modes:

Morse Mode → Enter Morse code using blinks

Control Mode → Send Forward / Backward / Stop commands to an ESP32 over UDP

Blink detection uses MediaPipe FaceMesh and an adaptive EAR (Eye Aspect Ratio) system for robust performance.

✨ Features

Real-time blink detection using MediaPipe

Adaptive EAR calibration based on initial frames

Morse code input using blink patterns

Automatic Morse decoding into text

UDP-based robot control (ESP32)

Noise-proof blink classification (hysteresis + cooldown)

On-screen interface with live status and feedback

🖥️ Demo (Modes)
Morse Mode
Blink Count	Action
2 blinks	. (dot)
3 blinks	- (dash)
4 blinks	Decode Morse character
5 blinks	Switch to CONTROL mode
Control Mode
Blink Count	ESP32 Action
2 blinks	Stop (S)
3 blinks	Forward (F)
4 blinks	Backward (B)
5 blinks	Switch to MORSE mode
🔌 ESP32 UDP Configuration

The Python script sends commands to:

IP:   10.173.204.147
Port: 4210


Commands sent:

F → forward

B → backward

S → stop

Ensure ESP32 and the computer are on the same Wi-Fi network.

📦 Installation
1. Clone the repository
git clone https://github.com/yourname/blink-morse-esp32.git
cd blink-morse-esp32

2. Install dependencies
pip install opencv-python mediapipe numpy

▶️ Run the Application
python main.py


Press Q anytime to quit.

🧠 How It Works
Eye Aspect Ratio (EAR)

EAR is calculated from 6 face mesh eye landmarks.

Lower EAR → eye closed

Higher EAR → eye open

Calibration

For the first 30 frames, the system:

Captures natural EAR values

Automatically computes EAR_OPEN and EAR_CLOSE thresholds

Blink Detection

A blink is registered only when:

EAR < close threshold

Eye remains closed for ≥ MIN_BLINK_DURATION

Enough time since last blink (cooldown)

Action Trigger

If no new blink for 3 seconds, the blink count is processed into:

Morse symbol

ESP32 command

Mode switch

🖼️ UI Elements Displayed

Current mode (MORSE / CONTROL)

Live Morse sequence

Decoded text

Blink counter

Eye landmarks

EAR (smoothed)

🗂️ Project Structure
.
├── main.py              # Blink detection + Morse + ESP32 control logic
├── README.md            # This file
└── requirements.txt     # Optional dependency file

🚀 Future Improvements

Gaze-based cursor movement

Adjustable thresholds via UI

Word prediction / dictionary support

Cloud-based communication logs

🤝 Contributing

Pull requests are welcome!
If you find a bug or want a feature, feel free to open an issue.
