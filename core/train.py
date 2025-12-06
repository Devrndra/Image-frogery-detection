import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from .model import DualStreamNetwork
from .data_loader import get_data_loaders
from .metrics import calculate_accuracy

def train_model(data_dir, num_epochs=10, batch_size=16, learning_rate=1e-4):
    # Device configuration
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Initialize Data Loaders
    print(f"Loading data from {data_dir}...")
    train_loader, val_loader = get_data_loaders(data_dir, batch_size=batch_size)
    
    if train_loader is None:
        print("Failed to load data. Please ensure 'data/authentic' and 'data/tampered' directories exist and contain images.")
        return

    # Initialize Model
    model = DualStreamNetwork().to(device)
    
    # Loss Functions
    criterion_cls = nn.BCEWithLogitsLoss()
    
    # Optimizer
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    print("Starting training...")

    # Training Loop
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0
        
        for i, batch in enumerate(train_loader):
            rgb = batch['image'].to(device)
            ela = batch['ela'].to(device)
            labels = batch['label'].to(device).unsqueeze(1)
            
            optimizer.zero_grad()
            
            class_logits, mask_logits = model(rgb, ela)
            
            # Calculate Loss
            loss = criterion_cls(class_logits, labels)
            
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            # Calculate training accuracy
            probs = torch.sigmoid(class_logits)
            preds = (probs > 0.5).float()
            correct_train += (preds == labels).sum().item()
            total_train += labels.size(0)
            
        epoch_loss = running_loss / len(train_loader)
        epoch_acc = correct_train / total_train
        
        # Validation
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0
        
        with torch.no_grad():
            for batch in val_loader:
                rgb = batch['image'].to(device)
                ela = batch['ela'].to(device)
                labels = batch['label'].to(device).unsqueeze(1)
                
                class_logits, mask_logits = model(rgb, ela)
                
                loss = criterion_cls(class_logits, labels)
                val_loss += loss.item()
                
                probs = torch.sigmoid(class_logits)
                preds = (probs > 0.5).float()
                correct_val += (preds == labels).sum().item()
                total_val += labels.size(0)
        
        val_loss /= len(val_loader)
        val_acc = correct_val / total_val
        
        print(f"Epoch [{epoch+1}/{num_epochs}] "
              f"Train Loss: {epoch_loss:.4f}, Train Acc: {epoch_acc:.4f} | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

    # Save Model
    os.makedirs('models', exist_ok=True)
    torch.save(model.state_dict(), 'models/image_auth_model.pth')
    print("Model saved to models/image_auth_model.pth")

if __name__ == "__main__":
    import sys
    # Default data directory
    data_path = 'data'
    
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
        
    if os.path.exists(data_path):
        train_model(data_path)
    else:
        print(f"Data directory '{data_path}' not found.")
        print("Please create a 'data' folder with 'authentic' and 'tampered' subfolders, or provide the path as an argument.")
