#!/usr/bin/env python3
"""Create a giclée print product in Printify for every painting good enough for one.

Print size is limited by the photograph, not by wishful thinking: Printify's
print areas are 300 DPI, and these paintings were photographed at roughly
2600x3500. A size is only offered when the source covers at least 80% of the
required pixels - a slight upscale is invisible, a large one is not, and a
soft print of Lisa's work costs more in reputation than it earns.

Reads PRINTIFY_TOKEN from the environment. Writes the resulting product ids
back into artworks.json so the site can link to them.

    python make_prints.py --dry-run
    python make_prints.py
"""
import argparse, base64, json, os, pathlib, sys, time, urllib.request

ROOT = pathlib.Path(__file__).parent
READY = ROOT / "print_ready"
CATALOG = ROOT / "mymomsart" / "artworks.json"
API = "https://api.printify.com/v1"

SHOP = 28768076
BLUEPRINT = 494          # Giclée Art Print
PROVIDER = 36            # Print Pigeons

# variant id -> (label, required px, retail cents). Portrait and landscape
# versions of the same paper size.
SIZES = {
    "portrait": [
        (66037, '8x11',  (2400, 3300), 4500),
        (66039, '11x14', (3300, 4200), 6500),
    ],
    "landscape": [
        (66033, '11x8',  (3300, 2400), 4500),
        (66041, '14x11', (4200, 3300), 6500),
    ],
}

UPSCALE_FLOOR = 0.80     # allow a 25% upscale, no more


def api(path, token, data=None, method=None):
    req = urllib.request.Request(
        f"{API}/{path}",
        data=json.dumps(data).encode() if data is not None else None,
        method=method,
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    # Printify sits behind Cloudflare, which rejects urllib's default agent (403, code 1010).
    req.add_header("User-Agent", "basil-artwork-catalogue/1.0")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"Printify error on {path}: {e.code} {e.read().decode()[:400]}")


def fits(src, need):
    return src[0] >= need[0] * UPSCALE_FLOOR and src[1] >= need[1] * UPSCALE_FLOOR


def describe(w):
    bits = []
    if w["width"] and w["height"]:
        bits.append(f'The original is {w["width"]}x{w["height"]} inches')
    if w["year"]:
        bits.append(f'painted in {w["year"]}')
    origin = ", ".join(bits)
    return (
        f'A giclee fine art print of "{w["title"]}", an original acrylic painting by '
        f"Dallas artist Lisa Barth. "
        + (origin + ". " if origin else "")
        + "Lisa pours and layers acrylic, then scrapes back to reveal what sits "
        "underneath, so her florals are composites of many forms rather than copies "
        "of anything in nature. Printed on matte fine art paper with archival inks. "
        "The original painting is one of a kind and sold separately."
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    token = os.environ.get("PRINTIFY_TOKEN", "").strip()
    if not token and not args.dry_run:
        sys.exit("PRINTIFY_TOKEN is not set.")

    from PIL import Image

    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    plan, rejected = [], []

    for w in cat["works"]:
        f = READY / f'artwork-{w["index"] + 1}.jpg'
        if not f.exists():
            continue
        src = Image.open(f).size
        orient = "landscape" if src[0] > src[1] else "portrait"
        usable = [(vid, label, price) for vid, label, need, price in SIZES[orient] if fits(src, need)]
        if not usable:
            rejected.append((w["title"], src))
            continue
        plan.append((w, f, src, orient, usable))

    if args.limit:
        plan = plan[: args.limit]

    print(f"{len(plan)} paintings printable, {len(rejected)} too low resolution")
    for title, src in rejected:
        print(f"  skipped {title} ({src[0]}x{src[1]})")

    if args.dry_run:
        for w, f, src, orient, usable in plan:
            sizes = ", ".join(f'{l} ${p/100:.0f}' for _, l, p in usable)
            print(f'  {w["title"]:<28} {src[0]}x{src[1]} {orient:<9} -> {sizes}')
        return

    for w, f, src, orient, usable in plan:
        if w.get("printifyProductId"):
            print(f'  skip {w["title"]} (already created)')
            continue

        up = api("uploads/images.json", token, {
            "file_name": f'{w["slug"]}.jpg',
            "contents": base64.b64encode(f.read_bytes()).decode(),
        })

        variant_ids = [vid for vid, _, _ in usable]
        product = api(f"shops/{SHOP}/products.json", token, {
            "title": f'{w["title"]} - fine art print by Lisa Barth',
            "description": describe(w),
            "blueprint_id": BLUEPRINT,
            "print_provider_id": PROVIDER,
            "variants": [
                {"id": vid, "price": price, "is_enabled": True} for vid, _, price in usable
            ],
            "print_areas": [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{"id": up["id"], "x": 0.5, "y": 0.5, "scale": 1, "angle": 0}],
                }],
            }],
        })

        w["printifyProductId"] = product["id"]
        sizes = ", ".join(l for _, l, _ in usable)
        print(f'  {w["title"]:<28} {sizes:<12} {product["id"]}')
        CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nDone.")


if __name__ == "__main__":
    main()
