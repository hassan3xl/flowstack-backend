# utils/generate_username.py
import uuid

def generate_username():
    # Take first 6 characters of UUID
    return f"user-{uuid.uuid4().hex[:6]}"
    # return f"user-{uuid.uuid4().hex[:6].upper()}"

