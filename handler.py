import datetime
import logging
import os
import urllib3
import json
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def run(event, context):
    # log
    current_time = datetime.datetime.now().time()
    name = "presence_setter"
    logger.info("Cron execution " + name + " ran at " + str(current_time))

    api_key = os.getenv("SLACK_API_KEY")
    if not api_key:
        logger.error("No api key available in the env")
        return

    http = urllib3.PoolManager()

    update_status(api_key, http)
    update_snooze(api_key, http)


def update_snooze(api_key, http):
    r = http.request("GET", "https://slack.com/api/dnd.info",
                     headers={"Authorization": "Bearer " + api_key})

    if r.status == 200:
        payload = json.loads(r.data)
        snooze_enabled = payload.get("snooze_enabled", False)

        if snooze_enabled:
            r = http.request("GET", f"https://slack.com/api/dnd.endDnd",
                             headers={"Authorization": "Bearer " + api_key})
            logger.info(f"Ending snooze")
            if r.status != 200:
                logger.error(f"Failed to end snooze")
        else:
            r = http.request("GET", f"https://slack.com/api/dnd.setSnooze?num_minutes=6120",
                             headers={"Authorization": "Bearer " + api_key})
            logger.info(f"Setting snooze for a long time")
            if r.status != 200:
                logger.error(f"Failed to set snooze")


def update_status(api_key, http):
    r = http.request("GET", "https://slack.com/api/users.getPresence",
                     headers={"Authorization": "Bearer " + api_key})

    new_presence = "away"
    if r.status == 200:
        payload = json.loads(r.data)
        presence = payload.get("presence", "away")
        logger.info(payload)
        logger.info(f"Current presence is set to {presence}")
        if presence == "away":
            new_presence = "auto"

    r = http.request("POST", f"https://slack.com/api/users.setPresence?presence={new_presence}",
                     headers={"Authorization": "Bearer " + api_key})
    logger.info(f"Setting status to {new_presence}")
    if r.status != 200:
        logger.error(f"Failed to set the status to {new_presence}")


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    run({}, {})
