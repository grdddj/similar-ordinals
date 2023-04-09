from pathlib import Path

HERE = Path(__file__).parent

img_folder = HERE / "images"
image_paths = [str(path) for path in img_folder.glob("*.jpg")]

features_db = "features.npy"
average_hash_db = "avg_hash.npy"
