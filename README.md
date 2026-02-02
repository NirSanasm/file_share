# Easy Share

A modern, secure file-sharing and pastebin application built with FastAPI. Share text snippets, code, and images with automatically generated short links.

## ✨ Features

- **📝 Text & Code Sharing** - Share text snippets, code, and markdown with syntax highlighting
- **🖼️ Image Uploads** - Support for PNG, JPEG, GIF, WebP, and BMP images (up to 10MB)
- **🔗 Short Links** - Automatically generated short URLs for easy sharing
- **🛡️ Security First**
  - File type validation with magic byte verification
  - MIME type checking
  - Filename sanitization
  - Content security validation
- **🚦 Rate Limiting** - Prevent abuse with intelligent rate limiting
  - 10 uploads per hour per IP
  - 100 views per hour per IP
  - Automatic temporary bans for excessive violations
- **🤖 CAPTCHA Protection** - Google reCAPTCHA v2 integration to prevent bot abuse
- **🗑️ Auto Cleanup** - Automatic deletion of files after 7 days
- **💾 Flexible Storage** - Support for local filesystem or Google Cloud Storage
- **📊 Storage Quotas** - Per-IP storage limits (100MB per IP)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pastebin_alt
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure the following:
   ```env
   # Storage Backend: "local" or "gcs"
   STORAGE_BACKEND=local
   
   # Google Cloud Storage (only needed if STORAGE_BACKEND=gcs)
   GCS_BUCKET_NAME=your-bucket-name
   GCS_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
   
   # Google reCAPTCHA v2 (get keys from https://www.google.com/recaptcha/admin)
   RECAPTCHA_SITE_KEY=your_site_key_here
   RECAPTCHA_SECRET_KEY=your_secret_key_here
   ```

4. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

5. **Open your browser**
   
   Navigate to `http://localhost:8000`

## 📁 Project Structure

```
pastebin_alt/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── utils.py               # Utility functions (ID generation, file operations)
├── storage.py             # Storage backend abstraction (local/GCS)
├── security.py            # File validation and security checks
├── rate_limiter.py        # Rate limiting middleware
├── captcha.py             # reCAPTCHA verification
├── cleanup.py             # Automatic file cleanup service
├── security_config.py     # Security configuration
├── templates/             # HTML templates
│   ├── index.html        # Upload page
│   └── view.html         # View shared content page
├── static/               # Static assets
│   ├── style.css        # Styles
│   └── script.js        # Frontend JavaScript
├── uploads/             # Local file storage (if using local backend)
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (create from .env.example)
```

## 🔧 Configuration

### Storage Backends

#### Local Storage (Default)
```env
STORAGE_BACKEND=local
```
Files are stored in the `uploads/` directory.

#### Google Cloud Storage
```env
STORAGE_BACKEND=gcs
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_JSON={"type":"service_account",...}
```

### Security Settings

The application includes comprehensive security features:

- **File Size Limits**
  - Images: 10MB max
  - Text/Code: 1MB max
  
- **Allowed File Types**
  - Images: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`
  - Text: `.txt`, `.md`, `.json`, `.xml`, `.csv`, `.log`
  - Code: `.py`, `.js`, `.html`, `.css`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.ts`, `.jsx`, `.tsx`

- **Blocked File Types**
  - Executables and potentially dangerous files are automatically rejected

### Rate Limiting

Configure rate limits in `rate_limiter.py`:
```python
RATE_LIMIT_UPLOADS = 10        # Max uploads per hour
RATE_LIMIT_VIEWS = 100         # Max views per hour
BAN_THRESHOLD = 20             # Violations before ban
BAN_DURATION = 86400           # Ban duration (24 hours)
```

### Storage Quotas

Configure storage quotas in `cleanup.py`:
```python
MAX_STORAGE_PER_IP = 100 * 1024 * 1024  # 100MB per IP
```

## 🔐 Security Features

### File Validation
- **Extension Checking** - Whitelist/blacklist validation
- **MIME Type Verification** - Using python-magic (libmagic)
- **Magic Byte Validation** - Ensures file content matches claimed type
- **Filename Sanitization** - Prevents path traversal attacks

### Rate Limiting
- **Sliding Window Algorithm** - Accurate rate limiting
- **IP-based Tracking** - Per-IP limits
- **Automatic Bans** - Temporary bans for repeat offenders
- **Proxy Support** - Handles X-Forwarded-For headers

### CAPTCHA Protection
- **Google reCAPTCHA v2** - Prevents automated abuse
- **Optional** - Can be disabled by not setting CAPTCHA keys

## 🗑️ Automatic Cleanup

The application includes an automatic cleanup service that:
- Runs every hour
- Deletes files older than 7 days
- Tracks file metadata and storage quotas
- Prevents storage bloat

## 📡 API Endpoints

### `POST /api/upload`
Upload text or file content.

**Form Data:**
- `text` (optional): Text content to share
- `file` (optional): File to upload
- `g-recaptcha-response` (required if CAPTCHA enabled): reCAPTCHA token

**Response:**
```json
{
  "url": "/abc123",
  "id": "abc123",
  "full_url": "http://localhost:8000/abc123",
  "expires_in_days": 7
}
```

### `GET /{paste_id}`
View shared content by ID.

**Response:** HTML page displaying the content

## 🛠️ Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running in Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

For production deployment, consider using:
- **Gunicorn** with Uvicorn workers
- **Nginx** as a reverse proxy
- **Docker** for containerization
- **Redis** for distributed rate limiting (requires code modification)

## 📦 Dependencies

- **fastapi** - Modern web framework
- **uvicorn** - ASGI server
- **python-multipart** - Form data parsing
- **jinja2** - Template engine
- **aiofiles** - Async file operations
- **google-cloud-storage** - GCS integration
- **python-dotenv** - Environment variable management
- **python-magic** - File type detection
- **python-magic-bin** - libmagic binaries (Windows)
- **requests** - HTTP library for CAPTCHA verification

## 🚨 Important Notes

1. **CAPTCHA Keys**: The application requires valid Google reCAPTCHA keys to function properly. Get them from [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin).

2. **Storage Backend**: For production use with multiple servers, use Google Cloud Storage instead of local storage.

3. **Rate Limiting**: The current implementation uses in-memory storage. For distributed deployments, consider using Redis.

4. **File Cleanup**: Files are automatically deleted after 7 days. Adjust the retention period in `cleanup.py` if needed.

5. **Security**: Always run behind HTTPS in production to protect user data and CAPTCHA tokens.

## 📝 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For issues or questions, please open an issue on the repository.
