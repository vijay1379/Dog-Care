from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from pymongo import MongoClient
from gridfs import GridFS
from bson.objectid import ObjectId
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# MongoDB setup
client = MongoClient('mongodb+srv://capcrypto621311:BPtR7SjMuSWjg6zv@dogdb.pls9o.mongodb.net/?retryWrites=true&w=majority&appName=dogDB')
db = client.dogdb
dogs = db.dogs
fs = GridFS(db)  # GridFS for storing images

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':  # Simple hardcoded check
            user = User(username)
            login_user(user)
            return redirect(url_for('upload'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Collect form data
        name = request.form['name']
        breed = request.form['breed']
        age = request.form['age']
        gender = request.form['gender']
        territory = request.form['territory']
        health = request.form['health']
        vaccination = request.form['vaccination']
        abc = request.form['abc']
        owner = request.form['owner']
        address = request.form['address']
        contact = request.form['contact']
        email = request.form['email']
        description = request.form['description']

        # Collect images
        profile_image = request.files['profile']
        pic1 = request.files['pic1']
        pic2 = request.files['pic2']
        pic3 = request.files['pic3']

        # Store images in MongoDB using GridFS
        profile_image_id = fs.put(profile_image, filename=profile_image.filename)
        pic1_id = fs.put(pic1, filename=pic1.filename)
        pic2_id = fs.put(pic2, filename=pic2.filename)
        pic3_id = fs.put(pic3, filename=pic3.filename)

        # Save dog details in MongoDB
        dog_data = {
            'name': name,
            'breed': breed,
            'age': age,
            'gender': gender,
            'territory': territory,
            'health': health,
            'vaccination': vaccination,
            'abc': abc,
            'owner': owner,
            'address': address,
            'contact': contact,
            'email': email,
            'description': description,
            'profile_image_id': profile_image_id,
            'pic1_id': pic1_id,
            'pic2_id': pic2_id,
            'pic3_id': pic3_id
        }
        dog_id = dogs.insert_one(dog_data).inserted_id
        print(f"Dog inserted with ID: {dog_id}")  # Debugging

        # Generate QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"https://dogcare-chi.vercel.app/dog/{dog_id}")  # For local development
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # Save QR code to a BytesIO object for download
        qr_buffer = BytesIO()
        img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        # Return the QR code as a downloadable file
        return send_file(
            qr_buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f"{name}_qr_code.png"
        )
    return render_template('upload.html')

@app.route('/dog/<dog_id>')
def dog_details(dog_id):
    try:
        dog = dogs.find_one({'_id': ObjectId(dog_id)})  # Convert string to ObjectId
        if dog:
            profile_image_url = f"/image/{dog['profile_image_id']}"
            pic1_url = f"/image/{dog['pic1_id']}"
            pic2_url = f"/image/{dog['pic2_id']}"
            pic3_url = f"/image/{dog['pic3_id']}"
            return render_template(
                'dog_details.html',
                dog=dog,
                profile_image_url=profile_image_url,
                pic1_url=pic1_url,
                pic2_url=pic2_url,
                pic3_url=pic3_url
            )
        return "Dog not found", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/image/<image_id>')
def get_image(image_id):
    image = fs.get(ObjectId(image_id))
    return send_file(BytesIO(image.read()), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=True)
