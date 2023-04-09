from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50  # type: ignore

# Load a pre-trained ResNet50 CNN
model = ResNet50(
    weights="imagenet", include_top=False, input_shape=(224, 224, 3), pooling="max"
)


def compute_features(img):
    # Resize the image to match the input size of the CNN
    img = cv2.resize(img, (224, 224))
    # Preprocess the image (e.g., subtract the mean pixel value)
    img = tf.keras.applications.resnet50.preprocess_input(img)
    # Add a batch dimension to the image (required by the CNN)
    img = np.expand_dims(img, axis=0)
    # Use the CNN to extract features from the image
    features = model.predict(img)
    # Remove the batch dimension from the features
    features = np.squeeze(features)
    return features
