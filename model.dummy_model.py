import random

# Simulate model checking for medicine quality based on data
def check_medicine_quality(medicine_data):
    return random.choice(['Authentic', 'Counterfeit'])



import random

# Dummy medicine data
medicine_data = [
    {"name": "Paracetamol", "salts": ["Paracetamol"], "code": "PCT-001", "quality": "Authentic"},
    {"name": "Ibuprofen", "salts": ["Ibuprofen"], "code": "IBP-002", "quality": "Authentic"},
    {"name": "Aspirin", "salts": ["Acetylsalicylic Acid"], "code": "ASP-003", "quality": "Authentic"},
    {"name": "Metformin", "salts": ["Metformin Hydrochloride"], "code": "MET-004", "quality": "Counterfeit"},
    {"name": "Amoxicillin", "salts": ["Amoxicillin Trihydrate"], "code": "AMX-005", "quality": "Authentic"},
    {"name": "Atorvastatin", "salts": ["Atorvastatin Calcium"], "code": "ATR-006", "quality": "Counterfeit"},
    {"name": "Ciprofloxacin", "salts": ["Ciprofloxacin Hydrochloride"], "code": "CIP-007", "quality": "Authentic"},
    {"name": "Omeprazole", "salts": ["Omeprazole Magnesium"], "code": "OMP-008", "quality": "Counterfeit"},
    {"name": "Levothyroxine", "salts": ["Levothyroxine Sodium"], "code": "LVT-009", "quality": "Authentic"},
    {"name": "Losartan", "salts": ["Losartan Potassium"], "code": "LOS-010", "quality": "Authentic"}
]

# Simulated model function
def check_medicine_quality(salts):
    for medicine in medicine_data:
        if set(salts) == set(medicine["salts"]):
            return medicine["quality"]
    return random.choice(["Authentic", "Counterfeit"])  # Default to random if not found

# Example usage
sample_salts = ["Paracetamol"]
print("Medicine Quality:", check_medicine_quality(sample_salts))  # Output: Authentic




