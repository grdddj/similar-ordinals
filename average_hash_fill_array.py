import imagehash
import numpy as np
from PIL import Image

from common import average_hash_db, image_paths

hash_size = 8

avg_hashes = []
for img_path in image_paths:
    with Image.open(img_path) as img:
        hash1 = imagehash.average_hash(img, hash_size).hash
        print("img_path", img_path)
        file_name = img_path.split("/")[-1]
        print("file_name", file_name)
        # print("hash1", hash1)
        avg_hashes.append(hash1)
avg_hashes = np.asarray(avg_hashes)

np.save(average_hash_db, avg_hashes)
