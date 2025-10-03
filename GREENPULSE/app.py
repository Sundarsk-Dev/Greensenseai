from flask import Flask, render_template, jsonify
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# Load trained model and scaler
try:
    model = joblib.load('models/emission_model.pkl')
    scaler = joblib.load('models/scaler.pkl')
    print("✅ Model and scaler loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None
    scaler = None

# Generate synthetic historical data (simulating 24 hours of readings)
def generate_historical_data(hours=24):
    """Generate realistic emission data for the past 24 hours"""
    current_time = datetime.now()
    data = []
    
    # Base values with realistic variations
    base_co = 2.5
    base_c6h6 = 8.0
    base_nox = 200
    base_no2 = 110
    base_temp = 22
    base_rh = 50
    
    for i in range(hours, 0, -1):
        timestamp = current_time - timedelta(hours=i)
        hour = timestamp.hour
        
        # Simulate traffic patterns (higher emissions during rush hours)
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            traffic_factor = 1.5
        elif 22 <= hour or hour <= 5:
            traffic_factor = 0.6
        else:
            traffic_factor = 1.0
        
        # Add some randomness
        noise = random.uniform(0.85, 1.15)
        
        co = base_co * traffic_factor * noise
        c6h6 = base_c6h6 * traffic_factor * noise
        nox = base_nox * traffic_factor * noise
        no2 = base_no2 * traffic_factor * noise
        temp = base_temp + random.uniform(-3, 3)
        rh = base_rh + random.uniform(-10, 10)
        
        # Calculate emission score (inverse of pollution)
        pollutant_avg = (co/5 + c6h6/15 + nox/400 + no2/200) / 4
        score = max(0, min(10, 10 * (1 - pollutant_avg)))
        
        data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'hour': timestamp.strftime('%H:%M'),
            'co': round(co, 2),
            'c6h6': round(c6h6, 2),
            'nox': round(nox, 2),
            'no2': round(no2, 2),
            'temp': round(temp, 1),
            'rh': round(rh, 1),
            'score': round(score, 2)
        })
    
    return data

# Prepare features for model prediction (matching 16 features)
def prepare_features(current_data, lag_data, rolling_3h, rolling_6h):
    """Prepare 16 features in exact order for model prediction"""
    
    # Calculate NO2/NOx ratio
    no2_nox_ratio = current_data['no2'] / current_data['nox'] if current_data['nox'] > 0 else 0
    
    features = [
        current_data['temp'],           # T
        current_data['rh'],             # RH
        current_data['hour_num'],       # Hour
        current_data['day_of_week'],    # DayOfWeek
        current_data['month'],          # Month
        lag_data['co'],                 # CO(GT)_Lag1
        lag_data['c6h6'],               # C6H6(GT)_Lag1
        lag_data['nox'],                # NOx(GT)_Lag1
        lag_data['no2'],                # NO2(GT)_Lag1
        lag_data['temp'],               # T_Lag1
        lag_data['rh'],                 # RH_Lag1
        rolling_3h['co'],               # CO(GT)_Rolling_3h
        rolling_6h['co'],               # CO(GT)_Rolling_6h
        rolling_3h['nox'],              # NOx(GT)_Rolling_3h
        rolling_6h['nox'],              # NOx(GT)_Rolling_6h
        no2_nox_ratio                   # NO2_NOx_Ratio
    ]
    
    return np.array(features).reshape(1, -1)

@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('index.html')

@app.route('/api/refresh-data')
def refresh_data():
    """Get current emission data and prediction"""
    try:
        # Generate historical data
        historical = generate_historical_data(24)
        
        # Current reading (latest)
        current = historical[-1]
        
        # For model prediction, we need lag and rolling features
        if len(historical) >= 6:
            # Lag data (1 hour ago)
            lag_data = historical[-2]
            
            # Rolling averages (3h and 6h)
            last_3h = historical[-3:]
            last_6h = historical[-6:]
            
            rolling_3h = {
                'co': np.mean([d['co'] for d in last_3h]),
                'nox': np.mean([d['nox'] for d in last_3h])
            }
            rolling_6h = {
                'co': np.mean([d['co'] for d in last_6h]),
                'nox': np.mean([d['nox'] for d in last_6h])
            }
            
            # Prepare current data with time features
            now = datetime.now()
            current_data = {
                'co': current['co'],
                'c6h6': current['c6h6'],
                'nox': current['nox'],
                'no2': current['no2'],
                'temp': current['temp'],
                'rh': current['rh'],
                'hour_num': now.hour,
                'day_of_week': now.weekday(),
                'month': now.month
            }
            
            lag_data_dict = {
                'co': lag_data['co'],
                'c6h6': lag_data['c6h6'],
                'nox': lag_data['nox'],
                'no2': lag_data['no2'],
                'temp': lag_data['temp'],
                'rh': lag_data['rh']
            }
            
            # Prepare features and predict
            if model and scaler:
                features = prepare_features(current_data, lag_data_dict, rolling_3h, rolling_6h)
                features_scaled = scaler.transform(features)
                predicted_score = float(model.predict(features_scaled)[0])
                predicted_score = max(0, min(10, predicted_score))  # Clamp to 0-10
            else:
                predicted_score = current['score'] * random.uniform(0.9, 1.1)
        else:
            predicted_score = current['score'] * random.uniform(0.9, 1.1)
        
        # Determine status
        current_score = current['score']
        if current_score >= 6.5:
            status = "Safe"
            color = "green"
        elif current_score >= 4.0:
            status = "Moderate"
            color = "yellow"
        else:
            status = "High Emissions"
            color = "red"
        
        if predicted_score >= 6.5:
            pred_status = "Safe"
            pred_color = "green"
        elif predicted_score >= 4.0:
            pred_status = "Moderate"
            pred_color = "yellow"
        else:
            pred_status = "High Emissions"
            pred_color = "red"
        
        return jsonify({
            'success': True,
            'current': {
                'score': round(current_score, 2),
                'status': status,
                'color': color,
                'timestamp': current['timestamp'],
                'co': current['co'],
                'nox': current['nox'],
                'no2': current['no2'],
                'temp': current['temp'],
                'rh': current['rh']
            },
            'prediction': {
                'score': round(predicted_score, 2),
                'status': pred_status,
                'color': pred_color
            },
            'historical': [
                {
                    'time': h['hour'],
                    'score': h['score']
                } for h in historical
            ]
        })
    
    except Exception as e:
        print(f"Error in refresh_data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\n🌱 GreenPulse AI - Starting server...")
    print("📊 Dashboard will be available at: http://127.0.0.1:5000")
    print("\n")
    app.run(debug=True, port=5000)