import json
import re
from typing import Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logger import get_logger

logger = get_logger("AIService")

class AIService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        
        # Initialize Gemini if available
        self.gemini_available = False
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.gemini_available = True
                logger.info("Gemini AI Client initialized.")
            except ImportError:
                logger.warning("google-generativeai package missing. Can't use Gemini API directly.")
                
        # Initialize Groq if available
        self.groq_available = False
        if self.groq_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_key)
                self.groq_available = True
                logger.info("Groq AI Client initialized.")
            except ImportError:
                logger.warning("groq package missing. Can't use Groq API directly.")

    async def generate_response(self, prompt: str, system_instruction: str = "") -> str:
        """Central method to invoke either Gemini or Groq, with simple code fallbacks."""
        if self.gemini_available:
            try:
                # Combine system instructions and prompt
                full_prompt = f"{system_instruction}\n\nUser Question:\n{prompt}" if system_instruction else prompt
                response = self.gemini_model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                logger.error(f"Gemini generation error: {e}, attempting Groq fallback")
                
        if self.groq_available:
            try:
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})
                
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.2
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"Groq generation error: {e}")
                
        # Non-AI dynamic mock fallback if no credentials or networks work
        return self._generate_rule_based_fallback(prompt, system_instruction)

    def compute_dataset_scores(self, dataset_name: str, description: str, source: str) -> Dict[str, Any]:
        """Heuristically computes dataset scores, ensuring deterministic values for SaaS stats."""
        # Simple string heuristics
        text = (dataset_name + " " + description).lower()
        
        # Calculate Base quality metrics
        metadata_quality = 90.0 if len(description) > 100 else 60.0
        if "readme" in text or "license" in text:
            metadata_quality += 10
            
        license_type = "Apache 2.0"
        if "cc0" in text or "public domain" in text:
            license_type = "CC0: Public Domain"
        elif "cc by" in text:
            license_type = "CC BY 4.0"
        elif "mit" in text:
            license_type = "MIT"
            
        trust_score = 70.0
        if source in ["Kaggle", "HuggingFace", "Zenodo"]:
            trust_score = 90.0
        elif source == "GitHub":
            trust_score = 80.0
            
        quality_score = (metadata_quality * 0.4) + (trust_score * 0.6)
        
        # Overall AI score combines factors
        overall_score = round((quality_score + trust_score) / 2, 1)
        
        return {
            "quality_score": round(quality_score, 1),
            "trust_score": round(trust_score, 1),
            "overall_ai_score": overall_score,
            "license": license_type,
            "popularity": "High" if overall_score > 80 else "Medium",
            "duplicate_ratio": 5.4 if "image" in text else 0.0,
            "missing_labels": "no" if "label" in text or "annotation" in text else "yes",
            "metadata_quality": "High" if metadata_quality > 80 else "Low"
        }

    async def get_dataset_recommendation(self, name: str, description: str) -> Dict[str, Any]:
        """Asks the AI to generate structured recommendations for this dataset."""
        prompt = f"""
        Analyze this dataset:
        Name: {name}
        Description: {description}
        
        Provide training advice as a JSON block matching this format:
        {{
            "best_use_case": "what tasks is this dataset best for",
            "recommended_model": "which NN model to train (e.g. ResNet50, YOLOv8, RoBERTa)",
            "preprocessing": "recommended image or text preprocessing steps",
            "difficulty": "Easy/Medium/Hard",
            "expected_accuracy": "estimated target accuracy (e.g., 92%)",
            "potential_issues": "what to watch out for (e.g., class imbalance, noisy images)"
        }}
        Return ONLY valid JSON.
        """
        
        system_instruction = "You are a professional Machine Learning engineer. Output JSON only."
        response_text = await self.generate_response(prompt, system_instruction)
        
        try:
            # Find the JSON block
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
            
        # Mock fallback recommendations if JSON decoding failed or offline
        return {
            "best_use_case": "Classification & Object Localization",
            "recommended_model": "YOLOv8-Medium" if "image" in name.lower() else "ResNet-50",
            "preprocessing": "Resize to 224x224, normalize pixel values to [0,1], perform random horizontal flip data augmentation.",
            "difficulty": "Medium",
            "expected_accuracy": "89.5%",
            "potential_issues": "Possible class imbalance or background lighting variation."
        }

    async def chat_with_dataset(self, name: str, description: str, chat_history: List[Dict[str, str]], user_message: str) -> str:
        """Chat helper with the dataset description injected as context."""
        context = f"""
        You are talking about the dataset: "{name}".
        Dataset Description: {description}
        
        Utilize the above context to answer user questions, explain the dataset's characteristics, or write Python scripts for downloading, preprocessing, and model training.
        """
        
        # Build chat context prompt
        history_str = ""
        for h in chat_history[-6:]:
            history_str += f"{h['role'].capitalize()}: {h['content']}\n"
            
        prompt = f"{history_str}User: {user_message}\nAssistant:"
        
        return await self.generate_response(prompt, system_instruction=context)

    def _generate_rule_based_fallback(self, prompt: str, system_instruction: str) -> str:
        """Deterministic string response generator when offline or credentials are missing."""
        prompt_lower = prompt.lower()
        if "preprocessing" in prompt_lower or "code" in prompt_lower:
            return """```python
import cv2
import numpy as np

def preprocess_image(image_path, target_size=(224, 224)):
    # 1. Load image
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # 2. Resize
    img = cv2.resize(img, target_size)
    
    # 3. Normalize values
    img = img.astype(np.float32) / 255.0
    
    # 4. Apply Channel Transpose (HWC to CHW for PyTorch)
    img = np.transpose(img, (2, 0, 1))
    return img

print("Boilerplate preprocessing pipeline initialized successfully.")
```"""
        elif "model" in prompt_lower or "train" in prompt_lower:
            return """```python
import torch
import torchvision.models as models

# Initialize pretrained ResNet model
model = models.resnet50(pretrained=True)
# Adjust classification head for our classes
num_ftrs = model.fc.in_features
model.fc = torch.nn.Linear(num_ftrs, 2) # Example: binary classification

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
print("Model initialized on device:", device)
```"""
        else:
            return f"Thank you for asking about the dataset. This dataset is optimized for advanced model architectures. Let me know if you need specific preprocessing pipelines or PyTorch code snippets."
