import imagehash
from PIL import Image
import os

def generate_phash(image_path):
    """Generates the perceptual hash of an image."""
    try:
        img = Image.open(image_path)
        # Use a typical hash size like 8 for a 64-bit hash
        image_hash = imagehash.phash(img, hash_size=8)
        return str(image_hash)
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def compare_hashes(original_hash_str, suspect_image_path, threshold=5):
    """
    Compares a new image hash to a known original hash.
    Returns:
        distance (int): Hamming distance
        is_authentic (bool): True if distance < threshold
    """
    try:
        original_hash = imagehash.hex_to_hash(original_hash_str)
        suspect_hash_obj = imagehash.phash(Image.open(suspect_image_path), hash_size=8)
        
        # Hamming Distance is the number of differing bits
        distance = original_hash - suspect_hash_obj
        
        return distance, distance < threshold, str(suspect_hash_obj)
    except Exception as e:
        print(f"Error comparing hashes: {e}")
        return -1, False, None

if __name__ == "__main__":
    # Test
    pass
