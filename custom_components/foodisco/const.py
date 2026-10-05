"""Constants for the Foodisco integration."""

from datetime import timedelta

DOMAIN = "foodisco"

# The project behind foodisco.app. Foodisco polls nothing in your home: this
# integration asks Foodisco for the day's totals and reports events (oven finished).
BASE_URL = "https://fanioqsbrwgehmuhxmwk.supabase.co/functions/v1"

# ha-status accepts one request per 30 s per token; a minute leaves room for a retry.
SCAN_INTERVAL = timedelta(seconds=60)

CONF_READ_TOKEN = "read_token"
CONF_EVENTS_TOKEN = "events_token"
CONF_ACCOUNT_ID = "account_id"
CONF_DISPLAY_NAME = "display_name"

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]
EVENT_OVEN_FINISHED = "oven_finished"
REPORTABLE_EVENTS = [EVENT_OVEN_FINISHED]
