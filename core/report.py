from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
from datetime import datetime

def generate_pdf_report(filename, result, original_img_path=None):
    """
    Generates a PDF report for the analysis result.
    Returns a BytesIO object containing the PDF.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "Image Authentication Report")
    
    # Metadata
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, height - 100, f"Filename: {filename}")
    
    # Result Status
    c.setFont("Helvetica-Bold", 16)
    status = "TAMPERED" if result['is_tampered'] else "AUTHENTIC"
    color = (1, 0, 0) if result['is_tampered'] else (0, 0.5, 0) # Red or Green
    c.setFillColorRGB(*color)
    c.drawString(50, height - 140, f"Status: {status}")
    
    # Confidence
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 160, f"Confidence: {result['confidence']*100:.2f}%")
    
    # Images (if available)
    # We expect result to contain base64 strings or paths, but here we might need to handle 
    # passing actual image data or paths. 
    # For simplicity, let's assume we pass the paths or handle the images if they are passed.
    # Since backend/main.py has the images in memory/temp, we might need to adjust this.
    
    # For now, let's just print the text report. 
    # If we want images, we need to save them to temp files and draw them.
    
    c.drawString(50, height - 200, "Analysis Details:")
    c.setFont("Helvetica", 12)
    c.drawString(60, height - 220, "- Error Level Analysis (ELA) performed.")
    c.drawString(60, height - 240, "- Dual-Stream CNN Inference completed.")
    c.drawString(60, height - 260, "- Forgery Mask generated.")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer

def generate_hashing_report(filename, result):
    """
    Generates a PDF report for the hashing analysis result.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "Image Integrity Report")
    
    # Metadata
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, height - 100, f"Filename: {filename}")
    
    # Result Status
    c.setFont("Helvetica-Bold", 16)
    status = "AUTHENTIC" if result['is_authentic'] else "TAMPERED"
    color = (0, 0.5, 0) if result['is_authentic'] else (1, 0, 0)
    c.setFillColorRGB(*color)
    c.drawString(50, height - 140, f"Status: {status}")
    
    # Details
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 170, f"Hamming Distance: {result['distance']}")
    c.drawString(50, height - 190, f"Original Hash: {result['original_hash']}")
    c.drawString(50, height - 210, f"Suspect Hash:  {result.get('suspect_hash', 'N/A')}")
    
    c.drawString(50, height - 250, "Analysis Details:")
    c.drawString(60, height - 270, "- Perceptual Hashing (pHash) comparison.")
    c.drawString(60, height - 290, "- Integrity verification against original fingerprint.")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer
