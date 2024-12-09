from flask import Flask, render_template, request, jsonify
import os
import sqlite3
from face_recognition import load_image_file, face_encodings, compare_faces
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect('database/nid_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            nid INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT,
            image_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/apply', methods=['POST'])
def apply_nid():
    full_name = request.form['fullName']
    email = request.form['email']
    image = request.files['image']
    
    # Save uploaded image
    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)
    
    # Compare with existing images
    uploaded_image = load_image_file(image_path)
    uploaded_encoding = face_encodings(uploaded_image)[0]

    conn = sqlite3.connect('database/nid_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    for user in users:
        db_image_path = user[3]
        db_image = load_image_file(db_image_path)
        db_encoding = face_encodings(db_image)[0]
        match = compare_faces([db_encoding], uploaded_encoding)
        if match[0]:
            return jsonify({'message': 'Match found', 'nid': user[0], 'details': user})

    # If no match, insert new user
    cursor.execute('INSERT INTO users (full_name, email, image_path) VALUES (?, ?, ?)',
                   (full_name, email, image_path))
    conn.commit()
    new_nid = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'New user created', 'nid': new_nid})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
