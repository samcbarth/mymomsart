#!/usr/bin/env python3
"""Push every URL in sitemap.xml to IndexNow (Bing, Yandex, Seznam, Naver).

Search engines normally find new pages by crawling, which for a site with no
inbound links can take weeks. IndexNow inverts that: the site tells them
directly. No account or API key from a dashboard - ownership is proved by
hosting a file whose name and contents are the same random key.

Google does not participate, so it still has to be handled through Search
Console. Everything else does.

    python submit_indexnow.py            # submit
    python submit_indexnow.py --dry-run  # just list what would go
"""
import argparse, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).parent
HOST = "art.samcbarth.com"
ENDPOINT = "https://api.indexnow.org/IndexNow"


def find_key():
    """The key file is named <key>.txt and contains that same key."""
    for f in ROOT.glob("*.txt"):
        name = f.stem
        if re.fullmatch(r"[0-9a-f]{8,128}", name) and f.read_text(encoding="utf-8").strip() == name:
            return name
    sys.exit("No IndexNow key file found in the site root.")


def urls():
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>(.*?)</loc>", sitemap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = find_key()
    url_list = urls()
    print(f"key {key}\n{len(url_list)} urls")

    if args.dry_run:
        for u in url_list:
            print("  ", u)
        return

    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/{key}.txt",
        "urlList": url_list,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            # 200 accepted, 202 accepted but key still being validated
            print(f"submitted: HTTP {r.status} {r.reason}")
    except urllib.error.HTTPError as e:
        print(f"rejected: HTTP {e.code} {e.reason}\n{e.read().decode()[:400]}")


if __name__ == "__main__":
    main()
