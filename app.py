from flask import Flask, request, jsonify, render_template
import torch
import cv2
import numpy as np
import time
import base64
import os
from dotenv import load_dotenv
from whatsapp_alert import send_whatsapp_alert
from google_drive_upload import upload_to_drive

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', trust_repo=True)
model.eval()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    data = request.get_json()

    whatsapp_number = data.get('whatsapp')
    drive_folder_id = data.get('drive')
    image_data = data.get('image')

    try:
        # Decode base64 image data
        image_data = image_data.split(",")[1]
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Run detection
        results = model(img)
        labels = results.pandas().xyxy[0]['name'].tolist()

        if 'person' in labels:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            image_path = f"media/detected_{timestamp}.jpg"
            cv2.imwrite(image_path, img)

            print(f"[INFO] Person detected. Saved image: {image_path}")

            try:
                # Upload to Google Drive
                upload_to_drive(image_path, drive_folder_id)

                # Send simple WhatsApp alert
                message = (
                    "🚨 Person detected!\n"
                    "📁 Picture uploaded to Drive. View it in your folder."
                )
                send_whatsapp_alert(message, whatsapp_number)

                print(f"[INFO] Alert sent to {whatsapp_number}")

                return jsonify({
                    'person_detected': True,
                    'message': message
                })

            except Exception as upload_err:
                print(f"[UPLOAD/WHATSAPP ERROR]: {upload_err}")
                return jsonify({
                    'person_detected': True,
                    'error': str(upload_err)
                })

        else:
            print("[INFO] No person detected.")
            return jsonify({'person_detected': False})

    except Exception as e:
        print(f"[DETECTION ERROR]: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('media'):
        os.makedirs('media')
    app.run(debug=True)
