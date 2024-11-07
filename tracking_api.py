import random

def get_tracking_status(unique_code):
    statuses = ["In transit", "At warehouse", "Out for delivery", "Delivered"]
    return random.choice(statuses)
