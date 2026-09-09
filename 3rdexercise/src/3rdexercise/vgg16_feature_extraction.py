import os
import torch
import torch.nn as nn
import torchvision
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader

# 1. Device Agnostic Setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# 2. Preprocessing & Data Augmentation Transforms (ImageNet standard)
# Pretrained models expect images of shape (3 x H x W) normalized with ImageNet mean/std
train_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

test_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 3. Load Datasets using ImageFolder
data_dir = "./data/exotic"  # Replace with the actual path to your exotic dataset
train_dataset = datasets.ImageFolder(root=os.path.join(data_dir, "train"), transform=train_transforms)
test_dataset = datasets.ImageFolder(root=os.path.join(data_dir, "val"), transform=test_transforms)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

class_names = train_dataset.classes
num_classes = len(class_names)
print(f"Classes: {class_names} (Total: {num_classes})")

# 4. Initialize Pretrained VGG16 Model
# Loading weights using modern torchvision Weights enum API
model = models.vgg16(weights=models.VGG16_Weights.DEFAULT)

# 5. ConvNet as a FIXED Feature Extractor: Freeze convolutional base layers
# require_grad = False means weights are frozen and will not update during backpropagation
for param in model.features.parameters():
    param.requires_grad = False

# 6. Modify the Classifier Head for multi-class prediction matching exotic classes
# In VGG16, the final linear layer is located at index 6 of model.classifier Sequential
num_features = model.classifier[6].in_features
model.classifier[6] = nn.Linear(num_features, num_classes)

model = model.to(device)

# 7. Loss and Optimizer
criterion = nn.CrossEntropyLoss()
# Only pass active gradient parameters to optimizer
optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=0.001)

# 8. Training & Testing Loop function
def train_model(model, train_loader, test_loader, criterion, optimizer, epochs=5):
    results = {"train_loss": [], "train_acc": [], "test_loss": [], "test_acc": []}
    
    for epoch in range(epochs):
        model.train()
        train_loss, train_correct = 0.0, 0
        total_train = 0
        
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            
            # Forward pass
            outputs = model(X)
            loss = criterion(outputs, y)
            
            # Backward pass & Optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Track statistics
            train_loss += loss.item() * X.size(0)
            _, preds = torch.max(outputs, 1)
            train_correct += torch.sum(preds == y.data).item()
            total_train += X.size(0)
            
        epoch_train_loss = train_loss / total_train
        epoch_train_acc = train_correct / total_train
        
        # Validation evaluation
        model.eval()
        test_loss, test_correct = 0.0, 0
        total_val = 0
        
        with torch.no_grad():
            for X, y in test_loader:
                X, y = X.to(device), y.to(device)
                outputs = model(X)
                loss = criterion(outputs, y)
                
                test_loss += loss.item() * X.size(0)
                _, preds = torch.max(outputs, 1)
                test_correct += torch.sum(preds == y.data).item()
                total_val += X.size(0)
                
        epoch_test_loss = test_loss / total_val
        epoch_test_acc = test_correct / total_val
        
        results["train_loss"].append(epoch_train_loss)
        results["train_acc"].append(epoch_train_acc)
        results["test_loss"].append(epoch_test_loss)
        results["test_acc"].append(epoch_test_acc)
        
        print(f"Epoch {epoch+1}/{epochs} | "
              f"Train Loss: {epoch_train_loss:.4f} Acc: {epoch_train_acc:.4f} | "
              f"Val Loss: {epoch_test_loss:.4f} Acc: {epoch_test_acc:.4f}")
              
    return results

# 9. Train and Save Model Weights
epochs = 5  # Modify based on training budget & datasets
results = train_model(model, train_loader, test_loader, criterion, optimizer, epochs=epochs)

# Save only weights (state_dict) as recommended
torch.save(model.state_dict(), "vgg16_feature_extraction.pth")
print("Model trained and weights saved to vgg16_feature_extraction.pth!")
