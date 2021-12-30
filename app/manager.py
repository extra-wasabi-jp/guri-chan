import os
import boto3

from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageSendMessage

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

dynamodb = boto3.Session(region_name=os.environ['AWS_REGION']).resource('dynamodb')
table = dynamodb.Table('APP_PROPS')

@app.route('/api/gurichan/status', methods=['POST'])
def status():

    # Line への返信
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    app.logger.info(f'Request body: {body}')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # DynamoDB から最新のCDNに保存されたイメージURLを取得する。
    response = table.get_item(
        Key={
            'app_name': 'guri-chan',
        },
    )
    last_updated_at: string = response['Item']['props']['last_uploaded_at']
    latest_image_index_url: string = response['Item']['props']['latest_image_index_url']
    latest_image_url: string = response['Item']['props']['latest_image_url']

    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(
            preview_image_url=latest_image_index_url,
            original_content_url=latest_image_url,
        )
    )


if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
    )
