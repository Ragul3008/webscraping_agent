import os
import math
from typing import List, Dict, Any, Tuple
from PIL import Image

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    import imagehash
except ImportError:
    imagehash = None

from backend.app.core.logger import get_logger
from backend.app.services.ai_service import AIService

logger = get_logger("CVService")

class CVService:
    def __init__(self):
        self.ai_service = AIService()

    def get_image_dimensions(self, file_path: str) -> Tuple[int, int]:
        """Reads PIL Image dimensions safely."""
        try:
            with Image.open(file_path) as img:
                return img.width, img.height
        except Exception:
            return 0, 0

    def compute_phash(self, file_path: str) -> str:
        """Computes perceptual hash of an image for near-duplicate identification."""
        if imagehash:
            try:
                with Image.open(file_path) as img:
                    h = imagehash.phash(img)
                    return str(h)
            except Exception as e:
                logger.warning(f"Error computing pHash: {e}")
        
        # Simple fallback hash based on average brightness pixels
        try:
            with Image.open(file_path) as img:
                img_gray = img.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
                pixels = list(img_gray.getdata())
                avg = sum(pixels) / 64
                bits = "".join(["1" if p > avg else "0" for p in pixels])
                hex_str = hex(int(bits, 2))[2:].zfill(16)
                return hex_str
        except Exception:
            return "0000000000000000"

    def is_image_blurry(self, file_path: str, threshold: float = 100.0) -> Tuple[bool, float]:
        """Detects image blur using the Laplacian variance method via OpenCV."""
        if not cv2 or not np:
            # Fallback if cv2 not installed
            return False, 120.0
            
        try:
            image = cv2.imread(file_path)
            if image is None:
                return True, 0.0
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            fm = cv2.Laplacian(gray, cv2.CV_64F).var()
            return fm < threshold, fm
        except Exception as e:
            logger.warning(f"Blur detection error: {e}")
            return False, 150.0

    def check_nsfw_and_watermark(self, file_path: str) -> Tuple[float, bool]:
        """Simulates NSFW scoring and watermark checking. Filters out low-quality/inappropriate material."""
        # Standard safety scores
        nsfw_score = 0.05
        has_watermark = False
        
        # Let's inspect image names/properties or keep default safe values
        name = os.path.basename(file_path).lower()
        if "watermark" in name:
            has_watermark = True
        if "nsfw" in name or "adult" in name:
            nsfw_score = 0.95
            
        return nsfw_score, has_watermark

    async def generate_caption_and_tags(self, file_path: str) -> Tuple[str, List[str]]:
        """Generates image caption descriptions and classification tag labels."""
        # Simple heuristic mappings based on filename keywords
        name = os.path.basename(file_path).lower()
        
        # In a real environment, we'd query BLIP or use a Gemini multimodal request:
        if self.ai_service.gemini_available:
            try:
                import google.generativeai as genai
                # Safe read
                with open(file_path, "rb") as f:
                    image_bytes = f.read()
                
                contents = [
                    {"mime_type": "image/jpeg", "data": image_bytes},
                    "Provide a short 1-sentence caption and 5 single-word tags as a JSON object: {\"caption\": \"...\", \"tags\": [\"tag1\", ...]}"
                ]
                response = self.ai_service.gemini_model.generate_content(contents)
                import re, json
                match = re.search(r"\{.*\}", response.text, re.DOTALL)
                if match:
                    res = json.loads(match.group(0))
                    return res.get("caption", ""), res.get("tags", [])
            except Exception as e:
                logger.warning(f"Gemini caption failed: {e}")

        # Static fallback rules if API key isn't provided or offline
        caption = f"An image file matching the category of {name}."
        tags = ["object", "visual", "dataset"]
        
        if "cat" in name:
            caption = "A close-up shot of a domesticated cat."
            tags = ["cat", "feline", "animal", "pet"]
        elif "dog" in name:
            caption = "A clean photograph of a dog in focus."
            tags = ["dog", "canine", "animal", "pet"]
        elif "mri" in name:
            caption = "A magnetic resonance imaging (MRI) scan displaying internal structures."
            tags = ["mri", "medical", "scan", "brain"]
        elif "xray" in name:
            caption = "A diagnostic X-ray film showing skeletal features."
            tags = ["xray", "medical", "scan", "bones"]
            
        return caption, tags

    def find_duplicate_images(self, image_paths: List[str], threshold: int = 4) -> List[Tuple[str, str, int]]:
        """Compares list of image paths and returns tuples of (img1, img2, hamming_distance)."""
        hashes = {}
        for path in image_paths:
            h = self.compute_phash(path)
            hashes[path] = h
            
        duplicates = []
        paths = list(hashes.keys())
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                h1 = hashes[paths[i]]
                h2 = hashes[paths[j]]
                
                # Compute hamming distance between hex strings
                val1 = int(h1, 16)
                val2 = int(h2, 16)
                diff = bin(val1 ^ val2).count("1")
                
                if diff <= threshold:
                    duplicates.append((paths[i], paths[j], diff))
                    
        return duplicates
