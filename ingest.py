#!/usr/bin/env python3
"""One-off: pull the Drive originals into the site.

- Re-renders every existing artwork-N.jpg from its higher-resolution original.
- Adds the paintings that were only in Drive as new artwork-N.jpg files.
- Regenerates thumbs.

Print masters stay out of the repo: they are only needed to upload to a
print-on-demand service, and committing 200MB of full-resolution art to a
public repo would both bloat the site and hand the files away for free.
"""
import pathlib, shutil
from PIL import Image
import imagehash
import pillow_heif

pillow_heif.register_heif_opener()

SCRATCH = pathlib.Path(__file__).parent
DRIVE = SCRATCH / "drive_raw"
REPO = SCRATCH / "mymomsart"
PHOTOS = REPO / "photos"
THUMBS = PHOTOS / "thumbs"
MASTERS = SCRATCH / "print_masters"

WEB_MAX = 2000       # longest edge for the on-page image
THUMB_MAX = 480
WEB_Q = 82

# Paintings that live only in Drive. Titles/sizes come from the filenames where
# the artist named them; the rest need naming by her.
NEW = [
    ("IMG_8165.heic", None, None, None),
    ("IMG_8170.jpg", None, None, None),
    ("IMG_8172.jpg", None, None, None),
    ("IMG_8176.jpg", None, None, None),
    ("IMG_8234.jpg", None, None, None),
    ("IMG_8283.jpg", None, None, None),
    ("IMG_8294.jpg", None, None, None),
    ("IMG_8303.jpg", None, None, None),
    ("IMG_8310.jpg", None, None, None),
    ("IMG_8509.heic", None, None, None),
    ("IMG_8604 (2).jpg", None, None, None),
    ("IMG_8605.jpg", None, None, None),
    ("IMG_8615.jpg", None, None, None),
    ("IMG_8669.jpg", None, None, None),
    ("IMG_8671.jpg", None, None, None),
    ("Lisa Barth BlueHibiscus60x48_acrylic_on_canvas.jpg", "Blue Hibiscus", (60, 48), None),
    ("Lisa Barth Geranium 40x30 2023.jpg", "Geranium", (40, 30), 2023),
    ("Two Out of the Water 20x26 2023.jpg", "Two Out of the Water", (20, 26), 2023),
    ("Water Garden 40x30 2023.jpg", "Water Garden", (40, 30), 2023),
]

# Excluded on purpose:
#   IMG_8677.jpg  - a collage of six paintings, not a single work
#   IMG_8617, "Geranium MG_1022", IMG_8511 - second shots of paintings already listed
#   *.heic twins of files already taken as .jpg


def phash(p):
    return imagehash.phash(Image.open(p).convert("RGB"), hash_size=16)


def write_web(src, dest_index):
    """Write photos/artwork-N.jpg and its thumb from a full-resolution source."""
    im = Image.open(src).convert("RGB")
    master = MASTERS / f"artwork-{dest_index}.jpg"
    if not master.exists():
        shutil.copy2(src, MASTERS / (f"artwork-{dest_index}" + src.suffix))

    web = im.copy()
    web.thumbnail((WEB_MAX, WEB_MAX), Image.LANCZOS)
    web.save(PHOTOS / f"artwork-{dest_index}.jpg", quality=WEB_Q, optimize=True, progressive=True)

    th = im.copy()
    th.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
    th.save(THUMBS / f"artwork-{dest_index}.jpg", quality=80, optimize=True)
    return web.size


def main():
    MASTERS.mkdir(exist_ok=True)
    drive_files = [f for f in DRIVE.iterdir() if f.name != "test.jpg"]
    dh = {}
    for f in drive_files:
        try:
            dh[f.name] = phash(f)
        except Exception:
            pass

    # 1. upgrade existing images where a matching original exists
    upgraded, skipped = [], []
    for i in range(1, 32):
        p = PHOTOS / f"artwork-{i}.jpg"
        cur = Image.open(p).size
        rh = phash(p)
        best = sorted(((rh - v, k) for k, v in dh.items()))
        d, name = best[0]
        if d > 30:
            skipped.append((i, d))
            continue
        src = DRIVE / name
        # only worth rewriting if the original is actually bigger
        if max(Image.open(src).size) <= max(cur):
            skipped.append((i, "original no larger"))
            continue
        new = write_web(src, i)
        upgraded.append((i, cur, new, name))

    print(f"upgraded {len(upgraded)} existing images")
    for i, cur, new, name in upgraded:
        print(f"  artwork-{i:<2} {cur[0]}x{cur[1]} -> {new[0]}x{new[1]}   from {name}")
    print(f"left alone: {skipped}")

    # 2. add the new paintings
    next_i = 32
    added = []
    for fname, title, size, year in NEW:
        src = DRIVE / fname
        if not src.exists():
            print("MISSING", fname)
            continue
        dims = write_web(src, next_i)
        added.append((next_i, fname, title, size, year, dims))
        next_i += 1

    print(f"\nadded {len(added)} new paintings as artwork-32..{next_i - 1}")
    for i, fname, title, size, year, dims in added:
        print(f"  artwork-{i:<3} {dims[0]}x{dims[1]}  {title or '(untitled)'}  <- {fname}")


if __name__ == "__main__":
    main()
