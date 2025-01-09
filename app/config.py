import sys
import os
from dotenv import load_dotenv
import logging


def load_configurations(app):
    load_dotenv()
    app.config["ACCESS_TOKEN"] ="EAAOnMkV2ew4BO0HSXQF5npbtPKyPZBE9ZBtyw3AxQpHQhbcrQpVf38IW0iLYZCdYN1krQTx8KmEyG0O347a2jSmAp1Q9Kufxwh59ZCjqfRzsZAhSGOm8ubM9qlk8wfKsxBq359dUltLsnqZABKJrTKkqCqMankZBJSR2ZBn3gjwC1Woi20ZCox4YBMhpewJZA0uSfAF0FUCaTjPXembGy91Ka6nnu1lla0jQaXMwIZD"
    app.config["YOUR_PHONE_NUMBER"] = os.getenv("YOUR_PHONE_NUMBER")
    app.config["APP_ID"] = os.getenv("APP_ID")
    app.config["APP_SECRET"] = os.getenv("APP_SECRET")
    app.config["RECIPIENT_WAID"] = os.getenv("RECIPIENT_WAID")
    app.config["VERSION"] = os.getenv("VERSION")
    app.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")
    app.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
