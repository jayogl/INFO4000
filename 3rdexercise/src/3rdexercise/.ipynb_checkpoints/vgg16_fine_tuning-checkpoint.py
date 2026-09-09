import os
import torch
import torch.nn as nn
import torchvision
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader

# 1. Device Agnostic Setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# 2. Preprocessing & Data Augmentation Transforms
train_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 3. Load Datasets using ImageFolder
data_dir = "./data/exotic"  # Replace with the actual path to your exotic dataset
train_dataset = datasets.ImageFolder(root=os.path.join(data_dir, "train"), transform=train_transforms)
val_dataset = datasets.ImageFolder(root=os.path.join(data_dir, "val"), transform=val_transforms)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

class_names = train_dataset.classes
num_classes = len(class_names)
print(f"Classes: {class_names} (Total: {num_classes})")

# 4. Initialize Pretrained VGG16 Model
model = models.vgg16(weights=models.VGG16_Weights.DEFAULT)

# 5. Modify the Classifier Head for multi-class prediction matching exotic classes
# For VGG16, replacement matches the exact shape format of final layers
num_features = model.classifier[6].in_features
model.classifier[6] = nn.Linear(num_features, num_classes)

# 💡 IN FINE-TUNING:
# Do not freeze the convolutional base (model.features). All weights remain active.
# To prevent backpropagation from destroying general pretrained patterns, use a LOW learning rate.
model = model.to(device)

# 6. Loss and Optimizer
criterion = nn.CrossEntropyLoss()
# Set a much lower learning rate (e.g., 1e-5) for fine-tuning
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)

# 7. Training & Testing Loop function
def train_model(model, train_loader, val_loader, criterion, optimizer, epochs=5):
    results = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    
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
        val_loss, val_correct = 0.0, 0
        total_val = 0
        
        with torch.no_grad():
            for X, y in val_loader:
                X, y = X.to(device), y.to(device)
                outputs = model(X)
                loss = criterion(outputs, y)
                
                val_loss += loss.item() * X.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == y.data).item()
                total_val += X.size(0)
                
        epoch_val_loss = val_loss / total_val
        epoch_val_acc = val_correct / total_val
        
        results["train_loss"].append(epoch_train_loss)
        results["train_acc"].append(epoch_train_acc)
        results["val_loss"].append(epoch_val_loss)
        results["val_acc"].append(epoch_val_acc)
        
        print(f"Epoch {epoch+1}/{epochs} | "
              f"Train Loss: {epoch_train_loss:.4f} Acc: {epoch_train_acc:.4f} | "
              f"Val Loss: {epoch_val_loss:.4f} Acc: {epoch_val_acc:.4f}")
              
    return results

# 8. Train and Save Model Weights
epochs = 5  # Modify based on training budget & datasets
results = train_model(model, train_loader, val_loader, criterion, optimizer, epochs=epochs)

# Save fine-tuned weights separately
torch.save(model.state_dict(), "vgg16_fine_tuned.pth")
print("Model fine-tuned and weights saved to vgg16_fine_tuned.pth!")
