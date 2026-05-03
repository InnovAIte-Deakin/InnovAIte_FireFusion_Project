import requests
import pandas as pd

API_URL = "https://emergency.vic.gov.au/public/events-geojson.json"


def extract_point(geometry):
    """
    Extract latitude and longitude from GeoJSON geometry.
    VicEmergency often uses GeometryCollection.
    """
    if not geometry:
        return None, None

    if geometry.get("type") == "Point":
        lon, lat = geometry.get("coordinates", [None, None])[:2]
        return lat, lon

    if geometry.get("type") == "GeometryCollection":
        for g in geometry.get("geometries", []):
            if g.get("type") == "Point":
                lon, lat = g.get("coordinates", [None, None])[:2]
                return lat, lon

    return None, None


def fetch_vic_emergency():
    response = requests.get(
        API_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )
    response.raise_for_status()
    return response.json()


data = fetch_vic_emergency()

records = []

for feature in data.get("features", []):
    props = feature.get("properties", {})
    lat, lon = extract_point(feature.get("geometry"))

    records.append({
        "id": props.get("id"),
        "feed_type": props.get("feedType"),
        "category1": props.get("category1"),
        "category2": props.get("category2"),
        "status": props.get("status"),
        "name": props.get("name"),
        "action": props.get("action"),
        "location": props.get("location"),
        "created": props.get("created"),
        "updated": props.get("updated"),
        "size": props.get("sizeFmt"),
        "source_org": props.get("sourceOrg"),
        "source_title": props.get("sourceTitle"),
        "latitude": lat,
        "longitude": lon,
        "text": props.get("text"),
    })

df = pd.DataFrame(records)

# Filter by feed type
incidents = df[df["feed_type"] == "incident"]

# Category selection
category = ["Fire", "Planned Burn", "Bushfire"]

# Filter by category for category1 and category2
filtered_df = incidents[incidents["category1"].isin(category) | incidents["category2"].isin(category)]

# Sort by created date
filtered_df = filtered_df.sort_values(by="created", ascending=False)

# Save to CSV
filtered_df.to_csv("vic_emergency_bushfire_incidents.csv", index=False, encoding="utf-8")