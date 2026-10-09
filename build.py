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


def print_cta(w):
    """Prints are the affordable way in; the original stays the headline."""
    if not w.get("printUrl"):
        return ""
    return (
        f'<a class="print-btn" href="{html.escape(w["printUrl"])}" target="_blank" rel="noopener">'
        f"Or buy a fine art print, from $45</a>"
    )


INQUIRY_TYPES = [
    ("commission", "A commission"),
    ("mural", "A mural or large install"),
    ("class", "A class or workshop"),
    ("original", "Buying an original"),
    ("trade", "A designer or business project"),
    ("other", "Something else"),
]
INQUIRY_BUDGETS = [
    ("under_500", "Under $500"),
    ("500_1500", "$500 to $1,500"),
    ("1500_3000", "$1,500 to $3,000"),
    ("3000_6000", "$3,000 to $6,000"),
    ("6000_plus", "$6,000+"),
    ("not_sure", "Not sure yet"),
]


def inquiry_form(kind, artwork="", ident="inquire", eyebrow="", heading="", intro=""):
    """Shared inquiry form. inquiry.js posts it to the HubSpot 'Basil Inquiry' form."""
    types = "".join(f'<option value="{v}">{l}</option>' for v, l in INQUIRY_TYPES)
    budgets = '<option value="">Choose one</option>' + "".join(
        f'<option value="{v}">{l}</option>' for v, l in INQUIRY_BUDGETS
    )
    head = ""
    if eyebrow:
        head += f'<p class="section-eyebrow">{eyebrow}</p>'
    if heading:
        head += f"<h2>{heading}</h2>"
    if intro:
        head += f'<p class="iq-intro">{intro}</p>'
    return f"""<div class="inquiry-inner" id="{ident}">
        {head}
        <form class="inquiry-form" data-inquiry-type="{kind}" data-artwork="{html.escape(artwork)}" novalidate>
          <div class="iq-row">
            <label>Your name<input type="text" name="name" autocomplete="name" required /></label>
            <label>Email<input type="email" name="email" autocomplete="email" required /></label>
          </div>
          <div class="iq-row">
            <label>Phone (optional)<input type="tel" name="phone" autocomplete="tel" /></label>
            <label>City<input type="text" name="location" autocomplete="address-level2" /></label>
          </div>
          <div class="iq-row">
            <label>I am interested in<select name="type">{types}</select></label>
            <label>Budget range<select name="budget">{budgets}</select></label>
          </div>
          <label>Timeline<input type="text" name="timeline" placeholder="For example: before the holidays" /></label>
          <label>Tell Lisa about your project<textarea name="details" rows="4"></textarea></label>
          <input type="text" name="website" class="iq-hp" tabindex="-1" autocomplete="off" aria-hidden="true" />
          <button type="submit" class="buy-btn">Send inquiry</button>
          <p class="iq-note" role="status" aria-live="polite">Lisa will reply to you by email.</p>
        </form>
      </div>"""


def inquiry_page_form(w):
    title = html.escape(w["title"])
    if w["status"] == "sold":
        return inquiry_form(
            "commission", w["slug"], eyebrow="Like this one?",
            heading="Ask for something in its spirit.",
            intro=f"{title} has found its home. Lisa takes commissions, so tell her what you have in mind.",
        )
    if w["checkoutUrl"]:
        return inquiry_form(
            "original", w["slug"], eyebrow="Questions?",
            heading="Ask about this painting.",
            intro="Ask about condition, framing, shipping, or a custom size. Or tell Lisa about a commission.",
        )
    return inquiry_form(
        "original", w["slug"], eyebrow="Inquire",
        heading=f"Ask about {title}.",
        intro="Lisa will send size, price and shipping details. Or tell her about a commission you have in mind.",
    )


def cta(w):
    """Buy button when a Stripe link exists, otherwise a jump to the inquiry form."""
    if w["status"] == "sold":
        return '<span class="buy-btn buy-btn--sold">Sold</span>'
    if w["checkoutUrl"]:
        return f'<a class="buy-btn" href="{html.escape(w["checkoutUrl"])}">Purchase: {price_label(w)}</a>'
    return '<a class="buy-btn" href="#inquire">Inquire about this piece</a>'


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
  <title>{title}: Original Painting by Lisa Barth | Basil Artwork</title>
  <meta name="description" content="{meta_desc}" />
  <link rel="canonical" href="{base}/art/{slug}.html" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta property="og:type" content="product" />
  <meta property="og:title" content="{title}, original painting by Lisa Barth" />
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
      <a href="https://my-moms-art.printify.me/" target="_blank" rel="noopener">Prints</a>
      <a href="../commissions/">Commissions</a>
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
        <p class="art-blurb">{note}</p>
        <p class="art-blurb art-blurb--process">{blurb}</p>
        {cta}
        {print_cta}
        <p class="art-note">One of a kind. Signed by the artist. Ships from the North Dallas studio. Local pickup and delivery welcome.</p>
        <p class="art-note"><a href="../commissions/">Want something like this, sized for your wall? Commission one.</a></p>
      </div>
    </div>
    <section class="inquiry-section">
      {inquiry}
    </section>
  </main>

  <footer>
    <span>&copy; 2026 Basil Artwork</span>
{footer_links}
    <div class="footer-contact">
      <a href="mailto:{email}">{email}</a>
      <a href="{ig}" target="_blank" rel="noopener">@basilartwork</a>
    </div>
  </footer>

  <script src="../inquiry.js"></script>
  <!-- HubSpot tracking: page analytics, and ties form submissions to the
       pages someone browsed before signing up. -->
  <script type="text/javascript" id="hs-script-loader" async defer src="//js.hs-scripts.com/20693956.js"></script>

