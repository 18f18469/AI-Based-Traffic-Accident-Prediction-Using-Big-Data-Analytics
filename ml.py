import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# تحميل النموذج والمحوّلات
risk_model = joblib.load(os.path.join(BASE_DIR, "risk_model.pkl"))
encoder_day = joblib.load(os.path.join(BASE_DIR, "encoder_day.pkl"))
encoder_location = joblib.load(os.path.join(BASE_DIR, "encoder_location.pkl"))

def predict_risk(day, hour, injuries, location):
    day_enc = encoder_day.transform([day])[0]
    location_enc = encoder_location.transform([location])[0]

    X = [[day_enc, hour, injuries, location_enc]]

    risk_score = risk_model.predict(X)[0]

    if risk_score <= 0.3:
        risk_level = "Low"
    elif risk_score <= 0.6:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return risk_score, risk_level

def get_known_days():
    return list(encoder_day.classes_)

def get_known_locations():
    return list(encoder_location.classes_)
