import os
import cv2
import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
import numpy as np
from .ela import compute_ela

class ImageAuthDataset(Dataset):
    def __init__(self, image_paths, labels, transform=None, image_size=(256, 256)):
        """
        Args:
            image_paths (list): List of file paths to images.
            labels (list): List of labels (0 for authentic, 1 for tampered).
            transform (callable, optional): Optional transform to be applied on a sample.
            image_size (tuple): Target size for resizing (width, height).
        """
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        self.image_size = image_size
        
        # Base transforms for resizing and normalization
        self.to_tensor = transforms.ToTensor()
        self.normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                              std=[0.229, 0.224, 0.225])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]

        try:
            # 1. Load Original Image
            # We use PIL to be consistent with ELA function
            original_img = Image.open(img_path).convert('RGB')
            
            # 2. Compute ELA
            # We compute ELA on the original image before resizing to capture artifacts best
            # However, for consistency in batching, we must resize eventually.
            # Ideally, ELA is computed on full resolution, then resized.
            ela_img = compute_ela(img_path)
            
            # 3. Resize both
            original_img = original_img.resize(self.image_size)
            ela_img = ela_img.resize(self.image_size)

            # 4. Apply Augmentations (if any)
            # Note: If we use random transforms, we must ensure they are applied identically
            # to both images. For now, we assume 'transform' handles this or we do it manually.
            # Here we will just convert to tensor and normalize.
            
            img_tensor = self.to_tensor(original_img)
            ela_tensor = self.to_tensor(ela_img)
            
            img_tensor = self.normalize(img_tensor)
            ela_tensor = self.normalize(ela_tensor) # ELA might need different stats, but using ImageNet is a common starting point
            
            return {
                'image': img_tensor,
                'ela': ela_tensor,
                'label': torch.tensor(label, dtype=torch.float32)
            }
            
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
            # Return a dummy tensor or handle error gracefully
            # For now, just return zeros (not ideal for training but prevents crash)
            return {
                'image': torch.zeros((3, *self.image_size)),
                'ela': torch.zeros((3, *self.image_size)),
                'label': torch.tensor(label, dtype=torch.float32)
            }

from torch.utils.data import DataLoader, random_split
import glob

def get_data_loaders(data_dir, batch_size=32, val_split=0.2, image_size=(256, 256)):
    """
    Creates DataLoaders for training and validation.
    Expected data_dir structure:
        data_dir/
            authentic/
            tampered/
    """
    authentic_dir = os.path.join(data_dir, 'authentic')
    tampered_dir = os.path.join(data_dir, 'tampered')
    
    if not os.path.exists(authentic_dir) or not os.path.exists(tampered_dir):
        print(f"Error: Data directory must contain 'authentic' and 'tampered' subdirectories.")
        return None, None

    # Gather all image paths
    # Supports common image extensions
    exts = ['*.jpg', '*.jpeg', '*.png', '*.tif']
    authentic_paths = []
    tampered_paths = []
    
    for ext in exts:
        authentic_paths.extend(glob.glob(os.path.join(authentic_dir, ext)))
        tampered_paths.extend(glob.glob(os.path.join(tampered_dir, ext)))
    
    print(f"Found {len(authentic_paths)} authentic images and {len(tampered_paths)} tampered images.")
    
    if len(authentic_paths) == 0 and len(tampered_paths) == 0:
        return None, None

    # Create full lists
    all_paths = authentic_paths + tampered_paths
    # Labels: 0 for authentic, 1 for tampered
    all_labels = [0] * len(authentic_paths) + [1] * len(tampered_paths)
    
    # Create full dataset
    full_dataset = ImageAuthDataset(all_paths, all_labels, image_size=image_size)
    
    # Split into train and val
    val_size = int(len(full_dataset) * val_split)
    train_size = len(full_dataset) - val_size
    
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    # Create DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    return train_loader, val_loader
