import torch
import torch.nn as nn
from torchvision import models
import os

MODEL_PATH = "forensic_model.pth"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_model():
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
            # Use map_location to handle CPU/GPU mismatch
            m.load_state_dict(torch.load(MODEL_PATH, map_location=device))
            m.to(device)
            m.eval()
            print("Model loaded successfully!")
            return True
        else:
            print("Model file not found!")
            return False
    except Exception as e:
        print(f"Model Load Error: {e}")
        return False

if __name__ == "__main__":
    load_model()
