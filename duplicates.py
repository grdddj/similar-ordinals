import os

import imagehash
import numpy as np
from PIL import Image


class DuplicateRemover:
    def __init__(self, dirname, hash_size=8):
        self.dirname = dirname
        self.hash_size = hash_size

    def find_duplicates(self):
        """
        Find and Delete Duplicates
        """

        fnames = os.listdir(self.dirname)
        hashes = {}
        duplicates = []
        print("Finding Duplicates Now!\n")
        for image in fnames:
            with Image.open(os.path.join(self.dirname, image)) as img:
                temp_hash = imagehash.average_hash(img, self.hash_size)
                if temp_hash in hashes:
                    print(
                        "Duplicate {} \nfound for Image {}!\n".format(
                            image, hashes[temp_hash]
                        )
                    )
                    duplicates.append(image)
                else:
                    hashes[temp_hash] = image

    def find_similar(self, location, similarity=80):
        threshold = 1 - similarity / 100
        diff_limit = int(threshold * (self.hash_size**2))
        print("diff_limit", diff_limit)

        with Image.open(location) as img:
            hash1 = imagehash.average_hash(img, self.hash_size).hash
            print("hash1", hash1)

        print("Finding Similar Images to {} Now!\n".format(location))
        for image in os.listdir(self.dirname):
            with Image.open(os.path.join(self.dirname, image)) as img:
                hash2 = imagehash.average_hash(img, self.hash_size).hash

                if np.count_nonzero(hash1 != hash2) <= diff_limit:
                    print(
                        "{} image found {}% similar to {}".format(
                            image, similarity, location
                        )
                    )


if __name__ == "__main__":
    dirname = "images"

    # Remove Duplicates
    dr = DuplicateRemover(dirname)
    # dr.find_duplicates()

    # Find Similar Images
    dr.find_similar("images/304.jpg", 99)
