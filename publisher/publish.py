import argparse, json, random, time, uuid
from datetime import datetime, timezone
from faker import Faker
from google.cloud import pubsub_v1

SPORTS = ["football", "basketball", "tennis", "esports"]
COUNTRIES = ["PL", "DE", "UK", "ES", "IT", "FR", "SE", "NO", "DK", "NL"]
CHANNELS = ["web", "mobile"]
STATUSES = ["placed", "settled", "void"]

def make_event(fake):
    bet_id = str(uuid.uuid4())
    user_id = f"user_{fake.random_int(1000,9999)}"
    game_id = f"game_{fake.random_int(100000,999999)}"
    sport = random.choice(SPORTS)
    country = random.choice(COUNTRIES)
    channel = random.choice(CHANNELS)
    stake = round(random.uniform(1.0, 200.0), 2)
    odds = round(random.uniform(1.2, 12.0), 2)
    status = random.choices(STATUSES, weights=[0.85, 0.1, 0.05])[0]
    now = datetime.now(timezone.utc).timestamp()
    return {
        "event_ts": now,
        "bet_id": bet_id,
        "user_id": user_id,
        "game_id": game_id,
        "sport": sport,
        "country": country,
        "channel": channel,
        "stake_amount": stake,
        "odds": odds,
        "status": status,
    }

def main(project, topic, rate):
    fake = Faker()
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic)
    print(f"Publishing to {topic_path} at ~{rate} msg/s. Ctrl+C to stop.")
    interval = 1.0 / max(rate, 1)
    try:
        while True:
            ev = make_event(fake)
            data = json.dumps(ev).encode("utf-8")
            publisher.publish(topic_path, data=data)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--topic", default="bets-topic")
    parser.add_argument("--rate", type=int, default=5, help="events per second")
    args = parser.parse_args()
    main(args.project, args.topic, args.rate)
