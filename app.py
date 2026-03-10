"""
Vehicle Service At Home - Flask Backend Application
Professional car and bike service booking platform with ML-powered recommendations
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import uuid

# Import ML model
from ml_model.service_classifier import ServiceClassifier, initialize_model

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'vehicle-service-secret-key-2024'
app.config['JSON_SORT_KEYS'] = False

# Global variables
service_classifier = None
service_centers_data = None
bookings = []

def load_service_centers():
    """Load service centers data from JSON file"""
    global service_centers_data
    try:
        with open('service_centers.json', 'r', encoding='utf-8') as f:
            service_centers_data = json.load(f)
        return True
    except Exception as e:
        print(f"Error loading service centers: {e}")
        return False

def initialize_app():
    """Initialize the application"""
    global service_classifier
    
    # Load service centers
    load_service_centers()
    
    # Initialize ML model
    service_classifier = initialize_model()
    
    print("Application initialized successfully!")

# Initialize on startup
initialize_app()

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/services')
def services():
    """Services listing page"""
    return render_template('services.html')

@app.route('/booking')
def booking():
    """Booking form page"""
    return render_template('booking.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/service-centers', methods=['GET'])
def get_service_centers():
    """Get all service centers or filter by vehicle type"""
    vehicle_type = request.args.get('type', 'all')
    brand = request.args.get('brand', '').lower()
    city = request.args.get('city', '').lower()
    
    if service_centers_data is None:
        return jsonify({'error': 'Service data not available'}), 500
    
    result = {
        'bike_centers': [],
        'car_centers': [],
        'all_brands': {
            'bikes': list(service_centers_data['bike_service_centers'].keys()),
            'cars': list(service_centers_data['car_service_centers'].keys())
        }
    }
    
    # Filter bike centers
    if vehicle_type in ['all', 'bike']:
        bike_centers = service_centers_data['bike_service_centers']
        for brand_name, centers in bike_centers.items():
            if brand and brand != brand_name:
                continue
            for center in centers:
                if city and city != center['city'].lower():
                    continue
                result['bike_centers'].append({
                    'brand': brand_name,
                    **center
                })
    
    # Filter car centers
    if vehicle_type in ['all', 'car']:
        car_centers = service_centers_data['car_service_centers']
        for brand_name, centers in car_centers.items():
            if brand and brand != brand_name:
                continue
            for center in centers:
                if city and city != center['city'].lower():
                    continue
                result['car_centers'].append({
                    'brand': brand_name,
                    **center
                })
    
    return jsonify(result)

@app.route('/api/brands', methods=['GET'])
def get_brands():
    """Get all available vehicle brands"""
    vehicle_type = request.args.get('type', 'all')
    
    result = {
        'bikes': [],
        'cars': []
    }
    
    if service_centers_data is None:
        return jsonify(result)
    
    if vehicle_type in ['all', 'bike']:
        result['bikes'] = [
            {'id': brand, 'name': brand.replace('_', ' ').title()} 
            for brand in service_centers_data['bike_service_centers'].keys()
        ]
    
    if vehicle_type in ['all', 'car']:
        result['cars'] = [
            {'id': brand, 'name': brand.replace('_', ' ').title()} 
            for brand in service_centers_data['car_service_centers'].keys()
        ]
    
    return jsonify(result)

@app.route('/api/service-types', methods=['GET'])
def get_service_types():
    """Get all available service types"""
    if service_centers_data is None:
        return jsonify({'error': 'Service data not available'}), 500
    
    return jsonify(service_centers_data['service_types'])

@app.route('/api/predict-service', methods=['POST'])
def predict_service():
    """ML-based service prediction from problem description"""
    data = request.get_json()
    
    if not data or 'description' not in data:
        return jsonify({'error': 'Description is required'}), 400
    
    description = data['description']
    vehicle_type = data.get('vehicle_type', 'car')
    
    # Use ML model to predict
    prediction = service_classifier.predict(description)
    
    # Add service descriptions
    prediction['service_descriptions'] = {}
    for service in prediction['recommended_services']:
        prediction['service_descriptions'][service] = service_classifier.get_service_description(service)
    
    return jsonify(prediction)

@app.route('/api/book-service', methods=['POST'])
def book_service():
    """Book a service appointment"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'phone', 'vehicle_type', 'vehicle_brand', 
                       'address', 'pincode', 'problem_description']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate pincode format (6 digits for India)
    pincode = data['pincode']
    if not pincode.isdigit() or len(pincode) != 6:
        return jsonify({'error': 'Please enter a valid 6-digit pincode'}), 400
    
    # Create booking
    booking = {
        'id': str(uuid.uuid4())[:8].upper(),
        'name': data['name'],
        'phone': data['phone'],
        'email': data.get('email', ''),
        'vehicle_type': data['vehicle_type'],
        'vehicle_brand': data['vehicle_brand'],
        'vehicle_model': data.get('vehicle_model', ''),
        'address': data['address'],
        'pincode': pincode,
        'problem_description': data['problem_description'],
        'preferred_date': data.get('preferred_date', ''),
        'preferred_time': data.get('preferred_time', ''),
        'status': 'Pending',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Get ML predictions for the problem
    prediction = service_classifier.predict(data['problem_description'])
    booking['recommended_services'] = prediction['recommended_services']
    
    # Save booking
    bookings.append(booking)
    
    return jsonify({
        'success': True,
        'booking_id': booking['id'],
        'message': 'Service booking submitted successfully!',
        'booking': booking
    })

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings (for admin)"""
    return jsonify(bookings)

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Get all available cities"""
    cities = set()
    
    if service_centers_data:
        # Get cities from bike centers
        for centers in service_centers_data['bike_service_centers'].values():
            for center in centers:
                cities.add(center['city'])
        
        # Get cities from car centers
        for centers in service_centers_data['car_service_centers'].values():
            for center in centers:
                cities.add(center['city'])
    
    return jsonify(sorted(list(cities)))

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(500)
def server_error(e):
    """500 error handler"""
    return render_template('error.html', error_code=500, error_message='Server error'), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("Vehicle Service At Home - Starting Server")
    print("=" * 60)
    print("\nAccess the website at: http://127.0.0.1:5000")
    print("\nPress CTRL+C to stop the server\n")
    app.run(debug=True, host='127.0.0.1', port=5000)

