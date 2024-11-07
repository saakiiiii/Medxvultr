import uuid

def generate_unique_code():
    return str(uuid.uuid4())[:8]
