import os

from linebot import LineBotApi, WebhookParser
from linebot.models import *


channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
line_bot_api = LineBotApi(channel_access_token)

# reply : array of pair
def send_quick_reply(reply_token,reply):
    arr = []
    for obj in reply:
        arr.append(QuickReplyButton(action=MessageAction(label=obj[0],text=obj[1])))
    flex_message = TextSendMessage(text="Invalid Input",quick_reply=QuickReply(items=arr))
    line_bot_api.reply_message(reply_token,flex_message)

def send_quick_message_reply(id,message,reply):
    arr = []
    for obj in reply:
        arr.append(QuickReplyButton(action=MessageAction(label=obj[0],text=obj[1])))
    flex_message = TextSendMessage(text=message,quick_reply=QuickReply(items=arr))
    line_bot_api.push_message(id,flex_message)

def send_text_message(reply_token,text):
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
    return "OK"


"""
def send_image_url(id, img_url):
    pass
"""

def send_button_message(id, text, buttons):
    pass

def push_message(id,message):
    line_bot_api.push_message(id,TextSendMessage(text=message))
    return "OK"

def send_image_carousel(id,img,labels,txt):
    arr = []
    for i,url in enumerate(img):
        arr.append(
                ImageCarouselColumn(
                    image_url = url,
                    action = MessageTemplateAction(
                        label=labels[i],
                        text=txt[i]
                        )
                    )
                )
    msg = TemplateSendMessage(
            alt_text='ImageCarousel template',
            template=ImageCarouselTemplate(columns=arr)
            )
    line_bot_api.push_message(id,msg)
    return "OK"

def send_confirm_message(id,message,labels,txt):
    arr = []
    for i in range(len(labels)):
        arr.append(
                MessageTemplateAction(
                    label=labels[i],
                    text=txt[i]
                    )
                )
    msg = TemplateSendMessage(
            alt_text='Confirm template',
            template=ConfirmTemplate(text=message,actions=arr)
            )
    line_bot_api.push_message(id,msg)
    return "OK"

