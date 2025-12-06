import os
import numpy as np
from PIL import Image, ImageChops, ImageEnhance

def compute_ela(image_path, quality=90):
    """
    Computes the Error Level Analysis (ELA) of an image.
    
    Args:
        image_path (str): Path to the original image.
        quality (int): JPEG quality for re-compression (default: 90).
        
    Returns:
        PIL.Image: The ELA image highlighting differences.
    """
    original = Image.open(image_path).convert('RGB')
    
    # Save the image at a specific quality to a temporary buffer/file
    # We use a temporary filename in the same directory to avoid permission issues or cross-device link errors
    temp_filename = 'temp_ela_image.jpg'
    original.save(temp_filename, 'JPEG', quality=quality)
    
    # Open the compressed image
    compressed = Image.open(temp_filename)
    
    # Compute the difference between the original and compressed image
    ela_image = ImageChops.difference(original, compressed)
    
    # Calculate the extrema (min/max pixel values) to scale the brightness
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    
    # If there is no difference (max_diff is 0), we can't scale, so just return the black image
    if max_diff == 0:
        max_diff = 1
        
    scale = 255.0 / max_diff
    
    # Enhance the brightness to make the differences visible
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    
    # Clean up the temporary file
    try:
        os.remove(temp_filename)
    except OSError:
        pass
        
    return ela_image

if __name__ == "__main__":
    # Test the function if run directly
    import sys
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
        if os.path.exists(img_path):
            ela = compute_ela(img_path)
            ela.show()
            print(f"ELA computed for {img_path}")
        else:
            print(f"File not found: {img_path}")
    else:
        print("Usage: python ela.py <image_path>")
