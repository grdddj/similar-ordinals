from pathlib import Path

HERE = Path(__file__).parent

img_folder = HERE / "images"
image_paths = [str(path) for path in img_folder.glob("*.jpg")]

hash_size = 16
db_file = HERE / f"average_hash_db_{hash_size}.json"
