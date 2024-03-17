import cv2
import numpy as np
from sklearn import svm
import os
import time
from flask import Flask, render_template, Response, jsonify
import pygame
import sys
import threading
import joblib

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

app = Flask(__name__)

eye_open_dir = r'Open'
eye_closed_dir = r'Closed'

clf = svm.SVC(C=0.2, kernel='poly')

def flip_horizontal(image):
    return cv2.flip(image, 1)

X_eye_open, y_eye_open = [], []
for filename in os.listdir(eye_open_dir):
    img = cv2.imread(os.path.join(eye_open_dir, filename), cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (80, 80))
    img_1d = img.flatten() / 255
    X_eye_open.append(img_1d)
    y_eye_open.append(1)

X_eye_closed, y_eye_closed = [], []
for filename in os.listdir(eye_closed_dir):
    img = cv2.imread(os.path.join(eye_closed_dir, filename), cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (80, 80))
    img_1d = img.flatten() / 255
    X_eye_closed.append(img_1d)
    y_eye_closed.append(0)

X = np.array(X_eye_open + X_eye_closed)
y = np.array(y_eye_open + y_eye_closed)
clf.fit(X, y)

# Save the model
joblib.dump(clf, 'svm_model2.plk')

cap = cv2.VideoCapture(0)

eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

eye_status = "Unknown"
eye_open_count = 0
eye_closed_count = 0
last_notification_time = 0
alarm_thread = None  # Biến luồng âm thanh
monitoring = False  # Biến kiểm soát việc theo dõi
alarm_playing = False  # Biến kiểm soát trạng thái âm thanh cảnh báo

pygame.mixer.init()
# Load the alarm sound
alarm_sound = pygame.mixer.Sound(r'D:\phat_hien_buon_ngu\templates\alarm.mp3')

def play_alarm_sound():
    global alarm_playing, eye_status
    while True:
        if eye_status == "WARNING!!" and not alarm_playing:
            alarm_playing = True
            alarm_sound.play()  # Play the alarm sound

def stop_alarm_sound():
    global alarm_playing
    alarm_playing = False

def set_web_eye_status_warning():
    global eye_status
    eye_status = "WARNING!!"
    return "Web eye status set to WARNING!!", 200

def set_web_eye_status_normal():
    global eye_status
    eye_status = "Normal"
    return "Web eye status set to Normal", 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_eye_monitoring', methods=['GET'])
def start_eye_monitoring():
    global monitoring, eye_status, alarm_thread, alarm_playing, eye_open_count, eye_closed_count
    monitoring = True
    eye_status = "Unknown"
    eye_open_count = 0
    eye_closed_count = 0
    if alarm_thread is None or not alarm_thread.is_alive():
        alarm_thread = threading.Thread(target=play_alarm_sound)
        alarm_thread.start()
    alarm_playing = False
    return "Eye monitoring started", 200

@app.route('/stop_eye_monitoring', methods=['GET'])
def stop_eye_monitoring():
    global monitoring, eye_status, alarm_thread, alarm_playing
    monitoring = False
    eye_status = "Unknown"
    alarm_playing = False
    return "Eye monitoring stopped", 200

@app.route('/set_web_eye_status_warning', methods=['GET'])
def set_web_eye_status_warning_route():
    return set_web_eye_status_warning()

@app.route('/set_web_eye_status_normal', methods=['GET'])
def set_web_eye_status_normal_route():
    return set_web_eye_status_normal()

def gen():
    global eye_status, eye_open_count, eye_closed_count, last_notification_time, monitoring, alarm_playing
    close_time=0
    while True:
        if monitoring:
            ret, frame = cap.read()
            frame = flip_horizontal(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            upper_half_gray = gray[:int(frame.shape[0] / 2), :]
            eyes = eye_cascade.detectMultiScale(upper_half_gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))

            if len(eyes) == 0:
                close_time += 1
                eye_closed_count += 1
                if eye_closed_count > eye_open_count:
                    if eye_status != "WARNING!!":
                        eye_status = "WARNING!!"
                        if not alarm_playing:
                            alarm_playing = True
                            alarm_sound.play()  # Play the alarm sound
                else:
                    eye_status = "Normal"
            else:
                close_time = 0
                eye_open_count += 1
                eye_status = "Normal"

            current_time = time.time()
            if current_time - last_notification_time >= 3:
                print(f"{current_time} - Mắt mở: {eye_open_count}, Mắt nhắm: {eye_closed_count}, Status: {eye_status}")
                last_notification_time = current_time
                eye_open_count = 0
                eye_closed_count = 0

            for (x, y, w, h) in eyes:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            frame = cv2.imencode('.jpg', frame)[1].tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')           

 
            # if eye_open_count % 3 == 0:  
            #     for (x, y, w, h) in eyes:
            #             eye_region = upper_half_gray[y:y + h, x:x + w]
            #             img_1d = cv2.resize(eye_region, (80, 80)).flatten() / 255
            #             prediction = clf.predict(np.array([img_1d]).reshape(1, -1))

            #             if prediction == 1:
            #                 status = "open"
            #             else:
            #                 status = "closed"
            #             cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            #             cv2.putText(frame, f"{status}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            #     if eye_closed_count > eye_open_count:
            #         eye_status = "WARNING!!"
            #         if not alarm_playing:
            #             alarm_playing = True
            #             alarm_sound.play()  
            #     frame = cv2.imencode('.jpg', frame)[1].tobytes()
            #     yield (b'--frame\r\n'
            #           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  


@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_eye_status')
def get_eye_status():
    global eye_status, alarm_playing
    return jsonify({'status': eye_status, 'is_warning': alarm_playing})

if __name__ == "__main__":
    app.run(debug=True)