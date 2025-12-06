import os
import json
import subprocess
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ExifTags
import hashlib
from datetime import datetime
from scipy.fftpack import dct
from scipy.ndimage import uniform_filter, variance
import torch
import torch.nn as nn
from torchvision import transforms, models

# Load Model
MODEL_PATH = "forensic_model.pth"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None

def load_model():
    global model
    if model is not None:
        return model
        
    try:
        if os.path.exists(MODEL_PATH):
            print("Loading Deep Learning Model...")
            m = models.resnet18(pretrained=False)
            num_ftrs = m.fc.in_features
            m.fc = nn.Sequential(
                nn.Linear(num_ftrs, 128),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(128, 1),
                nn.Sigmoid()
            )
            m.load_state_dict(torch.load(MODEL_PATH, map_location=device))
            m.to(device)
            m.eval()
            model = m
            return model
    except Exception as e:
        print(f"Model Load Error: {e}")
    return None

# Preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def make_report(image_path):
    """
    Main entry point for the forensic pipeline.
    Returns a dictionary compatible with the GUI.
    """
    if not os.path.exists(image_path):
        return {"error": "File not found"}

    try:
        # 1. Load Image
        original = Image.open(image_path).convert("RGB")
        
        # 2. Run Analyses
        ela_result = perform_ela(image_path, original)
        meta_result = analyze_metadata(image_path) # Changed to use path for ExifTool
        # clone_result = detect_clones(original) # Removed per user request
        noise_result = analyze_noise_variance(original)
        ai_result = analyze_ai_artifacts(original) 
        dct_result = analyze_dct(original)
        dl_result = analyze_deep_learning(original) # New DL check
        
        # 3. Formulate Verdict
        verdict_data = calculate_verdict(ela_result, meta_result, ai_result, dct_result, noise_result, dl_result)
        
        # 4. Construct Report
        report = {
            "file": image_path,
            "tamper_probability": verdict_data["score"] / 100.0,
            "tamper_verdict": verdict_data["verdict"],
            "tamper_method": verdict_data["method"],
            "score": verdict_data["score"],
            "verdict": verdict_data["verdict"], # Duplicate for GUI compatibility
            "flags": verdict_data["flags"],
            
            "ai_detection": {
                "verdict": ai_result["verdict"],
                "score": ai_result["score"]
            },
            
            "frequency": {"hf_ratio": ai_result["hf_ratio"]}, # Backwards compat
            "noise": noise_result,
            "dct": dct_result,
            
            "ela": {
                "ela_image": ela_result["path"],
                "ela_score": ela_result["score"]
            },
            
            "exif": {
                "has_exif": meta_result["has_exif"],
                "generator": meta_result["software"],
                "raw": meta_result["raw"]
            },
            
            "details": {
                "ela": {
                    "score": ela_result["score"],
                    "ela_path": ela_result["path"]
                },
                "metadata": {
                    "camera": meta_result["camera"],
                    "software": meta_result["software"],
                    "has_exif": meta_result["has_exif"],
                    "raw_tags": meta_result["raw"]
                },
                "clones": {
                    "matches": 0,
                    "detected": False
                },
                "quantization": {
                    "quality": "Unknown",
                    "double_compressed": dct_result["double_compressed"],
                    "dct_score": dct_result["dct_score"]
                },
                "faces": {
                    "faces": 0,
                    "anomalies": 0
                },
                "lighting": {
                    "consistent": True,
                    "variance": noise_result["score"]
                },
                "ai_detection": {
                    "status": ai_result["verdict"],
                    "conf": ai_result["score"],
                    "hf_ratio": ai_result["hf_ratio"],
                    "ai_gen": ai_result["score"] > 0.5,
                    "reasons": ai_result["reasons"]
                }
            }
        }
        
        return report

    except Exception as e:
        print(f"Pipeline Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def perform_ela(path, original):
    """
    Error Level Analysis:
    Saves image at 90% quality and diffs it with original.
    """
    try:
        temp_path = "temp_ela.jpg"
        original.save(temp_path, "JPEG", quality=90)
        resaved = Image.open(temp_path).convert("RGB")
        
        ela_img = ImageChops.difference(original, resaved)
        
        # Calculate score on RAW difference (before enhancement)
        np_ela = np.array(ela_img)
        # Average difference per pixel (0-255)
        raw_score = np.mean(np_ela)
        score = raw_score / 255.0
        
        # Enhance for display
        extrema = ela_img.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff
        ela_img = ImageEnhance.Brightness(ela_img).enhance(scale)
        
        # Save ELA image for GUI
        output_path = os.path.join(os.path.dirname(path), "ela_output.png")
        ela_img.save(output_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {"path": output_path, "score": score}
    except Exception as e:
        print(f"ELA Error: {e}")
        return {"path": "", "score": 0.0}

def analyze_metadata(image_path):
    """
    Extracts metadata using ExifTool (subprocess).
    Returns dictionary with 'software', 'camera', 'raw', etc.
    """
    meta = {
        "has_exif": False,
        "software": "Unknown",
        "camera": "Unknown",
        "raw": {}
    }
    
    try:
        # Run ExifTool
        # -j: JSON output
        # -G: Group names (optional, but keeping it simple for now)
        cmd = ["exiftool", "-j", image_path]
        
        # Windows specific: prevent cmd window popping up
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                tags = data[0]
                meta["has_exif"] = True
                meta["raw"] = tags
                
                # Intelligent extraction
                # Check for various software tags
                soft_candidates = [
                    tags.get("Software"),
                    tags.get("ProcessingSoftware"),
                    tags.get("CreatorTool"),
                    tags.get("HistorySoftwareAgent")
                ]
                # Pick first non-None
                meta["software"] = next((s for s in soft_candidates if s), "Unknown")
                
                # Camera
                make = tags.get("Make", "")
                model = tags.get("Model", "")
                if make or model:
                    meta["camera"] = f"{make} {model}".strip()
                
    except Exception as e:
        print(f"ExifTool Error: {e}")
        
    return meta

def detect_clones(img):
    """
    Simple block-based hash matching for copy-move detection.
    Resizes image for performance.
    """
    try:
        # Resize for speed
        w, h = img.size
        aspect = h / w
        new_w = 256
        new_h = int(new_w * aspect)
        small = img.resize((new_w, new_h))
        gray = small.convert("L")
        
        block_size = 16
        blocks = {}
        matches = 0
        
        pixels = np.array(gray)
        
        for y in range(0, new_h - block_size, 8): # Stride 8
            for x in range(0, new_w - block_size, 8):
                block = pixels[y:y+block_size, x:x+block_size]
                
                # Ignore flat blocks (variance < 50)
                if np.var(block) < 50:
                    continue
                    
                block_hash = hashlib.md5(block.tobytes()).hexdigest()
                
                if block_hash in blocks:
                    # Filter out immediate neighbors (smooth areas)
                    prev_x, prev_y = blocks[block_hash]
                    dist = ((x - prev_x)**2 + (y - prev_y)**2)**0.5
                    if dist > block_size * 2:
                        matches += 1
                else:
                    blocks[block_hash] = (x, y)
                    
        return {"matches": matches, "detected": matches > 10} # Increased threshold
    except Exception as e:
        print(f"Clone Error: {e}")
        return {"matches": 0, "detected": False}

def analyze_noise_variance(img):
    """
    Advanced Local Noise Analysis.
    Generates a noise map to find splicing.
    """
    try:
        gray = img.convert("L")
        np_img = np.array(gray, dtype=float)
        
        # Estimate local variance using a sliding window (3x3)
        # We use a trick: Var(X) = E[X^2] - (E[X])^2
        mean = uniform_filter(np_img, size=5)
        mean_sq = uniform_filter(np_img**2, size=5)
        local_var = mean_sq - mean**2
        
        # Normalize to 0-255 for visualization
        v_min, v_max = local_var.min(), local_var.max()
        if v_max - v_min > 0:
            norm_var = 255 * (local_var - v_min) / (v_max - v_min)
        else:
            norm_var = np.zeros_like(local_var)
            
        # Save Noise Map
        noise_map = Image.fromarray(norm_var.astype(np.uint8))
        # Colorize for better visibility (Heatmap style)
        noise_map = ImageEnhance.Contrast(noise_map).enhance(2.0)
        
        output_path = os.path.join(os.path.dirname(img.filename) if hasattr(img, 'filename') else ".", "noise_map.png")
        noise_map.save(output_path)
        
        # Calculate consistency score (Variance of the local variances)
        # High variance in the noise map means some parts are noisy and others are smooth -> Splicing?
        consistency_score = np.std(local_var)
        
        return {
            "ai_noise": consistency_score,
            "noise_map": output_path,
            "score": consistency_score
        }
    except Exception as e:
        print(f"Noise Error: {e}")
        return {"ai_noise": 0.0, "score": 0.0}

def analyze_dct(img):
    """
    DCT Coefficient Analysis for Double Compression.
    """
    try:
        gray = img.convert("L")
        np_img = np.array(gray)
        h, w = np_img.shape
        
        # Crop to multiple of 8
        h = (h // 8) * 8
        w = (w // 8) * 8
        np_img = np_img[:h, :w]
        
        blocks = np_img.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
        
        # Compute DCT for each block
        dct_blocks = dct(dct(blocks, axis=1, norm='ortho'), axis=2, norm='ortho')
        
        # Analyze coefficients (e.g., at pos 1,1 or 2,2)
        # In double compressed images, the histogram of these coefficients often has periodic zeros or peaks
        coeffs = dct_blocks[:, 1, 1].flatten()
        
        # Simple histogram analysis
        hist, bins = np.histogram(coeffs, bins=100, range=(-50, 50))
        
        # Check for periodicity/anomalies in histogram (simplified Benford's law check or peak detection)
        # A simple metric: Sum of absolute differences between adjacent histogram bins
        # Spiky histogram = potential double compression
        diffs = np.abs(np.diff(hist))
        spikiness = np.mean(diffs)
        
        return {"dct_score": spikiness, "double_compressed": spikiness > 50} # Threshold needs tuning
    except Exception as e:
        print(f"DCT Error: {e}")
        return {"dct_score": 0.0, "double_compressed": False}

def analyze_ai_artifacts(img):
    """
    Advanced AI Detection using FFT Spectral Artifacts.
    AI generators (GAN/Diffusion) often leave grid-like artifacts 
    visible as peaks in the frequency domain.
    """
    try:
        gray = img.convert("L")
        np_img = np.array(gray)
        
        # 1. Compute FFT
        f = np.fft.fft2(np_img)
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1)
        
        h, w = magnitude.shape
        cy, cx = h // 2, w // 2
        
        # 2. Mask out the center (low frequencies) and main axes (natural edges)
        # Natural images have strong energy on the axes. AI artifacts are often off-axis.
        mask = np.ones_like(magnitude, dtype=bool)
        
        # Mask center
        y, x = np.ogrid[:h, :w]
        center_mask = (x - cx)**2 + (y - cy)**2 <= (min(h,w)//10)**2
        mask[center_mask] = False
        
        # Mask axes (with some width)
        mask[cy-2:cy+3, :] = False # Horizontal axis
        mask[:, cx-2:cx+3] = False # Vertical axis
        
        # 3. Detect Peaks in the remaining spectrum
        # We look for high energy points that stand out from the background
        masked_mag = magnitude.copy()
        masked_mag[~mask] = 0
        
        # Threshold: Mean + 3*StdDev
        mean = np.mean(masked_mag[mask])
        std = np.std(masked_mag[mask])
        threshold = mean + 3.5 * std # High threshold for distinct peaks
        
        peaks = np.sum(masked_mag > threshold)
        
        # 4. Calculate HF Ratio (still useful for blur)
        total_energy = np.sum(magnitude)
        low_freq_energy = np.sum(magnitude[center_mask])
        hf_ratio = (total_energy - low_freq_energy) / total_energy
        
        # Verdict Logic
        # Real images usually have < 100 significant off-axis peaks
        # AI images (especially older GANs or unrefined Diffusion) can have > 1000
        # But modern AI is better. We combine peaks + HF ratio.
        
        is_ai = False
        confidence = 0.0
        reasons = []
        
        if peaks > 500:
            is_ai = True
            confidence += 0.6
            reasons.append(f"Spectral peaks detected ({peaks}) - Grid artifacts")
        elif peaks > 200:
            confidence += 0.3
            reasons.append(f"Some spectral anomalies ({peaks})")
            
        if hf_ratio > 0.98: # Extremely high noise
            # Could be AI noise or just high ISO
            pass 
        elif hf_ratio < 0.005: # Too smooth
            is_ai = True
            confidence += 0.5
            reasons.append("Unnaturally smooth (Low HF energy)")
            
        return {
            "hf_ratio": hf_ratio,
            "peaks": int(peaks),
            "verdict": "POSSIBLE AI" if (is_ai or confidence > 0.5) else "LIKELY REAL",
            "score": min(confidence, 0.99),
            "reasons": reasons
        }
    except Exception as e:
        print(f"AI Check Error: {e}")
        return {"hf_ratio": 0.0, "peaks": 0, "verdict": "Unknown", "score": 0.0, "reasons": []}

def analyze_deep_learning(img):
    """
    Uses the trained ResNet model to predict Real vs Fake.
    """
    try:
        m = load_model()
        if m is None:
            return {"dl_score": 0.0, "verdict": "Model Not Loaded"}
            
        img_t = transform(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            output = m(img_t)
            score = output.item() # 0 = Fake, 1 = Real (based on folder order usually, but let's check)
            # Wait, ImageFolder sorts classes alphabetically: Fake (0), Real (1)
            # So output near 0 is Fake, near 1 is Real.
            
            # Convert to "Tamper Probability" (1 - Real Probability)
            tamper_prob = 1.0 - score
            
            return {
                "dl_score": tamper_prob,
                "verdict": "FAKE" if tamper_prob > 0.5 else "REAL"
            }
    except Exception as e:
        print(f"DL Error: {e}")
        return {"dl_score": 0.0, "verdict": "Error"}

def calculate_verdict(ela, meta, ai, dct, noise, dl):
    """
    Combines all metrics into a final score and verdict.
    """
    score = 0
    flags = []
    
    # --- DEEP LEARNING (Primary) ---
    if dl["verdict"] != "Model Not Loaded":
        # If model is confident (> 80% or < 20%), trust it heavily
        if dl["dl_score"] > 0.8:
            score += 80
            flags.append(f"Deep Learning Model detected FAKE ({dl['dl_score']*100:.1f}%)")
        elif dl["dl_score"] < 0.2:
            # Model thinks it's real, but we still check heuristics
            pass
        else:
            # Model uncertain, rely on heuristics
            score += int(dl["dl_score"] * 50)
    
    # --- HEURISTICS (Secondary) ---
    
    # 1. ELA Check
    if ela["score"] > 0.02: 
        score += 20
        flags.append("High compression error (Potential Resave)")
        
    # 2. Metadata Check
    suspicious_soft = ["photoshop", "gimp", "canva", "paint", "editor"]
    soft = meta["software"].lower()
    if any(s in soft for s in suspicious_soft):
        score += 30
        flags.append(f"Editing software detected: {meta['software']}")
        
    # 3. Clone Check - REMOVED
    # if clone["detected"]:
    #    score += 40
    #    flags.append(f"Cloned regions detected ({clone['matches']} matches)")
        
    # 4. AI Check (Spectral Artifacts)
    if ai["score"] > 0.5:
        score += 30
        flags.append(f"Spectral Artifacts detected")
        
    # 5. DCT Check
    if dct["double_compressed"]:
        score += 20
        flags.append("Double compression artifacts")
        
    # 6. Noise Check
    if noise["score"] > 500: 
        score += 20
        flags.append("Inconsistent noise levels")
        
    # Cap score
    score = min(score, 99)
    
    # Verdict
    if score > 70:
        verdict = "Fake / Tampered"
        method = "Deep Learning + Forensics"
    elif score > 40:
        verdict = "Suspicious"
        method = "Anomalies Detected"
    else:
        verdict = "Real / Authentic"
        method = "None"
        
    return {
        "score": score,
        "verdict": verdict,
        "method": method,
        "flags": flags
    }
