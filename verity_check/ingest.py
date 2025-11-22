import base64
import io
from pathlib import Path
from typing import List, Dict, Union
from PIL import Image
import pdf2image
import concurrent.futures

# Suppress DecompressionBombWarning for large files
Image.MAX_IMAGE_PIXELS = None

MAX_PAGES = 5

def encode_image_to_base64(image: Image.Image) -> str:
    """Converts a PIL Image to a base64 string, resizing if necessary."""
    # Resize if too large (max 2048px on longest side)
    max_size = 2048
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=75)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def process_file(file_path: str) -> List[Dict[str, Union[str, int]]]:
    """
    Processes a single file (PDF or Image) and returns a list of processed image data.
    
    Args:
        file_path: Path to the input file.
        
    Returns:
        List of dictionaries containing:
            - filename: Original filename
            - page_number: int
            - image_base64: Base64 encoded image string
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    processed_images = []
    
    img_list = []
    pages = 0
    
    if path.suffix.lower() == ".pdf":
        try:
            # Convert PDF to images (200 DPI for speed/size balance)
            images = pdf2image.convert_from_path(str(path), dpi=200)
            for i, image in enumerate(images):
                if pages > MAX_PAGES:
                    break
                img_list.append(encode_image_to_base64(image))  
                pages += 1
        except Exception as e:
            print(f"Error processing PDF {file_path}: {e}")
            return []
            
    elif path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        try:
            image = Image.open(path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            pages = 1
            img_list = [encode_image_to_base64(image)]
        except Exception as e:
            print(f"Error processing image {file_path}: {e}")
            return []
    else:
        print(f"Unsupported file format: {path.suffix}")
        return []

    processed_images.append({
                    "filename": path.name,
                    "page_number": pages,
                    "image_base64": img_list
                })
    return processed_images

def ingest_documents(file_paths: List[str]) -> List[Dict[str, Union[str, int]]]:
    """
    Ingests a list of document paths and returns processed image data.
    Uses parallel processing for speed.
    """
    all_processed_data = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(process_file, file_paths)
        
        for result in results:
            all_processed_data.extend(result)
            
    return all_processed_data
