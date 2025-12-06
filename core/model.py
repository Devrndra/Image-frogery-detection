import torch
import torch.nn as nn
from torchvision import models
import torch.nn.functional as F

class DualStreamNetwork(nn.Module):
    def __init__(self, num_classes=1, pretrained=True):
        """
        Dual-Stream Network for Image Authentication with Localization.
        
        Args:
            num_classes (int): Number of output classes (1 for binary classification).
            pretrained (bool): Whether to use pretrained ResNet weights.
        """
        super(DualStreamNetwork, self).__init__()
        
        # Stream 1: RGB Image
        self.rgb_stream = models.resnet18(pretrained=pretrained)
        # We need intermediate features for U-Net like skip connections, but for simplicity
        # we'll just use the final feature map for now.
        self.rgb_features = nn.Sequential(*list(self.rgb_stream.children())[:-2]) # Output: 512 x H/32 x W/32
        
        # Stream 2: ELA Image
        self.ela_stream = models.resnet18(pretrained=pretrained)
        self.ela_features = nn.Sequential(*list(self.ela_stream.children())[:-2]) # Output: 512 x H/32 x W/32
        
        # Fusion
        self.fusion_conv = nn.Conv2d(512 * 2, 512, kernel_size=1)
        
        # Classification Head
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )
        
        # Segmentation Head (Simple FCN Decoder)
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(512, 256, kernel_size=4, stride=2, padding=1), # -> 256 x H/16 x W/16
            nn.ReLU(),
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1), # -> 128 x H/8 x W/8
            nn.ReLU(),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),  # -> 64 x H/4 x W/4
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),   # -> 32 x H/2 x W/2
            nn.ReLU(),
            nn.ConvTranspose2d(32, 1, kernel_size=4, stride=2, padding=1)     # -> 1 x H x W
        )
        
    def forward(self, rgb, ela):
        # Extract features
        rgb_feat = self.rgb_features(rgb)
        ela_feat = self.ela_features(ela)
        
        # Fuse features
        combined_feat = torch.cat((rgb_feat, ela_feat), dim=1)
        fused_feat = self.fusion_conv(combined_feat)
        
        # Classification
        pooled = self.avgpool(fused_feat)
        class_logits = self.classifier(pooled)
        
        # Segmentation
        mask_logits = self.decoder(fused_feat)
        
        return class_logits, mask_logits

if __name__ == "__main__":
    model = DualStreamNetwork()
    rgb = torch.randn(2, 3, 256, 256)
    ela = torch.randn(2, 3, 256, 256)
    cls, mask = model(rgb, ela)
    print(f"Class output: {cls.shape}")
    print(f"Mask output: {mask.shape}")
