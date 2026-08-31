#!/usr/bin/env python3
"""Publish the Printify products to the pop-up storefront.

Creating a product does not make it buyable; it has to be published to the
connected sales channel. Publishing also mints the storefront URL, which is
what the site links to, so the URL is written back into artworks.json.

Reads PRINTIFY_TOKEN from the environment.
"""
import json, os, pathlib, sys, time, urllib.request

ROOT = pathlib.Path(__file__).parent
CATALOG = ROOT / "mymomsart" / "artworks.json"
API = "https://api.printify.com/v1"
SHOP = 28768076

PUBLISH = {
    "title": True, "description": True, "images": True,
    "variants": True, "tags": True, "keyFeatures": True,
    "shipping_template": True,
}


def api(path, token, data=None):
    req = urllib.request.Request(
        f"{API}/{path}",
        data=json.dumps(data).encode() if data is not None else None,
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "basil-artwork-catalogue/1.0")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"Printify error on {path}: {e.code} {e.read().decode()[:300]}")


def main():
    token = os.environ.get("PRINTIFY_TOKEN", "").strip()
    if not token:
        sys.exit("PRINTIFY_TOKEN is not set.")

    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    todo = [w for w in cat["works"] if w.get("printifyProductId") and not w.get("printUrl")]
    print(f"publishing {len(todo)} products")

    for w in todo:
        pid = w["printifyProductId"]
        api(f"shops/{SHOP}/products/{pid}/publish.json", token, PUBLISH)
        # The storefront URL only exists once the product is published.
        detail = api(f"shops/{SHOP}/products/{pid}.json", token)
        handle = (detail.get("external") or {}).get("handle")
        if not handle:
            print(f'  {w["title"]:<28} published, no URL yet')
            continue
        w["printUrl"] = handle
        print(f'  {w["title"]:<28} {handle}')
        CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")

    done = sum(1 for w in cat["works"] if w.get("printUrl"))
    print(f"\n{done} paintings now have a print for sale")


if __name__ == "__main__":
    main()
