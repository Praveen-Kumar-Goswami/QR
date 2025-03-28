from flask import Flask, request, render_template
import os
import qrcode
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import cv2
from PIL import Image
import cv2

app = Flask(__name__)

# Ensure the 'static' directory exists globally
STATIC_DIR = "static"
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)


# RSA Key Handling
def generate_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key


def save_keys(private_key, public_key):
    with open("private_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open("public_key.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))


def load_public_key():
    with open("public_key.pem", "rb") as f:
        return serialization.load_pem_public_key(f.read())


# Generate QR Code
def generate_qr(data, signature):
    qr_data = f"{data}|{signature.hex()}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    qr_path = os.path.join(STATIC_DIR, "signed_qr.png")
    img.save(qr_path)
    return qr_path


# Decode QR Code
def decode_qr(image_path):
    img = Image.open(image_path)
    img = np.array(img)  # Convert PIL Image to NumPy array
    qr_detector = cv2.QRCodeDetector()
    data, _, _ = qr_detector.detectAndDecode(img)  # Extract QR code data
    return data if data else None


# Verify Signature
def verify_signature(public_key, data, signature):
    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


# Flask Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    qr_path = None
    if request.method == 'POST':
        data = request.form['data']
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        save_keys(private_key, private_key.public_key())
        hashed_data = hashlib.sha256(data.encode()).digest()
        signature = private_key.sign(
            hashed_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        qr_path = generate_qr(data, signature)
    return render_template('index.html', qr_path=qr_path)


@app.route('/verify', methods=['POST'])
def verify():
    message = None
    if 'file' not in request.files:
        message = "No file uploaded"
        return render_template('index.html', qr_path=None, message=message)

    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, "uploaded_qr.png")
    file.save(file_path)

    qr_text = decode_qr(file_path)
    if not qr_text:
        message = "No QR code detected or invalid format"
        return render_template('index.html', qr_path=None, message=message)

    try:
        data, signature_hex = qr_text.split('|')
        hashed_data = hashlib.sha256(data.encode()).digest()
        signature = bytes.fromhex(signature_hex)
        public_key = load_public_key()

        if verify_signature(public_key, hashed_data, signature):
            message = "QR Code Verified: Authentic"
        else:
            message = "QR Code Verification Failed: Possible Tampering Detected"
    except Exception as e:
        message = f"Error in processing: {str(e)}"

    return render_template('index.html', qr_path=None, message=message)


# Main
if __name__ == '__main__':
    private_key, public_key = generate_keys()
    save_keys(private_key, public_key)
    app.run(debug=True)
