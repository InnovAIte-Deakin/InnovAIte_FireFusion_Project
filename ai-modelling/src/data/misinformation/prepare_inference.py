"""Read the source post collections and produce misinformation API request records."""
import csv
import html
import json


def clean_text(text):
    return " ".join(html.unescape(text).split())


def csv_rows(path, *, delimiter=","):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream, delimiter=delimiter)


def add_post(posts, post_id, text):
    if not text or not text.strip():
        return
    if post_id is None or not str(post_id).strip():
        raise ValueError("Observed post has an empty ID")

    post_id = str(post_id).strip()
    text = text.strip()
    if post_id in posts:
        if clean_text(posts[post_id]) != clean_text(text):
            raise ValueError(f"Conflicting observed text for post {post_id}")
        return
    posts[post_id] = text


def observed_posts(raw, wildfire):
    posts = {}
    trec_file = raw / "TRECIS-2018-2020B.json"
    trec = json.loads(trec_file.read_bytes())
    for event in trec["events"]:
        for tweet in event["tweets"]:
            add_post(posts, tweet["postID"], tweet.get("postText"))

    for row in wildfire:
        add_post(posts, row["tweet_id"], row["text"])

    for event in ("2013_Australia_bushfire", "2012_Colorado_wildfires"):
        path = raw / "CrisisLexT26" / event / f"{event}-tweets_labeled.csv"
        for row in csv_rows(path):
            # The original CSV header has a space before "Tweet Text".
            add_post(posts, row["Tweet ID"], clean_text(row[" Tweet Text"]))

    records = []
    for post_id in sorted(posts):
        records.append({"id": post_id, "content": posts[post_id]})
    return records


def synthetic_posts(raw):
    path = raw / "Firefusion_Synthetic_Social_Media_Posts.json"
    records = []
    for row in json.loads(path.read_bytes()):
        records.append({
            "id": row["post_id"],
            "content": row["text"],
            "ts": row["timestamp"],
            "platform": row["platform"],
            "author_name": row["username"],
        })
    return records


def inference_datasets(raw, wildfire):
    return {
        "inference/observed_posts.jsonl": observed_posts(raw, wildfire),
        "inference/synthetic_demo_posts.jsonl": synthetic_posts(raw),
    }
