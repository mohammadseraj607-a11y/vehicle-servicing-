"""
Service Classifier - ML Model for Vehicle Service Recommendation
Uses NLP to analyze problem descriptions and recommend appropriate services
"""

import os
import json
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import warnings
warnings.filterwarnings('ignore')

# Service keywords mapping
SERVICE_KEYWORDS = {
    'General Service': ['service', 'maintenance', 'checkup', 'regular', 'routine', 'periodic', 'full service'],
    'Oil Change': ['oil', 'lubrication', 'engine oil', 'oil leak', 'oil change', 'oil filter'],
    'Brake Repair': ['brake', 'braking', 'stop', 'squeaking', 'grinding', 'pad', 'disc', ' ABS ', 'brake fluid'],
    'Engine Repair': ['engine', 'motor', 'starting', 'not start', 'cold start', 'overheating', 'temperature', 
                      'smoke', 'power loss', 'misfire', 'check engine'],
    'Transmission Repair': ['transmission', 'gear', 'shifting', 'clutch', 'manual', 'automatic', 'gearbox',
                           'not shifting', 'hard shift', 'slipping'],
    'Suspension Repair': ['suspension', 'shock', 'bounce', 'ride comfort', 'wheel', 'alignment', 'balancing',
                         'steering', 'noise on bumps', 'wheels'],
    'AC Service': ['ac', 'air conditioning', 'cooling', 'heater', 'temperature control', 'refrigerant',
                   'not cooling', 'warm air', 'fan'],
    'Electrical Repair': ['battery', 'alternator', 'light', 'wiring', 'electrical', 'horn', 'windshield',
                          'wiper', 'indicator', 'dashboard', 'sensor'],
    'Battery Replacement': ['battery', 'dead', 'not starting', 'jump start', 'battery light', 'weak battery'],
    'Tire Service': ['tire', 'tyres', 'puncture', 'flat', 'wheel', 'balancing', 'alignment', 'tread'],
    'Clutch Repair': ['clutch', 'slipping', 'hard clutch', 'clutch plate', 'press', 'release'],
    'Exhaust Repair': ['exhaust', 'smoke', 'noise', 'silencer', 'catalytic', 'emission', 'smell'],
    'Body Paint': ['paint', 'dent', 'scratch', 'body', 'panel', 'fender', 'bumper', 'damage'],
    'Car Wash': ['wash', 'clean', 'polish', 'detailing', 'interior', 'exterior'],
    'Interior Cleaning': ['interior', 'cleaning', 'seats', 'carpets', 'odor', 'vacuum']
}

class ServiceClassifier:
    """ML Model for classifying vehicle service needs based on problem description"""
    
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.service_types = list(SERVICE_KEYWORDS.keys())
        self.is_trained = False
        
    def _prepare_training_data(self):
        """Prepare training data from keywords"""
        texts = []
        labels = []
        
        for service, keywords in SERVICE_KEYWORDS.items():
            for keyword in keywords:
                texts.append(keyword)
                labels.append(service)
                
        return texts, labels
    
    def _keyword_based_prediction(self, description):
        """Keyword-based prediction as fallback"""
        description_lower = description.lower()
        scores = {}
        
        for service, keywords in SERVICE_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    score += 1
            scores[service] = score
        
        # Sort by score and return top recommendations
        sorted_services = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        recommendations = [s[0] for s in sorted_services if s[1] > 0]
        
        if not recommendations:
            return ['General Service']
        
        return recommendations[:3]
    
    def train(self):
        """Train the ML model"""
        try:
            texts, labels = self._prepare_training_data()
            
            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=500)
            X = self.vectorizer.fit_transform(texts)
            y = np.array(labels)
            
            # Train Naive Bayes classifier
            self.model = MultinomialNB(alpha=0.1)
            self.model.fit(X, y)
            
            # Evaluate on training data
            y_pred = self.model.predict(X)
            self.is_trained = True
            
            return True, "Model trained successfully"
        except Exception as e:
            return False, f"Training error: {str(e)}"
    
    def predict(self, description):
        """Predict service type from problem description"""
        if not description or len(description.strip()) == 0:
            return {
                'recommended_services': ['General Service'],
                'confidence': 0.5,
                'all_scores': {}
            }
        
        # Try ML-based prediction
        if self.is_trained and self.vectorizer and self.model:
            try:
                X = self.vectorizer.transform([description])
                probabilities = self.model.predict_proba(X)[0]
                classes = self.model.classes_
                
                # Get probability scores
                scores = {}
                for i, cls in enumerate(classes):
                    scores[cls] = float(probabilities[i])
                
                # Sort by probability
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                top_services = [s[0] for s in sorted_scores[:3]]
                
                return {
                    'recommended_services': top_services,
                    'confidence': float(max(probabilities)),
                    'all_scores': scores
                }
            except Exception:
                pass
        
        # Fallback to keyword-based prediction
        recommendations = self._keyword_based_prediction(description)
        
        return {
            'recommended_services': recommendations,
            'confidence': 0.6,
            'all_scores': {}
        }
    
    def get_service_description(self, service_type):
        """Get detailed description for a service type"""
        descriptions = {
            'General Service': 'Complete vehicle inspection and maintenance including oil change, filter replacement, and system checks.',
            'Oil Change': 'Engine oil and filter replacement with premium quality lubricants.',
            'Brake Repair': 'Brake pad replacement, disc resurfacing, and brake fluid flush.',
            'Engine Repair': 'Comprehensive engine diagnostics and repair for starting, overheating, and performance issues.',
            'Transmission Repair': 'Transmission fluid service, gear repair, and clutch system maintenance.',
            'Suspension Repair': 'Shock absorber replacement, strut service, and wheel alignment.',
            'AC Service': 'AC refrigerant refill, compressor service, and cooling system repair.',
            'Electrical Repair': 'Battery service, wiring repairs, light and sensor replacements.',
            'Battery Replacement': 'Old battery removal and installation of new genuine battery.',
            'Tire Service': 'Puncture repair, tire rotation, wheel balancing, and alignment.',
            'Clutch Repair': 'Clutch plate replacement, hydraulic system service, and adjustment.',
            'Exhaust Repair': 'Silencer replacement, catalytic converter service, and emission control.',
            'Body Paint': 'Dent removal, scratch repair, and premium paint job.',
            'Car Wash': 'Exterior washing, polishing, and protective coating.',
            'Interior Cleaning': 'Deep cleaning of seats, carpets, and interior surfaces.'
        }
        return descriptions.get(service_type, 'Professional vehicle service')


def initialize_model():
    """Initialize and return the service classifier"""
    classifier = ServiceClassifier()
    success, message = classifier.train()
    print(f"ML Model: {message}")
    return classifier


if __name__ == "__main__":
    # Test the model
    classifier = initialize_model()
    
    test_descriptions = [
        "My car makes squeaking noise when braking",
        "Engine not starting in the morning, battery seems weak",
        "AC not cooling properly, giving warm air",
        "Car shaking at high speeds, need wheel alignment",
        "Oil leakage from engine bottom"
    ]
    
    print("\n=== Testing ML Model ===")
    for desc in test_descriptions:
        result = classifier.predict(desc)
        print(f"\nDescription: {desc}")
        print(f"Recommended: {result['recommended_services']}")
        print(f"Confidence: {result['confidence']:.2f}")

