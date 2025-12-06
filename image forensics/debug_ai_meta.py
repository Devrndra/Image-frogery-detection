from PIL import Image, ExifTags
import sys

img_path = r"C:/Users/devau/.gemini/antigravity/brain/54a56b80-24db-4719-ab92-e77c7268cf85/uploaded_image_1764336157101.png"

try:
    img = Image.open(img_path)
    print(f"Format: {img.format}")
    print(f"Info: {img.info}")
    
    exif = img.getexif()
    if exif:
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            print(f"{tag}: {value}")
    else:
        print("No EXIF data found via getexif()")
        
except Exception as e:
    print(f"Error: {e}")
