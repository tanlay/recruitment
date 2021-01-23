from dingtalkchatbot.chatbot import DingtalkChatbot
from django.conf import settings


""""定义钉钉机器"""
def send(message, at_mobiles=[]):
    webhook = settings.DINGTALK_WEB_HOOK
    xiaoding = DingtalkChatbot(webhook)
    xiaoding.send_text(f'面试通知：{message}', at_mobiles=at_mobiles)