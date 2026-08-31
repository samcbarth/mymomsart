#!/usr/bin/env python3
"""Static build step for Basil Artwork.

Reads artworks.json (the single source of truth) and generates:
  - art/<slug>.html   one SEO landing page per painting
  - art/index.html    the shop index
  - sitemap.xml
  - robots.txt

Re-run after any edit to artworks.json:  python build.py
"""
import json, html, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).parent
CAT = json.loads((ROOT / "artworks.json").read_text(encoding="utf-8"))
ARTIST = CAT["artist"]
BASE = ARTIST["site"].rstrip("/")
WORKS = CAT["works"]


def pixels(index, thumb=False):
    """Actual pixel size of an artwork file, for the img width/height attributes."""
    sub = "thumbs/" if thumb else ""
    return Image.open(ROOT / f"photos/{sub}artwork-{index + 1}.jpg").size


def breadcrumbs(w):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Basil Artwork", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Available work", "item": BASE + "/art/"},
            {"@type": "ListItem", "position": 3, "name": w["title"]},
        ],
    }, indent=2)


def dims(w):
    if w["width"] and w["height"]:
        return f'{w["width"]}x{w["height"]} in'
    return ""


def subtitle(w):
    bits = [w["medium"], dims(w), str(w["year"]) if w["year"] else ""]
    return " &middot; ".join(b for b in bits if b)


def price_label(w):
    if w["status"] == "sold":
        return "Sold"
    if w["price"]:
        return f'${w["price"]:,}'
    return "Price on request"


def cta(w):
    """Buy button when a Stripe link exists, otherwise an inquiry mailto."""
    if w["status"] == "sold":
        return '<span class="buy-btn buy-btn--sold">Sold</span>'
    if w["checkoutUrl"]:
        return f'<a class="buy-btn" href="{html.escape(w["checkoutUrl"])}">Purchase &mdash; {price_label(w)}</a>'
    subj = f'Inquiry: {w["title"]}'
    body = f'Hi Lisa, I am interested in {w["title"]}. Is it still available?'
    href = f'mailto:{ARTIST["email"]}?subject={subj}&body={body}'.replace(" ", "%20")
    return f'<a class="buy-btn" href="{html.escape(href)}">Inquire about this piece</a>'


def jsonld(w):
    offer = {
        "@type": "Offer",
        "availability": "https://schema.org/InStock" if w["status"] == "available" else "https://schema.org/SoldOut",
        "priceCurrency": "USD",
        "url": f'{BASE}/art/{w["slug"]}.html',
    }
    if w["price"]:
        offer["price"] = w["price"]
    data = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": w["title"],
        "artform": "Painting",
        "artMedium": w["medium"],
        "artworkSurface": "Canvas",
        "image": f'{BASE}/photos/artwork-{w["index"] + 1}.jpg',
        "url": f'{BASE}/art/{w["slug"]}.html',
        "creator": {
            "@type": "Person",
            "name": ARTIST["name"],
            "url": BASE,
            "sameAs": [ARTIST["instagram"]],
        },
        "offers": offer,
    }
    if w["year"]:
        data["dateCreated"] = str(w["year"])
    if w["width"] and w["height"]:
        data["width"] = {"@type": "QuantitativeValue", "value": w["width"], "unitCode": "INH"}
        data["height"] = {"@type": "QuantitativeValue", "value": w["height"], "unitCode": "INH"}
    return json.dumps(data, indent=2)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} &mdash; Original Painting by Lisa Barth | Basil Artwork</title>
  <meta name="description" content="{meta_desc}" />
  <link rel="canonical" href="{base}/art/{slug}.html" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta property="og:type" content="product" />
  <meta property="og:title" content="{title} &mdash; original painting by Lisa Barth" />
  <meta property="og:description" content="{meta_desc}" />
  <meta property="og:image" content="{base}/photos/artwork-{img}.jpg" />
  <meta property="og:url" content="{base}/art/{slug}.html" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../styles.css" />
  <script type="application/ld+json">{ld}</script>
  <script type="application/ld+json">{crumbs}</script>
