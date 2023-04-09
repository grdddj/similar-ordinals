# pip install faiss-cpu
import cv2
import faiss
import numpy as np

from common import features_db, image_paths
from compute_features import compute_features

features = np.load(features_db)

# Build an index of the image features using faiss
index = faiss.IndexFlatL2(features.shape[1])
index.add(features)  # type: ignore

# Load a query image and compute its features
query_img = cv2.imread("prase2.jpg")
query_feature = compute_features(query_img)

# Use the index to find the most similar images to the query image
k = 10  # number of most similar images to retrieve
D, I = index.search(np.asarray([query_feature]), k)  # type: ignore

# I contains the indices of the k most similar images in the dataset
most_similar_images = [image_paths[i] for i in I[0]]
print("most_similar_images", most_similar_images)
