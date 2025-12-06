# utils/generate_username.py
import uuid

def generate_flow_username():
    # Take first 6 characters of UUID
    return f"FLOW-{uuid.uuid4().hex[:6].upper()}"
