# JAVIER MOBILE - optional Instagram Graph API module
#
# Only active when IG_ACCESS_TOKEN and IG_BUSINESS_ID are set in .env.
# Without them, JAVIER only offers the honest "outbox" preparation tool.
#
# Setup (short version, details in README.md):
#   1. Make the MeowUfo Instagram account a Business account
#      (Instagram app -> Settings -> Account type -> Business).
#   2. Link it to a Facebook Page (create one if needed) via
#      Instagram Settings -> Linked accounts, or Meta Business Suite.
#   3. Create an app at https://developers.facebook.com (type: Business),
#      add the product "Instagram Graph API".
#   4. In the Graph API Explorer, generate a user token with the scopes
#      instagram_basic, instagram_content_publish, pages_show_list,
#      pages_read_engagement - then extend it to a long-lived token.
#   5. Get the IG business account id:
#      GET /me/accounts -> page id -> GET /{page-id}?fields=instagram_business_account
#   6. Put both values in .env as IG_ACCESS_TOKEN and IG_BUSINESS_ID.
#
# The Graph API can only publish images that are reachable on a PUBLIC
# https URL - it fetches the image from Meta's servers. Simplest options:
#   - Tailscale Funnel: expose the outbox folder briefly
#     (tailscale funnel 8000), or
#   - upload the image to the Shopify CDN / any image host first and use
#     that URL.

import os
import time

import requests

GRAPH = "https://graph.facebook.com/v23.0"


def is_configured():
    return bool(os.environ.get("IG_ACCESS_TOKEN")) and \
        bool(os.environ.get("IG_BUSINESS_ID"))


def publish_post(image_url, caption):
    if not is_configured():
        return {"error": "Instagram Graph API ist nicht konfiguriert "
                         "(IG_ACCESS_TOKEN / IG_BUSINESS_ID fehlen in .env)"}
    if not image_url.startswith("https://"):
        return {"error": "image_url muss eine oeffentliche https-URL sein - "
                         "die Graph API laedt das Bild von dort"}
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_id = os.environ["IG_BUSINESS_ID"]
    try:
        r = requests.post(
            "%s/%s/media" % (GRAPH, ig_id),
            data={"image_url": image_url, "caption": caption,
                  "access_token": token},
            timeout=30)
        body = r.json()
        if "id" not in body:
            return {"error": "media container failed: %s" % body}
        container_id = body["id"]

        # Meta processes the container asynchronously; poll briefly.
        # Token goes in the Authorization header, not the URL, so it
        # cannot end up in proxy/server logs.
        ready = False
        for _ in range(10):
            s = requests.get(
                "%s/%s" % (GRAPH, container_id),
                params={"fields": "status_code"},
                headers={"Authorization": "Bearer %s" % token},
                timeout=15).json()
            if s.get("status_code") == "FINISHED":
                ready = True
                break
            if s.get("status_code") == "ERROR":
                return {"error": "container processing failed: %s" % s}
            time.sleep(2)
        if not ready:
            return {"error": "container not ready after 20s - Bild "
                             "vermutlich zu gross oder URL zu langsam; "
                             "spaeter erneut versuchen"}

        r = requests.post(
            "%s/%s/media_publish" % (GRAPH, ig_id),
            data={"creation_id": container_id, "access_token": token},
            timeout=30)
        body = r.json()
        if "id" not in body:
            return {"error": "publish failed: %s" % body}
        return {"ok": True, "published_media_id": body["id"],
                "note": "Post ist live auf Instagram."}
    except requests.RequestException as e:
        return {"error": "instagram request failed: %s" % e}
