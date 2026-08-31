#!/usr/bin/env python3
"""Create a Stripe Payment Link for every priced, available painting.

The site is static and lives on GitHub Pages, so there is no backend to run a
checkout session. Payment Links solve that: each one is a hosted Stripe
checkout page, so the only thing the site needs is a URL.

Reads the key from the STRIPE_SECRET_KEY environment variable. Use a
restricted key with write access to Products, Prices and Payment Links only -
never a full secret key, and never commit it.

    setx STRIPE_SECRET_KEY "rk_live_..."      # once, in a new shell after

    python make_payment_links.py --dry-run    # show what would be created
    python make_payment_links.py              # create them
    python build.py                           # regenerate the pages

Safe to re-run: a work that already has a checkoutUrl is skipped, so an
interrupted run resumes rather than creating duplicates.
"""
import argparse, json, os, pathlib, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).parent
CATALOG = ROOT / "artworks.json"
API = "https://api.stripe.com/v1"


def call(path, key, data=None, idempotency=None):
    url = f"{API}/{path}"
    body = urllib.parse.urlencode(data, doseq=True).encode() if data else None
    req = urllib.request.Request(url, data=body)
    req.add_header("Authorization", f"Bearer {key}")
    if idempotency:
        req.add_header("Idempotency-Key", idempotency)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read()).get("error", {})
        raise SystemExit(f"Stripe error on {path}: {detail.get('message', e)}")


def shipping_countries():
    # Originals ship from Texas. Start with the US and Canada; widen later if
    # the artist is willing to deal with customs paperwork.
    return ["US", "CA"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key and not args.dry_run:
        sys.exit(
            "STRIPE_SECRET_KEY is not set.\n"
            "Create a restricted key in Stripe (Products, Prices, Payment Links: write),\n"
            'then:  setx STRIPE_SECRET_KEY "rk_live_..."  and open a new shell.'
        )
    if key.startswith("pk_"):
        sys.exit(
            "That is a publishable key. It cannot create products or payment links.\n"
            "Use a restricted key (rk_live_...) with write access to Products, Prices and Payment Links."
        )

    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    base = cat["artist"]["site"].rstrip("/")

    todo = [
        w for w in cat["works"]
        if w["price"] and w["status"] == "available" and not w["checkoutUrl"]
    ]
    skipped = [w for w in cat["works"] if not w["price"]]

    print(f"{len(todo)} paintings to list, {len(skipped)} skipped for having no price")
    if args.dry_run:
        for w in todo:
            print(f'  ${w["price"]:>5,}  {w["title"]}')
        return

    for w in todo:
        desc = f'{w["medium"]}'
        if w["width"] and w["height"]:
            desc += f', {w["width"]}x{w["height"]} in'
        if w["year"]:
            desc += f', {w["year"]}'
        desc += ". Original painting, one of a kind, signed by the artist."

        product = call("products", key, {
            "name": f'{w["title"]} - original painting by Lisa Barth',
            "description": desc,
            "images[0]": f'{base}/photos/artwork-{w["index"] + 1}.jpg',
            "url": f'{base}/art/{w["slug"]}.html',
            "metadata[slug]": w["slug"],
        }, idempotency=f'basil-product-{w["slug"]}')

        price = call("prices", key, {
            "product": product["id"],
            "currency": "usd",
            "unit_amount": w["price"] * 100,
        }, idempotency=f'basil-price-{w["slug"]}')

        link_data = {
            "line_items[0][price]": price["id"],
            "line_items[0][quantity]": 1,
            # Each painting exists once. Without this the same original could
            # be sold twice over.
            "line_items[0][adjustable_quantity][enabled]": "false",
            "after_completion[type]": "redirect",
            "after_completion[redirect][url]": f'{base}/art/{w["slug"]}.html',
            "shipping_address_collection[allowed_countries][]": shipping_countries(),
            "phone_number_collection[enabled]": "true",
            "metadata[slug]": w["slug"],
        }
        link = call("payment_links", key, link_data, idempotency=f'basil-link-{w["slug"]}')

        w["checkoutUrl"] = link["url"]
        print(f'  ${w["price"]:>5,}  {w["title"]:<28} {link["url"]}')

        # Save after every piece so an interruption never loses a live link.
        CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nDone. Now run:  python build.py")


if __name__ == "__main__":
    main()
