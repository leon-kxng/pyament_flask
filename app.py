from flask import Flask, request, jsonify, send_file, abort
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, Payment, User, Image  # Import the Image model
from sqlalchemy.orm import sessionmaker
import os, io
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask_bcrypt import Bcrypt, generate_password_hash

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Allow credentials in CORS
migrate = Migrate(app, db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'  # SQLite database file
app.config['SECRET_KEY'] = 'acbf6c117f294c35b9fa6f2f2edc4d99'  # Change this to a secure secret key
db.init_app(app)
bcrypt = Bcrypt(app)  # Initialize Bcrypt

# JWT Token Required Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['id']).first()
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    # Extract user information from the request
    phone_number = data.get('phone_number')
    username = data.get('username')
    password = data.get('password')
    profile_pic_id = data.get('profile_pic_id')  # Get profile picture ID from request data

    # Validate phone number format
    if not phone_number or not (phone_number.startswith('01') or phone_number.startswith('07')) or len(phone_number) != 10:
        return jsonify({'message': 'Invalid phone number format'}), 400

    # Check if a user with the same phone number or username already exists
    existing_user_phone = User.query.filter_by(phone_number=phone_number).first()
    existing_user_username = User.query.filter_by(username=username).first()

    if existing_user_phone:
        return jsonify({'message': 'User with similar phone number already exists'}), 400

    if existing_user_username:
        return jsonify({'message': 'User with similar username already exists'}), 400

    # Check if the provided profile_pic_id exists in the Image table
    if profile_pic_id is not None:
        if db.session.query(Image).get(profile_pic_id) is None:
            return jsonify({'message': 'Invalid profile picture ID'}), 400

    # Create a new user
    new_user = User(phone_number=phone_number, username=username, profile_pic_id=profile_pic_id)
    new_user.set_password(password)  # Hash the password
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User signed up successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Extract username/phone_number and password from the request
    username = data.get('username')
    phone_number = data.get('phone_number')
    password = data.get('password')

    # Check if either username or phone number is provided
    if not username and not phone_number:
        return jsonify({'message': 'Username or phone number is required'}), 400

    # Find the user by username or phone number
    user = None
    if username:
        user = User.query.filter_by(username=username).first()
    elif phone_number:
        user = User.query.filter_by(phone_number=phone_number).first()

    # If user not found or password incorrect, return error
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid username/phone number or password'}), 401

    # Generate JWT token
    token_payload = {'id': user.id, 'exp': datetime.utcnow() + timedelta(hours=2)}  # Token expires in 2 hours
    token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')

    # Return token along with user information
    return jsonify({
        'message': 'Login successful',
        'user_id': user.id,
        'token': token  # Convert bytes to string
    }), 200

@app.route('/users', methods=['GET', 'OPTIONS'])
@token_required
def get_user_info(current_user):
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight request successful'}), 200
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization')

    # Serialize current user's data into JSON format
    user_data = {
        'user_id': current_user.id,
        'phone_number': current_user.phone_number,
        'username': current_user.username,
        'profile_pic_id': current_user.profile_pic_id
    }

    return jsonify(user_data)

@app.route('/payment/callback', methods=['POST'])
def payment_callback():
    data = request.get_json()

    # Extract relevant payment information
    ResultCode = data['Body']['stkCallback']['ResultCode']
    CheckoutRequestID = data['Body']['stkCallback']['CheckoutRequestID']

    if 'CallbackMetadata' in data['Body']['stkCallback']:
        CallbackMetadata = data['Body']['stkCallback']['CallbackMetadata']
        Amount = next((item['Value'] for item in CallbackMetadata['Item'] if item['Name'] == 'Amount'), None)
        MpesaReceiptNumber = next((item['Value'] for item in CallbackMetadata['Item'] if item['Name'] == 'MpesaReceiptNumber'), None)
        PhoneNumber = next((item['Value'] for item in CallbackMetadata['Item'] if item['Name'] == 'PhoneNumber'), None)
    else:
        Amount = None
        MpesaReceiptNumber = None
        PhoneNumber = None

    if ResultCode == 0:
        # Store payment information in the database
        payment = Payment(CheckoutRequestID=CheckoutRequestID, ResultCode=ResultCode, Amount=Amount, MpesaReceiptNumber=MpesaReceiptNumber, PhoneNumber=PhoneNumber)
        db.session.add(payment)
        db.session.commit()
        return jsonify({'message': 'Payment processed successfully'})
    elif ResultCode == 1031:
        return jsonify({'message': 'Transaction cancelled by user'})
    else:
        return jsonify({'message': 'Error processing payment'}), 500

@app.route('/payments', methods=['GET'])
def get_payments():
    # Retrieve all payment records from the database
    payments = Payment.query.all()

    # Serialize payment records into JSON format
    payments_json = []
    for payment in payments:
        payments_json.append({
            'CheckoutRequestID': payment.CheckoutRequestID,
            'ResultCode': payment.ResultCode,
            'Amount': payment.Amount,
            'MpesaReceiptNumber': payment.MpesaReceiptNumber,
            'PhoneNumber': payment.PhoneNumber
        })

    return jsonify({'payments': payments_json})

@app.route('/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    # Fetch the image data from the database
    image = Image.query.get_or_404(image_id)
    
    # Check if the image data exists
    if image is None or image.image_data is None:
        abort(404)  # Return a 404 error if image data is not found
    
    # Determine the MIME type based on the image file extension
    image_extension = 'png' if image.image_data.startswith(b'\x89PNG') else \
                      'jpg' if image.image_data.startswith(b'\xff\xd8\xff') else \
                      'jpeg' if image.image_data.startswith(b'\xff\xd8\xff') else \
                      'svg+xml' if image.image_data.startswith(b'<?xml') else None
    
    if image_extension is None:
        abort(404)  # Return a 404 error for unsupported image types
    
    mimetype = f'image/{image_extension}'
    
    # Send the image data with the determined MIME type
    return send_file(io.BytesIO(image.image_data), mimetype=mimetype)

if __name__ == '__main__':
    app.run(debug=True)
