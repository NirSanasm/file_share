from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from utils import generate_short_id, save_text_paste, save_upload_file, get_file_content, find_file, get_public_url
from config import STORAGE_BACKEND, LOCAL_UPLOAD_DIR

app = FastAPI(title="Easy Share")

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
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/upload")
async def upload_paste(
    text: str = Form(None),
    file: UploadFile = File(None)
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="No content provided")

    short_id = generate_short_id()
    
    if file and file.filename:
        # It's a file upload
        ext = os.path.splitext(file.filename)[1]
        filename = f"{short_id}{ext}"
        await save_upload_file(file, filename)
    else:
        # It's a text paste
        filename = f"{short_id}.txt"
        save_text_paste(text, filename)

    return {"url": f"/{short_id}", "id": short_id}


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
        "id": paste_id
    })
