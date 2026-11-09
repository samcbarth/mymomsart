# Basil Artwork

Site for Lisa Barth's abstract floral paintings. Live at https://art.samcbarth.com/ (GitHub Pages, deploys on push to `main`).

## How it works
- `artworks.json` is the single source of truth: artist info, size price table, every painting.
- `python build.py` regenerates `art/*.html`, the home gallery, the shop index, `sitemap.xml` and `robots.txt`. Do not hand-edit generated files.
- `script.js` handles the gallery viewer and the HubSpot newsletter form (portal 20693956).

## Scripts (stdlib Python, secrets from environment only)
- `make_payment_links.py`: Stripe Payment Links for priced originals. Needs `STRIPE_KEY`.
- `make_prints.py`, `publish_prints.py`: Printify products for shop 28768076. Needs `PRINTIFY_TOKEN`. Reads `print_ready/` (gitignored).
- `submit_indexnow.py`: tells search engines about new URLs.
- `ingest.py`: pulls originals from Google Drive.

## Deploy
Work on a branch, run `python build.py`, open a PR. Merging to `main` publishes.
