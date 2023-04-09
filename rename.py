from pathlib import Path

HERE = Path(__file__).parent

img_folder = HERE / "images"

# rename all the files there to start with a number 0, 1, 2 ...
for i, path in enumerate(img_folder.glob("*.jpg")):
    path.rename(path.parent / f"{i}.jpg")
