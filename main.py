
from flask import Flask, request
import requests

app = Flask(__name__)

# Airtable config
AIRTABLE_BASE_ID = "app9VwN9k00nPmpNC"
AIRTABLE_TABLE_NAME = "tblp5E0XBJDGPEEYt"
AIRTABLE_API_KEY = "patCCJQPkpHn8HURJ.ab0c036429d219b5deb8b30ca3c5619c843a1cbb59d199c88ede37139a448182"

# RapidAPI config
RAPIDAPI_KEY = "d2e8898bfemsh86306d337b38bcap193d1djsnbfe332449d9a"
RAPIDAPI_HOST = "instagram-premium-api-2023.p.rapidapi.com"

@app.route("/", methods=["GET"])
def sync_data():
    print("🚀 Sync route hit")

    airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers_airtable = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.get(airtable_url, headers=headers_airtable)
        print(f"📦 Airtable GET status: {res.status_code}")
        print(f"📦 Airtable content: {res.text[:300]}")
        if res.status_code != 200:
            return "Airtable fetch error", 500

        records = res.json().get("records", [])
        usernames = [r["fields"]["Username"] for r in records if "Username" in r["fields"]]
        print(f"📋 Found usernames: {usernames}")

        if not usernames:
            print("⚠️ No usernames found in Airtable.")
            return "No usernames to process.", 200

        for username in usernames:
            print(f"🔍 Fetching user: {username}")
            try:
                user_res = requests.get(
                    f"https://{RAPIDAPI_HOST}/v1/user/by/username?username={username}",
                    headers={
                        "x-rapidapi-key": RAPIDAPI_KEY,
                        "x-rapidapi-host": RAPIDAPI_HOST
                    }
                )
                print(f"🧾 user_res status: {user_res.status_code}")
                user_json = user_res.json()
                print(f"🧾 user_res body: {str(user_json)[:300]}")
                user_id = user_json.get("user", {}).get("pk_id")
                if not user_id:
                    print(f"❌ No user ID found for {username}")
                    continue

                media_res = requests.get(
                    f"https://{RAPIDAPI_HOST}/v2/user/medias?user_id={user_id}&count=50",
                    headers={
                        "x-rapidapi-key": RAPIDAPI_KEY,
                        "x-rapidapi-host": RAPIDAPI_HOST
                    }
                )
                print(f"📽️ Media fetch status: {media_res.status_code}")
                medias = media_res.json().get("data", [])
                print(f"📽️ Found {len(medias)} media items")

                for media in medias:
                    if media.get("media_type") != "video":
                        continue
                    video_url = media.get("video_url")
                    if not video_url:
                        continue

                    data = {
                        "fields": {
                            "Username": username,
                            "Caption": media.get("caption", ""),
                            "Reel Link": video_url,
                            "Thumbnail": media.get("thumbnail_url", ""),
                            "Views": media.get("view_count", 0)
                        }
                    }
                    post = requests.post(airtable_url, headers=headers_airtable, json=data)
                    print(f"📤 POST status: {post.status_code}")
                    if post.status_code == 200:
                        print(f"✅ Added: {video_url}")
                    else:
                        print(f"⚠️ Failed to add: {video_url} — {post.text}")
            except Exception as e:
                print(f"❌ Error for {username}: {e}")

    except Exception as e:
        print(f"💥 Top-level error: {e}")
        return "Internal Server Error", 500

    return "✅ Sync complete", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
