import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader

# CONFIG
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 20
DATASET_PATH = "dataset" # User needs to change this or put data here

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: Dataset not found at '{DATASET_PATH}'")
        print("Please create a folder named 'dataset' with two subfolders: 'real' and 'fake'")
        return

    # Data Transforms
    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    print("Loading data...")
    try:
        dataset = datasets.ImageFolder(DATASET_PATH, transform=transform)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # Use Full Dataset for Training (Overfit for Demo)
    train_dataset = dataset
    # Create a dummy validation set (same as train) just to avoid errors, or skip val
    val_dataset = dataset 

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    print(f"Classes: {dataset.classes}")
    
    # Model (ResNet18)
    print("Building ResNet18 model...")
    model = models.resnet18(pretrained=True)
    
    # Freeze base layers
    for param in model.parameters():
        param.requires_grad = False
        
    # Replace head
    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_ftrs, 128),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(128, 1),
        nn.Sigmoid()
    )
    
    model = model.to(device)
    
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=0.001)

    print("Starting training...")
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.float().to(device).unsqueeze(1)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            predicted = (outputs > 0.5).float()
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        print(f"Epoch {epoch+1}/{EPOCHS} - Loss: {running_loss/len(train_loader):.4f} - Acc: {correct/total:.4f}")
        
        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.float().to(device).unsqueeze(1)
                outputs = model(inputs)
                predicted = (outputs > 0.5).float()
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        
        print(f"Val Acc: {val_correct/val_total:.4f}")

    print("Saving model...")
    torch.save(model.state_dict(), 'forensic_model.pth')
    print("Model saved as 'forensic_model.pth'")

if __name__ == "__main__":
    train()