</body>
</html>
"""

BLURB = (
    "An original acrylic work by Lisa Barth, built up in poured and layered colour and then "
    "scraped back to reveal what sits underneath. Her florals are not copies of anything in "
    "nature. They are composites of many forms, fused into something familiar and "
    "entirely her own. Painted by hand in a North Dallas studio."
)


SERVICES = CAT.get("services", [])

FOOTER_LINKS = """    <nav class="footer-links" aria-label="Services">
      {links}
    </nav>"""


def footer_links(prefix):
    """Footer links to every service page. prefix is the path back to the site root."""
    return "".join(f'<a href="{prefix}{s["slug"]}/">{s["label"]}</a>' for s in SERVICES)


SERVICE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{meta}" />
  <link rel="canonical" href="{base}/{slug}/" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{meta}" />
  <meta property="og:image" content="{base}/photos/artwork-21.jpg" />
  <meta property="og:url" content="{base}/{slug}/" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../styles.css" />
  <script type="application/ld+json">{ld}</script>
</head>
<body class="art-page">

  <nav id="nav">
    <a class="nav-logo" href="../index.html">Basil Artwork</a>
    <div class="nav-links">
      <a href="../index.html#gallery">Gallery</a>
      <a href="../art/index.html">Collect</a>
      <a href="https://my-moms-art.printify.me/" target="_blank" rel="noopener">Prints</a>
      <a href="../commissions/">Commissions</a>
      <a href="../index.html#my-mom">My Mom</a>
    </div>
  </nav>

  <header class="shop-hero">
    <p class="section-eyebrow">{eyebrow}</p>
    <h1>{h1}</h1>
  </header>

  <main>
    <section class="svc-body">
{paras}
    </section>
{examples}
    <section class="inquiry-section">
      {inquiry}
    </section>
  </main>

  <footer>
    <span>&copy; 2026 Basil Artwork</span>
{footer_links}
    <div class="footer-contact">
      <a href="mailto:{email}">{email}</a>
      <a href="{ig}" target="_blank" rel="noopener">@basilartwork</a>
    </div>
  </footer>

  <script src="../inquiry.js"></script>
  <script type="text/javascript" id="hs-script-loader" async defer src="//js.hs-scripts.com/20693956.js"></script>

</body>
</html>
"""


def service_ld(s):
    data = {
        "@context": "https://schema.org",
        "@type": "ProfilePage" if s.get("about") else "Service",
        "name": s["h1"],
        "url": f'{BASE}/{s["slug"]}/',
        "description": s["meta"],
    }
    person = {
        "@type": "Person",
        "name": ARTIST["name"],
        "alternateName": ARTIST["brand"],
        "url": BASE,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Dallas",
            "addressRegion": "TX",
            "addressCountry": "US",
        },
        "sameAs": [ARTIST["instagram"], "https://northdallasart.com/lisa-barth/"],
    }
    if s.get("about"):
        data["mainEntity"] = person
    else:
        data["provider"] = person
        data["serviceType"] = s["label"]
    return json.dumps(data, indent=2)


def service_paras(s):
    out = []
    for p in s["paras"]:
        if isinstance(p, str):
            out.append(f"      <p>{html.escape(p)}</p>")
        elif "sam" in p:
            out.append(f'      <p class="svc-line">{html.escape(p["sam"])}</p>')
        else:
            out.append(
                f'      <p>{html.escape(p["link"])}</p>\n'
                f'      <p><a class="tour-btn" href="{html.escape(p["href"])}" target="_blank" rel="noopener">{html.escape(p["text"])}</a></p>'
            )
    return "\n".join(out)


