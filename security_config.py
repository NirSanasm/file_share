"""
Security configuration settings.
Centralized configuration for all security features.
"""

# File Upload Security
MAX_IMAGE_SIZE_MB = 10  # Maximum image file size in MB
MAX_TEXT_SIZE_MB = 1    # Maximum text file size in MB
MAX_FILE_SIZE_MB = 10   # Default maximum file size in MB

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
ALLOWED_TEXT_EXTENSIONS = ['.txt', '.md', '.json', '.xml', '.csv', '.log']
ALLOWED_CODE_EXTENSIONS = ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.go', '.rs', '.ts', '.jsx', '.tsx']

# Rate Limiting
RATE_LIMIT_UPLOADS_PER_HOUR = 10  # Max uploads per hour per IP
RATE_LIMIT_VIEWS_PER_HOUR = 100   # Max views per hour per IP
RATE_LIMIT_WINDOW_SECONDS = 3600  # Time window in seconds (1 hour)

# Ban Configuration
BAN_THRESHOLD_VIOLATIONS = 20     # Number of violations before ban
BAN_DURATION_HOURS = 24           # Ban duration in hours

# Resource Management
FILE_EXPIRATION_DAYS = 7          # Files expire after X days
CLEANUP_INTERVAL_HOURS = 1        # Run cleanup every X hours
MAX_STORAGE_PER_IP_MB = 100       # Maximum storage per IP in MB

# Content Validation
MIN_TEXT_LENGTH = 1               # Minimum text content length
MAX_TEXT_LENGTH_MB = 1            # Maximum text content length in MB
SPAM_DETECTION_ENABLED = True     # Enable basic spam detection
