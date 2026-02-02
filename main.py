from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os
from utils import generate_short_id, save_text_paste, save_upload_file, get_file_content, find_file, get_public_url
from config import STORAGE_BACKEND, LOCAL_UPLOAD_DIR, RECAPTCHA_SITE_KEY
from security import validate_upload_file, validate_text_content, sanitize_filename, get_file_category
from rate_limiter import RateLimitMiddleware, rate_limiter
from cleanup import cleanup_service, file_metadata
from captcha import verify_recaptcha, is_captcha_enabled

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Start cleanup service
    import asyncio
    cleanup_task = asyncio.create_task(cleanup_service.run_cleanup_loop())
    print("[Startup] Cleanup service started")
    
    yield
    
    # Shutdown: Stop cleanup service
    cleanup_service.stop()
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    print("[Shutdown] Cleanup service stopped")


app = FastAPI(title="Easy Share", lifespan=lifespan)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount uploads only for local storage
if STORAGE_BACKEND == "local":
    if not os.path.exists(LOCAL_UPLOAD_DIR):
        os.makedirs(LOCAL_UPLOAD_DIR)
    app.mount("/uploads", StaticFiles(directory=LOCAL_UPLOAD_DIR), name="uploads")

# Setup templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recaptcha_site_key": RECAPTCHA_SITE_KEY
    })


@app.post("/api/upload")
async def upload_paste(
    request: Request,
    text: str = Form(None),
    file: UploadFile = File(None),
    recaptcha_token: str = Form(None, alias="g-recaptcha-response")
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="No content provided")
    
    # Get client IP for quota tracking and CAPTCHA verification
    client_ip = rate_limiter.get_client_ip(request)
    
    # Verify CAPTCHA if enabled
    if is_captcha_enabled():
        is_valid, error_msg = verify_recaptcha(recaptcha_token, client_ip)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg or "CAPTCHA verification failed")
    
    short_id = generate_short_id()
    file_size = 0
    
    if file and file.filename:
        # Validate uploaded file
        is_valid, error, content = await validate_upload_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        file_size = len(content)
        
        # Check storage quota for this IP
        quota_ok, quota_error = file_metadata.check_ip_quota(client_ip, file_size)
        if not quota_ok:
            raise HTTPException(status_code=429, detail=quota_error)
        
        # Sanitize filename and save
        sanitized_name = sanitize_filename(file.filename)
        ext = os.path.splitext(sanitized_name)[1]
        filename = f"{short_id}{ext}"
        
        # Save file using the already-read content
        from io import BytesIO
        from fastapi import UploadFile as FastAPIUploadFile
        
        # Create a new UploadFile object with the validated content
        validated_file = FastAPIUploadFile(
            file=BytesIO(content),
            filename=filename,
            headers=file.headers
        )
        await save_upload_file(validated_file, filename)
        
        # Record file metadata
        file_metadata.add_file(filename, client_ip, file_size)
    else:
        # Validate text content
        is_valid, error = validate_text_content(text)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        file_size = len(text.encode('utf-8'))
        
        # Check storage quota for this IP
        quota_ok, quota_error = file_metadata.check_ip_quota(client_ip, file_size)
        if not quota_ok:
            raise HTTPException(status_code=429, detail=quota_error)
        
        # It's a text paste
        filename = f"{short_id}.txt"
        save_text_paste(text, filename)
        
        # Record file metadata
        file_metadata.add_file(filename, client_ip, file_size)

    return {
        "url": f"/{short_id}", 
        "id": short_id, 
        "full_url": f"{request.base_url}{short_id}",
        "expires_in_days": 7
    }


@app.get("/{paste_id}", response_class=HTMLResponse)
async def view_paste(request: Request, paste_id: str):
    # Find the file in storage
    found_file = find_file(paste_id)
    
    if not found_file:
        raise HTTPException(status_code=404, detail="Paste not found")
    
    content, type_ = get_file_content(found_file)
    
    is_image = False
    if type_ == "binary":
        ext = os.path.splitext(found_file)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
            is_image = True
            content = get_public_url(found_file)

    return templates.TemplateResponse("view.html", {
        "request": request,
        "content": content,
        "is_image": is_image,
        "id": paste_id,
        "share_link": f"{request.base_url}{paste_id}"
    })
