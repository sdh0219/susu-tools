"""
Depth estimation module using Depth Anything V2.
Falls back to a simple gradient-based depth if the model is not available.
"""

import numpy as np
import cv2
from pathlib import Path

# Try to import Depth Anything V2
_depth_model = None
_model_loaded = False

def load_depth_model():
    """Load Depth Anything V2 model. Call once at startup."""
    global _depth_model, _model_loaded
    try:
        from depth_anything_v2.dpt import DepthAnythingV2
        import torch

        model_configs = {
            'depth_anything_v2_vitl.pth': {'encoder': 'vitl', 'features': 256, 'out_channels': [256, 512, 1024, 1024]},
            'depth_anything_v2_vitb.pth': {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]},
            'depth_anything_v2_vits.pth': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
        }

        # Try to find model weights
        model_dir = Path(__file__).parent / 'checkpoints'
        model_dir.mkdir(exist_ok=True)

        for model_name, config in model_configs.items():
            model_path = model_dir / model_name
            if model_path.exists():
                print(f"Loading Depth Anything V2 model: {model_name}")
                model = DepthAnythingV2(**config)
                model.load_state_dict(torch.load(str(model_path), map_location='cpu', weights_only=True))
                model = model.to('cuda' if torch.cuda.is_available() else 'cpu').eval()
                _depth_model = model
                _model_loaded = True
                print(f"Depth model loaded successfully on {'cuda' if torch.cuda.is_available() else 'cpu'}")
                return True

        print("No Depth Anything V2 checkpoint found. Using fallback depth estimation.")
        print(f"Download a checkpoint to {model_dir} from https://huggingface.co/depth-anything/Depth-Anything-V2-Large")
        return False

    except ImportError:
        print("Depth Anything V2 not installed. Using fallback depth estimation.")
        print("Install with: pip install depth-anything-v2")
        return False
    except Exception as e:
        print(f"Error loading depth model: {e}. Using fallback.")
        return False


def estimate_depth_fallback(frame: np.ndarray) -> np.ndarray:
    """
    Fallback depth estimation using image gradients and center bias.
    Provides a rough depth map for testing without the full model.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)

    # Gradient-based depth (edges are closer)
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    gradient_mag = np.sqrt(grad_x**2 + grad_y**2)

    # Invert: high gradient = edges = closer objects
    depth = 255 - np.clip(gradient_mag * 2, 0, 255)

    # Add center bias (center of image tends to be further away in typical shots)
    h, w = depth.shape
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    center_x, center_y = w / 2, h / 2
    dist_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
    max_dist = np.sqrt(center_x**2 + center_y**2)
    center_bias = (dist_from_center / max_dist) * 80

    # Combine
    depth = np.clip(depth * 0.6 + center_bias * 0.4, 0, 255)

    # Apply Gaussian blur for smoothness
    depth = cv2.GaussianBlur(depth, (15, 15), 0)

    # Normalize to 0-255
    depth = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)

    return depth.astype(np.uint8)


def smooth_depth(depth: np.ndarray) -> np.ndarray:
    """
    Smooth depth map with edge-preserving filter.
    Removes noise while keeping object boundaries sharp.
    """
    # Bilateral filter: smooths while preserving edges
    depth_u8 = depth.astype(np.uint8)
    smoothed = cv2.bilateralFilter(depth_u8, d=9, sigmaColor=75, sigmaSpace=75)
    # Additional Gaussian blur for overall smoothness
    smoothed = cv2.GaussianBlur(smoothed, (5, 5), 0)
    return smoothed


def estimate_depth(frame: np.ndarray) -> np.ndarray:
    """
    Estimate depth map from a single RGB frame.
    Uses Depth Anything V2 if available, otherwise falls back to gradient-based estimation.
    Applies smoothing for better parallax layer separation.
    """
    global _depth_model, _model_loaded

    if _model_loaded and _depth_model is not None:
        try:
            import torch
            # Depth Anything expects RGB input
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            depth = _depth_model.infer_image(rgb, 518)  # 518 is the default input size
            # Normalize to 0-255
            depth = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
            depth = depth.astype(np.uint8)
            # Apply edge-preserving smooth for clean layer separation
            depth = smooth_depth(depth)
            return depth
        except Exception as e:
            print(f"Depth model inference failed: {e}, using fallback")

    return estimate_depth_fallback(frame)
