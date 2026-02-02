"""
CAPTCHA verification module using Google reCAPTCHA v2.
"""
import requests
from typing import Tuple
from config import RECAPTCHA_SECRET_KEY


RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def verify_recaptcha(token: str, remote_ip: str = None) -> Tuple[bool, str]:
    """
    Verify reCAPTCHA token with Google's API.
    
    Args:
        token: The reCAPTCHA response token from the client
        remote_ip: Optional client IP address
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not token:
        return False, "CAPTCHA token is missing"
    
    if not RECAPTCHA_SECRET_KEY:
        # If no secret key configured, skip verification (for development)
        print("[WARNING] RECAPTCHA_SECRET_KEY not configured. Skipping CAPTCHA verification.")
        return True, ""
    
    # Prepare the request payload
    payload = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': token
    }
    
    if remote_ip:
        payload['remoteip'] = remote_ip
    
    try:
        # Make request to Google's verification API
        response = requests.post(
            RECAPTCHA_VERIFY_URL,
            data=payload,
            timeout=5
        )
        
        if response.status_code != 200:
            return False, f"CAPTCHA verification service error (status {response.status_code})"
        
        result = response.json()
        
        # Check if verification was successful
        if result.get('success'):
            return True, ""
        
        # Get error codes if verification failed
        error_codes = result.get('error-codes', [])
        
        # Map error codes to user-friendly messages
        error_messages = {
            'missing-input-secret': 'CAPTCHA configuration error',
            'invalid-input-secret': 'CAPTCHA configuration error',
            'missing-input-response': 'CAPTCHA verification required',
            'invalid-input-response': 'CAPTCHA verification failed. Please try again.',
            'bad-request': 'CAPTCHA verification failed',
            'timeout-or-duplicate': 'CAPTCHA expired. Please verify again.'
        }
        
        # Get the first error message
        if error_codes:
            error_msg = error_messages.get(error_codes[0], 'CAPTCHA verification failed')
        else:
            error_msg = 'CAPTCHA verification failed'
        
        return False, error_msg
        
    except requests.RequestException as e:
        print(f"[ERROR] CAPTCHA verification request failed: {e}")
        return False, "CAPTCHA verification service unavailable. Please try again."
    except Exception as e:
        print(f"[ERROR] CAPTCHA verification error: {e}")
        return False, "CAPTCHA verification error. Please try again."


def is_captcha_enabled() -> bool:
    """Check if CAPTCHA is enabled (secret key is configured)."""
    return bool(RECAPTCHA_SECRET_KEY)