def service_examples(s):
    if not s["examples"]:
        return ""
    by_slug = {w["slug"]: w for w in WORKS}
    cards = []
    for slug in s["examples"]:
        w = by_slug[slug]
        tw, th = pixels(w["index"], thumb=True)
        cards.append(
            f'''        <a class="shop-card" href="../art/{slug}.html">
          <div class="img-wrap"><img src="../photos/thumbs/artwork-{w["index"] + 1}.jpg" width="{tw}" height="{th}" alt="{html.escape(w["title"])} by Lisa Barth" loading="lazy" /></div>
          <div class="shop-card-info"><h3>{html.escape(w["title"])}</h3><p>{subtitle(w)}</p></div>
        </a>'''
        )
    return (
        f'''    <section class="shop-grid-wrap svc-examples">
      <h2 class="svc-h2">{html.escape(s.get("examples_heading", "Paintings"))}</h2>
      <div class="shop-grid">
{chr(10).join(cards)}
      </div>
    </section>'''
    )


def build_services():
    for s in SERVICES:
        d = ROOT / s["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(
            SERVICE.format(
                title=html.escape(s["title"]),
                meta=html.escape(s["meta"]),
                slug=s["slug"],
                base=BASE,
                ld=service_ld(s),
                eyebrow=html.escape(s["eyebrow"]),
                h1=html.escape(s["h1"]),
                paras=service_paras(s),
                examples=service_examples(s),
                inquiry=inquiry_form(
                    s["kind"], ident="inquire", heading=html.escape(s["form_heading"]),
                    intro="Lisa will reply to you by email.",
                ),
                footer_links=FOOTER_LINKS.format(links=footer_links("../")),
                email=ARTIST["email"],
                ig=ARTIST["instagram"],
            ),
            encoding="utf-8",
        )
    print(f"built {len(SERVICES)} service pages")


def build_pages():
    out = ROOT / "art"
    out.mkdir(exist_ok=True)
    for w in WORKS:
        d = dims(w)
        desc = (
            f'{w["title"]} - original {w["medium"].lower()}'
            + (f', {d},' if d else "")
            + f' by Dallas artist Lisa Barth. {w.get("note", "")} {price_label(w)}.'
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
                print_cta=print_cta(w),
                inquiry=inquiry_page_form(w),
                blurb=BLURB,
                note=w.get("note", ""),
                ld=jsonld(w),
                crumbs=breadcrumbs(w),
                img_w=pixels(w["index"])[0],
                img_h=pixels(w["index"])[1],
                base=BASE,
                email=ARTIST["email"],
                ig=ARTIST["instagram"],
                footer_links=FOOTER_LINKS.format(links=footer_links("../")),
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
  <title>Collect Original Paintings: Basil Artwork by Lisa Barth</title>
  <meta name="description" content="Original abstract floral paintings by Dallas artist Lisa Barth, available to collect direct from the studio. Each piece is one of a kind." />
  <link rel="canonical" href="{base}/art/" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta property="og:title" content="Collect Original Paintings: Basil Artwork" />
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
      <a href="https://my-moms-art.printify.me/" target="_blank" rel="noopener">Prints</a>
      <a href="../commissions/">Commissions</a>
      <a href="../index.html#my-mom">My Mom</a>
    </div>
  </nav>

  <header class="shop-hero">
    <p class="section-eyebrow">Available work</p>
    <h1>Take one home.</h1>
    <p class="shop-hero-sub">Every painting here is an original: one of a kind, signed, and sold directly by the artist. Most are also available as fine art prints.</p>
  </header>

  <main>
    <section class="shop-grid-wrap">
      <div class="shop-grid">
{cards}      </div>
    </section>
  </main>

  <footer>
    <span>&copy; 2026 Basil Artwork</span>
{footer_links}
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


def build_home_inquiry():
    """Regenerate the home-page commissions form between its markers."""
    index = ROOT / "index.html"
    s = index.read_text(encoding="utf-8")
    start_tag, end_tag = "<!-- inquiry:start -->", "<!-- inquiry:end -->"
    form = inquiry_form(
        "commission", ident="inquire-home", eyebrow="Commissions and projects",
        heading="Something made<br>for your space.",
        intro="Lisa takes commissions, paints murals and large installs, and teaches classes and workshops. Tell her what you have in mind and she will reply by email.",
    )
    block = f"{start_tag}\n    <section id=\"commissions\">\n      {form}\n    </section>\n    {end_tag}"
    a = s.index(start_tag)
    z = s.index(end_tag) + len(end_tag)
    index.write_text(s[:a] + block + s[z:], encoding="utf-8")
    print("rebuilt home inquiry form")


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
        SHOP.format(cards=cards, base=BASE, email=ARTIST["email"], ig=ARTIST["instagram"], footer_links=FOOTER_LINKS.format(links=footer_links("../"))),
        encoding="utf-8",
    )
    print("built shop index")


def build_sitemap():
    urls = [f"{BASE}/", f"{BASE}/art/"] + [f'{BASE}/{s["slug"]}/' for s in SERVICES] + [f'{BASE}/art/{w["slug"]}.html' for w in WORKS]
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
    build_services()
    build_gallery()
    build_home_inquiry()
    build_shop()
    build_sitemap()
