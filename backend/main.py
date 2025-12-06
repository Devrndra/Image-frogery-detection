from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import io
import base64
from PIL import Image
import numpy as np
import os
from .inference import ImageAuthenticator

app = FastAPI(title="Image Authentication API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Authenticator
authenticator = ImageAuthenticator()

@app.get("/")
async def root():
    return {"message": "Image Authentication API is running"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        image_stream = io.BytesIO(contents)
        
        result = authenticator.predict(image_stream)
        
        if result is None:
            raise HTTPException(status_code=500, detail="Prediction failed")
            
        # Convert ELA image to base64 for display
        ela_buffer = io.BytesIO()
        result['ela_image'].save(ela_buffer, format="JPEG")
        ela_b64 = base64.b64encode(ela_buffer.getvalue()).decode('utf-8')
        
        # Convert Mask to base64 (heatmap)
        # Normalize mask to 0-255
        mask_uint8 = (result['mask'] * 255).astype(np.uint8)
        mask_img = Image.fromarray(mask_uint8, mode='L')
        mask_buffer = io.BytesIO()
        mask_img.save(mask_buffer, format="PNG")
        mask_b64 = base64.b64encode(mask_buffer.getvalue()).decode('utf-8')
        
        return JSONResponse(content={
            "filename": file.filename,
            "is_tampered": result['is_tampered'],
            "confidence": result['confidence'],
            "ela_image": f"data:image/jpeg;base64,{ela_b64}",
            "mask_image": f"data:image/png;base64,{mask_b64}"
        })
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- HASHING ENDPOINTS ---
from core.hashing import generate_phash, compare_hashes
import shutil

@app.post("/hash")
async def create_hash(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Save to temp file
        temp_path = f"temp_hash_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Generate Hash
        phash = generate_phash(temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if phash is None:
            raise HTTPException(status_code=500, detail="Failed to generate hash")
            
        return {"filename": file.filename, "hash": phash}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare")
async def compare_image_hash(original_hash: str, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    try:
        # Save to temp file
        temp_path = f"temp_compare_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Compare
        distance, is_authentic, suspect_hash = compare_hashes(original_hash, temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if distance == -1:
             raise HTTPException(status_code=500, detail="Comparison failed")
             
        return {
            "filename": file.filename,
            "original_hash": original_hash,
            "suspect_hash": suspect_hash,
            "distance": distance,
            "is_authentic": is_authentic,
            "message": "Authentication SUCCESS" if is_authentic else "Authentication FAILED"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- REPORT GENERATION ---
from core.report import generate_pdf_report
from fastapi.responses import Response

@app.post("/report")
async def create_report(
    filename: str, 
    is_tampered: bool, 
    confidence: float
):
    try:
        # Create a result dictionary
        result = {
            "is_tampered": is_tampered,
            "confidence": confidence
        }
        
        pdf_buffer = generate_pdf_report(filename, result)
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report_{filename}.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from core.report import generate_hashing_report

@app.post("/report/hashing")
async def create_hashing_report(
    filename: str, 
    is_authentic: bool, 
    distance: int,
    original_hash: str,
    suspect_hash: str
):
    try:
        result = {
            "is_authentic": is_authentic,
            "distance": distance,
            "original_hash": original_hash,
            "suspect_hash": suspect_hash
        }
        
        pdf_buffer = generate_hashing_report(filename, result)
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=integrity_report_{filename}.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
