import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from collections import deque

from fsm import TocMachine
from utils import send_text_message, send_quick_reply

load_dotenv()


app = Flask(__name__, static_url_path="")


machine = TocMachine()
machines = {}

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent ,message is TextMessage and str, response
    for event in events:
        isText = [
                isinstance(event,MessageEvent),
                isinstance(event.message,TextMessage),
                isinstance(event.message.text,str)
                ]

        if all(isText):
            if event.source.user_id not in machines:
                machines[event.source.user_id] = TocMachine()
            response = machines[event.source.user_id].advance(event)
            print(f"\nFSM STATE: {machines[event.source.user_id].state}")
            #print(f"REQUEST BODY: \n{body}")
            if response == False:
                actions = [("CHECK","check gold"),("RETURN","return to main menu")]
                if machines[event.source.user_id].is_initial():
                    actions = [("START","start"),("ADD","add gold"),("CHECK","check gold")]
                elif machines[event.source.user_id].is_gold_add():
                    actions = [("100","100"),("500","500"),("1000","1000")] + actions
                elif machines[event.source.user_id].is_coin_flip():
                    actions = [
                            ("half",str(int(machines[event.source.user_id].gold/2))),
                            ("all",str(int(machines[event.source.user_id].gold)))] + actions
                elif machines[event.source.user_id].is_start():
                    actions = [
                            ("BJ","play blackjack"),
                            ("DICE","roll dice"),
                            ("COIN","flip a coin")
                            ] + actions
                send_quick_reply(event.reply_token,actions)

    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
