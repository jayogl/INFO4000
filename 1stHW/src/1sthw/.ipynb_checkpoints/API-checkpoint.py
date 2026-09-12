import io
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
device = torch_directml.device()
class_names = ['covid', 'normal']

# Load Weights
weights = models.ResNet18_Weights.DEFAULT
model = models.resnet18(weights=weights)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, len(class_names))
model.load_state_dict(torch.load('covid_model.pth', map_location=device))
model.to(device)
model.eval()

# Inference Preprocessing Pipeline
inference_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No image file provided in request'}), 400

    file = request.files['file']
    try:
        # Read Image
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes))
        input_tensor = inference_transform(image).unsqueeze(0).to(device)

        # Model Inference
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probabilities, 1)

        result = {
            'prediction': class_names[predicted_idx.item()],
            'confidence': float(confidence.item()),
            'probabilities': {
                class_names[i]: float(probabilities[i].item())
                for i in range(len(class_names))
            }
        }
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'Failed to process image: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting Flask Backend API on http://localhost:5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)