</head>
<body class="art-page">

  <nav id="nav">
    <a class="nav-logo" href="../index.html">Basil Artwork</a>
    <div class="nav-links">
      <a href="../index.html#gallery">Gallery</a>
      <a href="index.html">Collect</a>
      <a href="../index.html#my-mom">My Mom</a>
    </div>
  </nav>

  <main class="art-detail">
    <a class="art-back" href="index.html">&larr; All available work</a>
    <div class="art-detail-inner">
      <div class="art-detail-img">
        <img src="../photos/artwork-{img}.jpg" width="{img_w}" height="{img_h}" alt="{title}, {subtitle_plain}, by Lisa Barth" />
      </div>
      <div class="art-detail-info">
        <p class="section-eyebrow">Original painting</p>
        <h1>{title}</h1>
        <p class="art-meta">{subtitle}</p>
        <p class="art-price">{price}</p>
        <p class="art-blurb">{blurb}</p>
        {cta}
        <p class="art-note">One of a kind. Signed by the artist. Ships from the North Dallas studio &mdash; local pickup and delivery welcome.</p>
      </div>
    </div>
  </main>

  <footer>
    <span>&copy; 2026 Basil Artwork</span>
    <div class="footer-contact">
      <a href="mailto:{email}">{email}</a>
      <a href="{ig}" target="_blank" rel="noopener">@basilartwork</a>
    </div>
  </footer>

  <!-- HubSpot tracking: page analytics, and ties form submissions to the
       pages someone browsed before signing up. -->
  <script type="text/javascript" id="hs-script-loader" async defer src="//js.hs-scripts.com/20693956.js"></script>

</body>
</html>
"""

BLURB = (
    "An original acrylic work by Lisa Barth, built up in poured and layered colour and then "
    "scraped back to reveal what sits underneath. Her florals are not copies of anything in "
    "nature &mdash; they are composites of many forms, fused into something familiar and "
    "entirely her own. Painted by hand in a North Dallas studio."
)


def build_pages():
    out = ROOT / "art"
    out.mkdir(exist_ok=True)
    for w in WORKS:
        d = dims(w)
        desc = (
            f'{w["title"]} - original {w["medium"].lower()}'
            + (f', {d},' if d else "")
            + f' by Dallas artist Lisa Barth. {price_label(w)}. One of a kind, available direct from the studio.'
        )
        (out / f'{w["slug"]}.html').write_text(
            PAGE.format(
                title=html.escape(w["title"]),
                slug=w["slug"],
                img=w["index"] + 1,
                subtitle=subtitle(w),
                subtitle_plain=html.escape(subtitle(w).replace("&middot;", "-")),
                meta_desc=html.escape(desc),
                price=price_label(w),
                cta=cta(w),
                blurb=BLURB,
                ld=jsonld(w),
                crumbs=breadcrumbs(w),
                img_w=pixels(w["index"])[0],
                img_h=pixels(w["index"])[1],
                base=BASE,
                email=ARTIST["email"],
                ig=ARTIST["instagram"],
            ),
            encoding="utf-8",
        )
    print(f"built {len(WORKS)} artwork pages")


GALLERY_CARD = """        <figure class="art-card" data-index="{index}" data-slug="{slug}" data-price="{price_raw}" data-status="{status}"
          data-title="{title}"
          data-desc="{subtitle}">
          <div class="img-wrap">
            <img src="photos/thumbs/artwork-{img}.jpg" width="{tw}" height="{th}" alt="{alt}" loading="lazy" />
          </div>
          <a class="card-price" href="art/{slug}.html">{price} &middot; view details</a>
        </figure>

