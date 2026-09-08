import os
import torch
import torch.nn as nn
from PIL import Image
import requests
from io import BytesIO
from torchvision import transforms, models

# 1. Device Agnostic Setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 2. Prediction Transform
# Images must match exact transformations used during original training: 
# Resize to 224, Convert to Tensor, and Normalize using ImageNet statistics.
predict_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 3. Model Re-initialization & Loading
def load_trained_model(weights_path, num_classes):
    # Load default architecture skeleton
    model = models.vgg16(weights=None)  # Load empty shell first
    num_features = model.classifier[6].in_features
    model.classifier[6] = nn.Linear(num_features, num_classes)
    
    # Load state_dict (saved weights)
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    
    model = model.to(device)
    model.eval()  # Set model to evaluation/inference mode
    return model

# 4. Image Prediction Function (Supports local paths and URLs)
def predict_image(image_source, model, class_names):
    # Load image from URL or local path
    if image_source.startswith("http://") or image_source.startswith("https://"):
        try:
            response = requests.get(image_source, timeout=10)
            img = Image.open(BytesIO(response.content)).convert("RGB")
            print("Loaded image successfully from URL.")
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return None
    else:
        if os.path.exists(image_source):
            img = Image.open(image_source).convert("RGB")
            print(f"Loaded local image: {image_source}")
        else:
            print(f"File not found: {image_source}")
            return None

    # Apply identical evaluation transformations
    img_transformed = predict_transforms(img)
    
    # Add batch dimension: shape (1, 3, 224, 224)
    img_batch = img_transformed.unsqueeze(0).to(device)
    
    # Run forward pass through frozen layers to prediction head
    with torch.no_grad():
        logits = model(img_batch)
        probabilities = torch.softmax(logits, dim=1)[0]
        predicted_idx = torch.argmax(probabilities).item()
        
    predicted_class = class_names[predicted_idx]
    confidence_score = probabilities[predicted_idx].item()
    
    print(f"\n--- PREDICTION RESULTS ---")
    print(f"Predicted Class: {predicted_class}")
    print(f"Confidence: {confidence_score:.2%}")
    print(f"All Probabilities: { {class_names[i]: float(prob) for i, prob in enumerate(probabilities)} }")
    return predicted_class, confidence_score

if __name__ == "__main__":
    # Example Execution Setup
    # Update classes to match the folders in your 'Exotic' dataset
    exotic_classes = ["bear", "lion", "tiger", "wolf"]  # Replace with your actual Exotic class names
    num_classes = len(exotic_classes)
    
    # Select path of trained weights file (either 'vgg16_feature_extraction.pth' or 'vgg16_fine_tuned.pth')
    weights_path = "vgg16_feature_extraction.pth"
    
    if os.path.exists(weights_path):
        trained_model = load_trained_model(weights_path, num_classes)
        
        # Test URL (Replace with any animal image URL)
        sample_url = "https://upload.wikimedia.org/wikipedia/commons/7/73/Lion_waiting_in_Namibia.jpg"
        predict_image(sample_url, trained_model, exotic_classes)
    else:
        print(f"Weights file '{weights_path}' not found. Run model training first!")
