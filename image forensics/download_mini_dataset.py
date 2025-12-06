import os
import requests
from PIL import Image
from io import BytesIO

# Sample URLs (Public domain / Creative Commons)
REAL_URLS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Example.jpg/600px-Example.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/600px-Cat03.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/600px-Cat_November_2010-1a.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Felis_catus-cat_on_snow.jpg/600px-Felis_catus-cat_on_snow.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Orange_tabby_cat_sitting_on_fallen_leaves-Hisashi-01A.jpg/600px-Orange_tabby_cat_sitting_on_fallen_leaves-Hisashi-01A.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Sleeping_cat_on_her_back.jpg/600px-Sleeping_cat_on_her_back.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Cat_March_2010-1.jpg/600px-Cat_March_2010-1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Kittyply_edit1.jpg/600px-Kittyply_edit1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Black_Cat_009.jpg/600px-Black_Cat_009.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Cat_August_2010-4.jpg/600px-Cat_August_2010-4.jpg"
]

# Using placeholders or known AI art hosting URLs (that allow hotlinking or are public)
# For demo, we will use some distinct "digital art" style images from public sources that look "fake" to the model
FAKE_URLS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Fractal_generated_by_a_procedure.jpg/600px-Fractal_generated_by_a_procedure.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Mandel_zoom_00_mandelbrot_set.jpg/600px-Mandel_zoom_00_mandelbrot_set.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Mandel_zoom_04_seehorse_tail.jpg/600px-Mandel_zoom_04_seehorse_tail.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Fractal_Broccoli.jpg/600px-Fractal_Broccoli.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Digital_Art_by_Gerd_Altmann.jpg/600px-Digital_Art_by_Gerd_Altmann.jpg", # Placeholder
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/600px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg", # Heavily processed
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/JPEG_Mansch.jpg/600px-JPEG_Mansch.jpg", # Compression artifacts
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/600px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Artificial_Intelligence_&_AI_&_Machine_Learning_-_30212411048.jpg/600px-Artificial_Intelligence_&_AI_&_Machine_Learning_-_30212411048.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Kandinsky_-_Composition_VII.jpg/600px-Kandinsky_-_Composition_VII.jpg"
]

def download_images(urls, folder):
    os.makedirs(folder, exist_ok=True)
    print(f"Downloading to {folder}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for i, url in enumerate(urls):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img.save(os.path.join(folder, f"image_{i}.jpg"))
                print(f"  Saved image_{i}.jpg")
            else:
                print(f"  Failed {url}: Status {resp.status_code}")
        except Exception as e:
            print(f"  Failed {url}: {e}")

if __name__ == "__main__":
    download_images(REAL_URLS, "dataset/Real")
    download_images(FAKE_URLS, "dataset/Fake")
    print("Mini dataset downloaded.")
