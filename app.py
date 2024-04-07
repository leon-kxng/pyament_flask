from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Payment
import os

app = Flask(__name__)
CORS(app)  # Add CORS support
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'  # SQLite database file
db.init_app(app)

# Check if the database file already exists
db_file_exists = os.path.exists('payments.db')

with app.app_context():
    # Create database tables only if the database file doesn't exist
    if not db_file_exists:
        db.create_all()  # Create database tables

@app.route('/payment/callback', methods=['POST'])
def payment_callback():
    data = request.get_json()

    # Logging the JSON data received
    print("Received JSON data:")
    print(json.dumps(data, indent=4))

    # Extract relevant payment information
    ResultCode = data['Body']['stkCallback']['ResultCode']
    CheckoutRequestID = data['Body']['stkCallback']['CheckoutRequestID']
    Amount = data['Body']['stkCallback']['CallbackMetadata']['Item'][0]['Value']
    MpesaReceiptNumber = data['Body']['stkCallback']['CallbackMetadata']['Item'][1]['Value']
    PhoneNumber = data['Body']['stkCallback']['CallbackMetadata']['Item'][4]['Value']

    if ResultCode == 0:
        # Store payment information in the database
        payment = Payment(CheckoutRequestID=CheckoutRequestID, ResultCode=ResultCode, Amount=Amount, MpesaReceiptNumber=MpesaReceiptNumber, PhoneNumber=PhoneNumber)
        db.session.add(payment)
        db.session.commit()

    return jsonify({'message': 'Payment processed successfully'})

if __name__ == '__main__':
    app.run(debug=True)
