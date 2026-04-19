import asyncio
import datetime as dt
import os

import boto3

from daily_brief.llm.build_graph import build_graph
from daily_brief.llm.state import BriefState
from daily_brief.utils.load_config import _load_config

def handler(event, context):
    config = _load_config()

    # Env vars override config.yaml defaults
    provider = os.environ.get("BRIEF_PROVIDER") or config["defaults"]["provider"]
    location = os.environ.get("BRIEF_LOCATION") or config["defaults"]["location"]
    topic = os.environ.get("BRIEF_TOPIC") or config["defaults"]["topic"]

    sender = os.environ["SES_SENDER"]
    recipient = os.environ["SES_RECIPIENT"]

    initial_state: BriefState = {
        "provider": provider,
        "location": location,
        "topic": topic,
        "tavily_cache": False,
        "situation": "",
        "world_directive": "",
        "national_directive": "",
        "local_directive": "",
        "raw_stories": [],
        "deduped_stories": [],
        "analyzed_stories": [],
        "connections": [],
        "briefing": "",
    }

    async def run():
        graph = build_graph()
        result = await graph.ainvoke(initial_state)
        return result["briefing"]

    briefing = asyncio.run(run())

    date_str = dt.datetime.now().strftime("%Y-%m-%d")
    subject = f"Daily Brief — {topic} — {date_str}"

    ses = boto3.client("ses", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [recipient]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Text": {"Data": briefing, "Charset": "UTF-8"}},
        },
    )

    return {"statusCode": 200, "chars": len(briefing)}
