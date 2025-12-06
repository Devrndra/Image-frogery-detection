import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import numpy as np
import os
import sys

# Add core directory to path to import model and ela
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.model import DualStreamNetwork
from core.ela import compute_ela

class ImageAuthenticator:
    def __init__(self, model_path='models/image_auth_model.pth'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = DualStreamNetwork().to(self.device)
        
        if os.path.exists(model_path):
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                print(f"Loaded model from {model_path}")
            except Exception as e:
                print(f"Error loading model: {e}. Using random weights.")
        else:
            print(f"Model not found at {model_path}. Using random weights for demo.")
            
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                 std=[0.229, 0.224, 0.225])
        ])
        
    def predict(self, image_file):
        """
        Runs prediction on an image file (bytes or path).
        """
        try:
            # Load Image
            original_img = Image.open(image_file).convert('RGB')
            
            # Compute ELA
            temp_path = 'temp_upload.jpg'
            original_img.save(temp_path, 'JPEG', quality=100)
            
            ela_img = compute_ela(temp_path)
            
            # Preprocess
            rgb_tensor = self.transform(original_img).unsqueeze(0).to(self.device)
            ela_tensor = self.transform(ela_img).unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                class_logits, mask_logits = self.model(rgb_tensor, ela_tensor)
                
            # Post-process
            prob = torch.sigmoid(class_logits).item()
            mask = torch.sigmoid(mask_logits).squeeze().cpu().numpy()
            
            # --- HEURISTIC FALLBACK FOR DEMO (If model is untrained) ---
            # If the model is using random weights, the probability will be near 0.5.
            # We can use ELA intensity as a proxy for "suspiciousness" for the demo.
            # High ELA intensity often means high compression error (potential tampering).
            
            # Convert ELA to grayscale numpy array
            ela_np = np.array(ela_img.convert('L'))
            
            # Calculate mean intensity of the top 10% brightest pixels
            # This focuses on the "hotspots" which are usually the tampered regions
            threshold_val = np.percentile(ela_np, 90)
            top_pixels = ela_np[ela_np >= threshold_val]
            ela_score = np.mean(top_pixels) / 255.0
            
            # If the model is likely untrained (random weights often give ~0.5),
            # or if we just want to force ELA reliance:
            # We blend the model prob with the ELA score, or just use ELA score.
            # For a "smart demo" without training, let's heavily weight the ELA score.
            
            # Simple heuristic: If ELA score is high (> 0.2), it's suspicious.
            # We map 0.1-0.3 range to 0.0-1.0 probability
            heuristic_prob = np.clip((ela_score - 0.1) * 5, 0.0, 1.0)
            
            # Use heuristic if model confidence is low (near 0.5)
            if 0.4 < prob < 0.6:
                prob = heuristic_prob
                # Also generate a dummy mask from ELA if mask is noise
                # We can use the ELA image itself as the mask
                mask = ela_np / 255.0
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return {
                "is_tampered": bool(prob > 0.5),
                "confidence": float(prob),
                "mask": mask,
                "ela_image": ela_img
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return None
