import os
import uuid
import json
import base64
import boto3
from datetime import datetime

from flask import Flask, request, abort, jsonify

from linebot.v3 import (
  WebhookHandler
)
from linebot.v3.webhooks import (
  MessageEvent,
  TextMessageContent,
  ImageMessageContent
)

from linebot.v3.messaging import (
  Configuration, 
  ReplyMessageRequest,
  MessagingApi,
  ApiException,
  ImageMessage,
  ApiClient
)
from linebot.v3.exceptions import (
  InvalidSignatureError
)

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']

configuration = Configuration(
    access_token=CHANNEL_ACCESS_TOKEN
)
handler = WebhookHandler(CHANNEL_SECRET)

endpointUrlS3 = os.getenv('S3_ENDPOINT_URL', default=None)
endpointUrlDynamoDB = os.getenv('DYNAMO_DB_ENDPOINT_URL', default=None)

# DyndamoDB クライアウト
dynamodb = boto3.client(
    'dynamodb',
    region_name=os.environ['AWS_REGION'],
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key = os.getenv('AWS_SECRET_KEY'),
    endpoint_url=endpointUrlDynamoDB
)

# S3 クライアント
s3 = boto3.client(
    's3',
    region_name=os.environ['AWS_REGION'],
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key = os.getenv('AWS_SECRET_KEY'),
    endpoint_url=endpointUrlS3
)

"""
Line ステータス用エンドポイント
"""
@app.route('/api/gurichan/status', methods=['POST'])
def status():

    # Line への返信
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    app.logger.info(f'### Request body: {body}')

    try:
        handler.handle(body, signature)
    except ApiException as e:
        app.logger.warn(f'### error {e}')
        abort(400)
    except InvalidSignatureError as e:
        app.logger.warn(f'### error {e}')
        abort(400)

    return 'OK'

"""
Line API ハンドラ
"""
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # DynamoDB から最新のCDNに保存されたイメージURLを取得する。
    try:
        response = dynamodb.get_item(
            TableName='APP_PROPS',
            Key={
                'app_name': {'S': 'guri-chan'},
            },
        )
    except Exception as e:
        app.logger.error(f'### error {e}')
        abort(400)

    last_updated_at: string = response['Item']['props']['M']['last_uploaded_at']['S']
    latest_image_index_url: string = response['Item']['props']['M']['latest_image_index_url']['S']
    latest_image_url: string = response['Item']['props']['M']['latest_image_url']['S']

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        ImageMessage(
                            original_content_url=latest_image_url,
                            preview_image_url=latest_image_index_url
                        )
                    ]
                )
            )
        except Exception as e:
            app.logger.error(f'### error = {e}')
            abort(400)


"""
ファイルアップロード
"""
@app.route('/api/gurichan/upload', methods=['POST'])
def upload():

    # シグネチャがヘッダーにセットされていてかつ正しい事
    if 'X-Gurichan-Signature' not in request.headers:
        return jsonify({
            'status': 'NG',
            'message': 'Header X-Gurichan-Signature is requred',
        }), 403

    signature = request.headers['X-Gurichan-Signature']
    if signature != os.getenv('UPLOAD_SIGNATURE', None):
        return jsonify({
            'status': 'NG',
            'message': 'invalid signature',
        }), 403

    body = request.data.decode('utf-8')
    body = json.loads(body)

    encodedImage = body['encoded_image']

    img_bin = base64.b64decode(encodedImage)

    now = datetime.now()
    ymd = now.strftime('%Y%m%d')
    filename = '{uuid}.jpg'.format(uuid=uuid.uuid4())
    fullpath = 'images/{ymd}/{filename}'.format(ymd=ymd, filename=filename)

    # S3 にファイルをアップロードする (s3://guri0-chan/images/yyyyMMdd/uuid.jpg)
    response = s3.put_object(
        Body=img_bin,
        Bucket='guri-chan',
        Key=fullpath,
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        return jsonify({
            'status': 'NG',
            'message': 'S3へのアップロードでエラーが発生しました',
        }), 500
    
    # DynamoDB のプロパティを更新する
    cloudfront_url = os.getenv('CLOUDFRONT_URL', 'http://localhost/')
    index_url = "{cloudfront_url}{fullpath}".format(cloudfront_url=cloudfront_url, fullpath=fullpath)
    image_url = "{cloudfront_url}{fullpath}".format(cloudfront_url=cloudfront_url, fullpath=fullpath)
    response = dynamodb.update_item(
        TableName='APP_PROPS',
        Key={
            "app_name": {"S": "guri-chan"},
        },
        UpdateExpression="SET props.last_uploaded_at = :last_uploaded_at"\
            " , props.latest_image_index_url = :index_url"\
            " , props.latest_image_url = :image_url",
        ExpressionAttributeValues={
            ":last_uploaded_at": { "S": now.isoformat() },
            ":index_url": { "S": index_url },
            ":image_url": { "S": image_url },
        },
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        return jsonify({
            'status': 'NG',
            'message': 'DynamoDB の更新が失敗しました',
        }), 500

    return jsonify({
        'status': 'OK',
        'message': '画像はアップロードされました',
        'url': image_url,
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
    )
