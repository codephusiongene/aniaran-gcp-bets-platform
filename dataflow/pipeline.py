import argparse
import json
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions, StandardOptions
from datetime import datetime, timezone

class ParseAndValidate(beam.DoFn):
    def process(self, element):
        if isinstance(element, bytes):
            element = element.decode("utf-8")
        try:
            record = json.loads(element)
        except Exception as e:
            # drop malformed; in prod send to DLQ
            return
        # Minimal validation & enrichment
        now = datetime.now(timezone.utc).isoformat()
        record.setdefault("load_ts", now)
        # Ensure required fields; if missing, drop
        required = ["bet_id", "user_id", "game_id", "stake_amount", "odds"]
        if not all(k in record for k in required):
            return
        # Compute payout if not provided
        if "payout" not in record:
            try:
                record["payout"] = float(record["stake_amount"]) * float(record["odds"])
            except Exception:
                record["payout"] = None
        # event_ts normalization
        if "event_ts" in record:
            # allow both ISO and epoch seconds
            try:
                # if epoch
                if isinstance(record["event_ts"], (int, float)):
                    record["event_ts"] = datetime.fromtimestamp(record["event_ts"], tz=timezone.utc).isoformat()
            except Exception:
                record["event_ts"] = now
        else:
            record["event_ts"] = now
        # defaults
        record.setdefault("sport", "football")
        record.setdefault("country", "PL")
        record.setdefault("channel", "web")
        record.setdefault("status", "placed")
        # ingest id
        record.setdefault("ingest_id", f'{record["bet_id"]}:{int(datetime.now().timestamp())}')
        yield record

def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", default="europe-west1")
    parser.add_argument("--runner", default="DirectRunner")
    parser.add_argument("--streaming", action="store_true")
    parser.add_argument("--input_subscription", required=True)
    parser.add_argument("--output_table", required=True, help="project:dataset.table")
    parser.add_argument("--temp_location", required=False)
    parser.add_argument("--staging_location", required=False)
    parser.add_argument("--num_workers", type=int, default=2)

    known_args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(
        pipeline_args,
        project=known_args.project,
        region=known_args.region,
        temp_location=known_args.temp_location,
        streaming=known_args.streaming,
        save_main_session=True,
        experiments=[],
    )
    options.view_as(StandardOptions).runner = known_args.runner
    options.view_as(SetupOptions).save_main_session = True

    schema = (
        "event_ts:TIMESTAMP,bet_id:STRING,user_id:STRING,game_id:STRING,"
        "sport:STRING,country:STRING,channel:STRING,stake_amount:NUMERIC,"
        "odds:FLOAT,payout:NUMERIC,status:STRING,ingest_id:STRING,load_ts:TIMESTAMP"
    )

    with beam.Pipeline(options=options) as p:
        (
            p
            | "ReadFromPubSub" >> beam.io.ReadFromPubSub(subscription=known_args.input_subscription)
            | "ParseAndValidate" >> beam.ParDo(ParseAndValidate())
            | "WriteToBQ" >> beam.io.WriteToBigQuery(
                known_args.output_table,
                schema=schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
                insert_retry_strategy=beam.io.gcp.bigquery_tools.RetryStrategy.RETRY_ALWAYS,
            )
        )

if __name__ == "__main__":
    run()
