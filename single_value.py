from __future__ import annotations

import numpy as np

# pip install scikit-learn
from sklearn.decomposition import PCA

from common import features_db, image_paths

features = np.load(features_db)

# Create a PCA object with one component
pca = PCA(n_components=1)

values: list[tuple[str, float]] = []
for index, feature_vector in enumerate(features):
    print("index", index)
    print("image_paths[index]", image_paths[index])
    # Fit the PCA model to the feature vector and transform it
    reduced_feature = pca.fit_transform(feature_vector.reshape(-1, 1))
    single_val = reduced_feature[0][0]
    print(single_val)
    values.append((image_paths[index], single_val))

# Sort the values by the single value
values.sort(key=lambda x: x[1])
for value in values:
    print(value)
