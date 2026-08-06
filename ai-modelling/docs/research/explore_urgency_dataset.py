import argparse
import json
from collections import Counter
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explore the TREC-IS urgency classification dataset."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to the TREC-IS JSON dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if not args.dataset.exists():
        raise FileNotFoundError(
            f"Dataset not found: {args.dataset}"
        )

    with args.dataset.open("r", encoding="utf-8") as file:
        data = json.load(file)

    events = data.get("events", [])
    tweets = []

    for event in events:
        tweets.extend(event.get("tweets", []))

    if not tweets:
        raise ValueError("No tweets were found in the dataset.")

    fields = sorted(tweets[0].keys())

    print(f"Dataset file: {args.dataset}")
    print(
        f"File size: "
        f"{args.dataset.stat().st_size / (1024 * 1024):.2f} MB"
    )
    print(f"Number of events: {len(events)}")
    print(f"Total number of tweets: {len(tweets)}")

    print("\nAvailable fields:")
    print(fields)

    print("\nMissing values:")
    for field in fields:
        missing = sum(
            tweet.get(field) in (None, "", [])
            for tweet in tweets
        )
        print(f"{field}: {missing}")

    priority_counts = Counter(
        tweet.get("postPriority", "Missing")
        for tweet in tweets
    )

    print("\nPriority label distribution:")
    for label, count in priority_counts.most_common():
        print(f"{label}: {count}")

    event_type_counts = Counter(
        tweet.get("eventType", "Missing")
        for tweet in tweets
    )

    print("\nEvent type distribution:")
    for event_type, count in event_type_counts.most_common():
        print(f"{event_type}: {count}")

    wildfire_tweets = [
        tweet
        for tweet in tweets
        if tweet.get("eventType") in {"wildfire", "fire"}
    ]

    print(
        f"\nWildfire/fire-related tweets: "
        f"{len(wildfire_tweets)}"
    )

    print("\nOne sample from each priority level:")

    for priority in ["Critical", "High", "Medium", "Low"]:
        sample = next(
            (
                tweet
                for tweet in tweets
                if tweet.get("postPriority") == priority
                and tweet.get("postText")
            ),
            None,
        )

        if sample:
            print("-" * 80)
            print(f"Priority: {priority}")
            print(f"Post ID: {sample.get('postID')}")
            print(f"Event type: {sample.get('eventType')}")
            print(f"Categories: {sample.get('postCategories')}")
            print(f"Text: {sample.get('postText')}")


if __name__ == "__main__":
    main()