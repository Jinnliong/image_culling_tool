import os
import io
import base64
import requests
import streamlit as st
from PIL import Image

def send_telegram_ping(message):
    try:
        # Securely fetch keys from Streamlit secrets
        bot_token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=8)
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def get_camera_settings(path):
    focal_length = "Unknown"
    aperture = "Unknown"
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif: return focal_length, aperture
            
            # 0x8769 is the ExifOffset IFD which contains standard camera settings
            exif_dict = exif.get_ifd(0x8769) if hasattr(exif, 'get_ifd') else exif
            
            # 37386 = FocalLength, 33437 = FNumber (Aperture)
            foc_val = exif_dict.get(37386) or exif.get(37386)
            ap_val = exif_dict.get(33437) or exif.get(33437)
            
            if foc_val:
                try:
                    f_len = foc_val[0] / foc_val[1] if isinstance(foc_val, tuple) else float(foc_val)
                    focal_length = f"{int(f_len)}mm"
                except: pass
                
            if ap_val:
                try:
                    f_num = ap_val[0] / ap_val[1] if isinstance(ap_val, tuple) else float(ap_val)
                    aperture = f"f/{f_num:.1f}"
                except: pass
                
    except Exception as e:
        pass
        
    return focal_length, aperture

def get_jpeg_files(folder_path):
    return sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg'))])

def encode_image(image_path, max_size=1080):
    try:
        # 1. Open the original image in Read-Only mode
        with Image.open(image_path) as img:
            
            # 2. The Smart Scout: Shrinks the clone to 1080px (if it's larger), keeps aspect ratio intact!
            img.thumbnail((max_size, max_size))
            
            # 3. Create a temporary "Memory Forge" in your RAM
            buffer = io.BytesIO()
            
            # 4. Save the resized clone into the buffer (Quality 85 keeps it sharp for the AI!)
            img.save(buffer, format="JPEG", quality=85)
            
            # 5. Convert to Base64 and send it to the brain
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None