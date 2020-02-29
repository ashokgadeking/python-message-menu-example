from flask import Flask, request, make_response, Response
import os
import json
import ssl
from slack import WebClient

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Slack client for Web API requests
slack_client = WebClient(token=SLACK_BOT_TOKEN, ssl=ssl_context)

# Flask webserver for incoming traffic from Slack
app = Flask(__name__)

# Helper for verifying that requests came from Slack
def verify_slack_token(request_token):
    if SLACK_VERIFICATION_TOKEN != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
        return make_response("Request contains invalid Slack verification token", 403)


# The endpoint Slack will load your menu options from
@app.route("/slack/message_options", methods=["POST"])
def message_options():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Verify that the request came from Slack
    verify_slack_token(form_json["token"])

    # Dictionary of menu options which will be sent as JSON
    menu_options = {
              "options": [
                {
                  "text": {
                    "type": "plain_text",
                    "text": "Cappuccino",
                  },
                  "value": "Cappuccino"
                },
                {
                  "text": {
                    "type": "plain_text",
                    "text": "Latte"
                  },
                  "value": "Latte"
                },
                {
                  "text": {
                    "type": "plain_text",
                    "text": "Cortado"
                  },
                  "value": "Cortado"
                }
              ]
        }

    # Load options dict as JSON and respond to Slack
    return Response(json.dumps(menu_options), mimetype='application/json')


# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():

    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Verify that the request came from Slack
    verify_slack_token(form_json["token"])

    # Check to see what the user's selection was and update the message accordingly
    selection = form_json["actions"][0]["selected_option"]["value"]

    response = slack_client.chat_postMessage(
      channel=form_json["channel"]["id"],
      ts=form_json["message"]["ts"],
      text="One {}, right coming up! :coffee:".format(selection),
    )

    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


# Send a Slack message on load. This needs to be _before_ the Flask server is started

# A Dictionary of message attachment options
attachments_json = [{
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Would you like some coffee? :coffee:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Pick a beverage..."
            },
            "accessory": {
                "type": "external_select",
                "action_id": "menu_options_2319",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select an item"
                },
                "min_query_length": 0
            }
        }
    ]
}]

# Send a message with the above attachment, asking the user if they want coffee
response = slack_client.chat_postMessage(
  channel="#random",
  attachments=json.dumps(attachments_json)
)

# Start the Flask server
if __name__ == "__main__":
    app.run()
