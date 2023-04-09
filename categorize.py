import cv2
import numpy as np

from common import features_db, image_paths
from compute_features import compute_features

# Load all the images in the dataset and compute their features
# using an image feature extraction algorithm
features = []
for img_path in image_paths:
    img = cv2.imread(img_path)
    print("img_path", img_path)
    feature = compute_features(img)
    print("feature", feature)
    print("feature", len(feature))
    features.append(feature)
features = np.asarray(features)
print("features", features)

np.save(features_db, features)
