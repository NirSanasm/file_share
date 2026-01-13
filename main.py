from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from utils import generate_short_id, save_text_paste, save_upload_file, get_file_content, UPLOAD_DIR

app = FastAPI(title="Pastebin Clone")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
        is_image = file.content_type.startswith("image/") if file.content_type else False
        # Save metadata or just rely on extension/content inspection in view
    else:
        # It's a text paste
        filename = f"{short_id}.txt"
        save_text_paste(text, filename)

    return {"url": f"/{short_id}", "id": short_id}

@app.get("/{paste_id}", response_class=HTMLResponse)
async def view_paste(request: Request, paste_id: str):
    # Simple lookup logic - in a real app, use a DB to map ID to filename/type
    # Here we search for files starting with the ID in the upload dir
    
    found_file = None
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(paste_id + ".") or f == paste_id:
            found_file = f
            break
            
    if not found_file:
        raise HTTPException(status_code=404, detail="Paste not found")
        
    content, type_ = get_file_content(found_file)
    
    is_image = False
    if type_ == "binary":
        # Assume it's an image if it was uploaded and we treated it as binary or based on extension
        ext = os.path.splitext(found_file)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
            is_image = True
            content = f"/uploads/{found_file}"
        else:
             # Fallback for other file types or force download? For now, treat as text or generic link
             pass

    return templates.TemplateResponse("view.html", {
        "request": request,
        "content": content,
        "is_image": is_image,
        "id": paste_id
    })
