from flask import Flask
from models import db, Image
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'  # Use the correct database URI
db.init_app(app)

def add_image_to_database(image_data):
    with app.app_context():
        # Check if the image already exists in the database
        existing_image = Image.query.filter_by(image_data=image_data).first()
        if existing_image:
            print(f"Image already exists in the database. Skipping...")
            return

        # Create a new image record
        new_image = Image(image_data=image_data)
        db.session.add(new_image)
        db.session.commit()
        print(f"Image added to the database.")

if __name__ == '__main__':
    # Add images to the database
    images_directory = './images/'  # Change this to the directory containing your images
    for filename in os.listdir(images_directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
            image_path = os.path.join(images_directory, filename)
            with open(image_path, 'rb') as f:
                image_data = f.read()
            add_image_to_database(image_data)
