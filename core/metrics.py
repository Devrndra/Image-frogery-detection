import torch
import numpy as np

def calculate_accuracy(outputs, labels, threshold=0.5):
    """
    Calculate binary classification accuracy.
    
    Args:
        outputs (torch.Tensor): Logits from the model (B, 1).
        labels (torch.Tensor): Ground truth labels (B, 1).
        threshold (float): Threshold for converting probabilities to binary predictions.
        
    Returns:
        float: Accuracy score.
    """
    probs = torch.sigmoid(outputs)
    preds = (probs > threshold).float()
    correct = (preds == labels).float().sum()
    return (correct / labels.size(0)).item()

def calculate_iou(masks_pred, masks_true, threshold=0.5, epsilon=1e-6):
    """
    Calculate Intersection over Union (IoU) for segmentation masks.
    
    Args:
        masks_pred (torch.Tensor): Predicted logits for masks (B, 1, H, W).
        masks_true (torch.Tensor): Ground truth masks (B, 1, H, W).
        threshold (float): Threshold for binarizing predictions.
        epsilon (float): Small value to prevent division by zero.
        
    Returns:
        float: Mean IoU score.
    """
    # Apply sigmoid and threshold
    probs = torch.sigmoid(masks_pred)
    preds = (probs > threshold).float()
    
    # Flatten
    preds = preds.view(preds.size(0), -1)
    true = masks_true.view(masks_true.size(0), -1)
    
    # Intersection and Union
    intersection = (preds * true).sum(dim=1)
    union = preds.sum(dim=1) + true.sum(dim=1) - intersection
    
    # IoU
    iou = (intersection + epsilon) / (union + epsilon)
    
    return iou.mean().item()
