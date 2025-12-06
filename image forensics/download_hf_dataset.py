import os
from datasets import load_dataset
from PIL import Image
from tqdm import tqdm

# Config
DATASET_ID = "yanbax/CIFAKE_autotrain_compatible"
OUTPUT_DIR = "dataset"
LIMIT = 200 # Download 200 images per class for speed (User can increase)

def save_images(dataset_split, class_name, limit):
    save_dir = os.path.join(OUTPUT_DIR, class_name)
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"Downloading {limit} {class_name} images...")
    count = 0
    for item in tqdm(dataset_split):
        if count >= limit:
            break
            
        # The dataset structure might vary, usually 'image' and 'label'
        # Check features
        try:
            img = item['image']
            label = item['label'] # 0: Fake, 1: Real (usually)
            
            # Check label mapping
            # For CIFAKE: 0 is usually Fake, 1 is Real. But let's verify if possible.
            # Assuming standard mapping. If class_name is 'Real', we want label 1.
            target_label = 1 if class_name == "Real" else 0
            
            if label == target_label:
                img.save(os.path.join(save_dir, f"{class_name}_{count}.jpg"))
                count += 1
        except Exception as e:
            print(f"Error saving image: {e}")

def download():
    print(f"Loading dataset: {DATASET_ID}...")
    try:
        # Load streaming to avoid downloading everything at once
        ds = load_dataset(DATASET_ID, split="train", streaming=True)
        
        # Save Real images (Label 1)
        save_images(ds, "Real", LIMIT)
        
        # Save Fake images (Label 0)
        save_images(ds, "Fake", LIMIT)
        
        print("\nDownload complete!")
        print(f"Images saved to: {os.path.abspath(OUTPUT_DIR)}")
        
    except Exception as e:
        print(f"Download Error: {e}")

if __name__ == "__main__":
    download()