"""


def build_gallery():
    """Rewrite the home-page gallery grid from the catalog so the two cannot drift."""
    index = ROOT / "index.html"
    s = index.read_text(encoding="utf-8")
    cards = "".join(
        GALLERY_CARD.format(
            index=w["index"],
            slug=w["slug"],
            img=w["index"] + 1,
            title=html.escape(w["title"]),
            subtitle=subtitle(w),
            alt=html.escape(f'{w["title"]} by Lisa Barth'),
            price=price_label(w),
            price_raw=w["price"] or "",
            status=w["status"],
            tw=pixels(w["index"], thumb=True)[0],
            th=pixels(w["index"], thumb=True)[1],
        )
        for w in WORKS
    )
    # Anchor on the grid open tag and the block that always follows it, so the
    # slice can never swallow (or leave behind) part of the card list.
    open_tag = '<div class="gallery-grid">'
    start = s.index(open_tag) + len(open_tag)
    end = s.rindex("      </div>", start, s.index('<div class="ig-cta">'))
    s = s[:start] + "\n\n" + cards + s[end:]
    index.write_text(s, encoding="utf-8")
    print(f"rebuilt home gallery ({len(WORKS)} cards)")


SHOP_CARD = """        <a class="shop-card{sold}" href="{slug}.html">
          <div class="img-wrap"><img src="../photos/thumbs/artwork-{img}.jpg" width="{tw}" height="{th}" alt="{title} by Lisa Barth" loading="lazy" /></div>
          <div class="shop-card-info">
            <h3>{title}</h3>
            <p class="shop-card-meta">{subtitle}</p>
            <p class="shop-card-price">{price}</p>
          </div>
        </a>
"""

SHOP = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Collect Original Paintings &mdash; Basil Artwork by Lisa Barth</title>
  <meta name="description" content="Original abstract floral paintings by Dallas artist Lisa Barth, available to collect direct from the studio. Each piece is one of a kind." />
  <link rel="canonical" href="{base}/art/" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta property="og:title" content="Collect Original Paintings &mdash; Basil Artwork" />
  <meta property="og:description" content="Original abstract florals by Lisa Barth, direct from a North Dallas studio." />
  <meta property="og:image" content="{base}/photos/artwork-21.jpg" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../styles.css" />
</head>
<body class="art-page">

  <nav id="nav">
    <a class="nav-logo" href="../index.html">Basil Artwork</a>
    <div class="nav-links">
      <a href="../index.html#gallery">Gallery</a>
      <a href="index.html">Collect</a>
      <a href="../index.html#my-mom">My Mom</a>
    </div>
  </nav>

  <header class="shop-hero">
    <p class="section-eyebrow">Available work</p>
    <h1>Take one home.</h1>
    <p class="shop-hero-sub">Every painting here is an original &mdash; one of a kind, signed, and sold directly by the artist. Nothing is reproduced.</p>
  </header>

  <main>
    <section class="shop-grid-wrap">
      <div class="shop-grid">
{cards}      </div>
    </section>
  </main>

  <footer>
    <span>&copy; 2026 Basil Artwork</span>
    <div class="footer-contact">
      <a href="mailto:{email}">{email}</a>
      <a href="{ig}" target="_blank" rel="noopener">@basilartwork</a>
    </div>
  </footer>

  <!-- HubSpot tracking: page analytics, and ties form submissions to the
       pages someone browsed before signing up. -->
  <script type="text/javascript" id="hs-script-loader" async defer src="//js.hs-scripts.com/20693956.js"></script>

</body>
</html>
"""


def build_shop():
    cards = "".join(
        SHOP_CARD.format(
            slug=w["slug"],
            img=w["index"] + 1,
            title=html.escape(w["title"]),
            subtitle=subtitle(w),
            price=price_label(w),
            sold=" shop-card--sold" if w["status"] == "sold" else "",
            tw=pixels(w["index"], thumb=True)[0],
            th=pixels(w["index"], thumb=True)[1],
        )
        for w in WORKS
    )
    (ROOT / "art" / "index.html").write_text(
        SHOP.format(cards=cards, base=BASE, email=ARTIST["email"], ig=ARTIST["instagram"]),
        encoding="utf-8",
    )
    print("built shop index")


def build_sitemap():
    urls = [f"{BASE}/", f"{BASE}/art/"] + [f'{BASE}/art/{w["slug"]}.html' for w in WORKS]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + body
        + "\n</urlset>\n",
        encoding="utf-8",
    )
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8"
    )
    print(f"built sitemap ({len(urls)} urls) + robots.txt")


if __name__ == "__main__":
    build_pages()
    build_gallery()
    build_shop()
    build_sitemap()
