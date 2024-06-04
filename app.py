from flask import Flask, request, render_template, send_from_directory
from stegano import lsb
import os
import threading
import time
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config['FOLDER_PLIKOW'] = 'uploads'

# Generowanie losowego klucza szyfrowania
encryption_key = Fernet.generate_key()

if not os.path.exists(app.config['FOLDER_PLIKOW']):
    os.makedirs(app.config['FOLDER_PLIKOW'])

def wyczysc_folder_uploads():
    for filename in os.listdir(app.config['FOLDER_PLIKOW']):
        file_path = os.path.join(app.config['FOLDER_PLIKOW'], filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

def opoznione_wyczysc_folder_uploads(delay):
    time.sleep(delay)
    wyczysc_folder_uploads()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hide', methods=['POST'])
def ukryj_wiadomosc():
    if 'image' not in request.files or 'message' not in request.form:
        return render_template('result.html', message='Uzupelnij formularz!')
    
    image = request.files['image']
    message = request.form['message']
    password = request.form.get('password')  # Pobierz hasło
    
    if image.filename == '':
        return render_template('result.html', message='Nie wybrano pliku')

    if not image.filename.lower().endswith('.png'):
        return render_template('result.html', message='Błędny format pliku, wybierz plik .PNG')
    
    if password:
        cipher = Fernet(encryption_key)
        message = cipher.encrypt(message.encode()).decode()

    image_path = os.path.join(app.config['FOLDER_PLIKOW'], image.filename)
    image.save(image_path)
    
    output_image_path = os.path.join(app.config['FOLDER_PLIKOW'], 'ciekawy_obrazek_' + image.filename)
    secret = lsb.hide(image_path, message)
    secret.save(output_image_path)
    
    # Opróżnianie katalogu uploads po 3 sekundach
    threading.Thread(target=opoznione_wyczysc_folder_uploads, args=(3,)).start()
    
    return send_from_directory(app.config['FOLDER_PLIKOW'], 'ciekawy_obrazek_' + image.filename, as_attachment=True)

@app.route('/reveal', methods=['POST'])
def ujawnij_wiadomosc():
    if 'image' not in request.files:
        return render_template('result.html', message='Plik nie jest obrazkiem')
    
    image = request.files['image']
    password = request.form.get('password')  # Pobierz hasło

    if image.filename == '':
        return render_template('result.html', message='Nie wybrano pliku')

    if not image.filename.lower().endswith('.png'):
        return render_template('result.html', message='Błędny format pliku, wybierz plik .PNG')

    image_path = os.path.join(app.config['FOLDER_PLIKOW'], image.filename)
    image.save(image_path)
    
    # Sprawdzenie, czy plik istnieje
    if not os.path.exists(image_path):
        return render_template('result.html', message='Plik nie istnieje')
    
    try:
        message = lsb.reveal(image_path)
        if message is None:
            return render_template('result.html', message='W pliku nie znaleziono ukrytej wiadomości')
        if password:
            cipher = Fernet(encryption_key)
            message = cipher.decrypt(message.encode()).decode()
    except IndexError:
        return render_template('result.html', message='W pliku nie znaleziono ukrytej wiadomości')
    
    # Opróżnianie katalogu uploads po ujawnieniu wiadomości
    wyczysc_folder_uploads()

    return render_template('result.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)

# Mirosław Sycz w65511 06.2024