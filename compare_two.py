from pathlib import Path

# pip install opencv-python
# pip install scikit-image
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

HERE = Path(__file__).parent

# image1 = HERE / "prase.jpg"
# image2 = HERE / "prase2.jpg"

image1 = cv2.imread("images/193.jpg")
image2 = cv2.imread("images/197.jpg")

image1 = cv2.resize(image1, (224, 224))
image2 = cv2.resize(image2, (224, 224))

# Convert the images to grayscale
gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

# Compute the SSIM and MSE between the two grayscale images
ssim_score = ssim(gray_image1, gray_image2)
mse_score = np.mean((gray_image1 - gray_image2) ** 2)  # type: ignore

# Print the similarity scores
print("SSIM score:", ssim_score)
print("MSE score:", mse_score)
