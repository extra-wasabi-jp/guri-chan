# guri-chan

https://qiita.com/kro/items/67f7510b36945eb9689b を参考に作成した<br/>
Line Messaging API の Bot アプリです。<br/>

Webhook で何かしらメッセージが届くと、DynamoDB に保存された画像が送信者に返信されます。<br/>
画像はS3(CloudFrontで公開) に保存された画像で、画像のURL は DynamoDB に保存された内容を取得しています

Python + Flask + boto3 で作りました。
実行環境として Docker Image のDockerfileもあります。

## 1. 準備

### 1-1. Let's Encript の取得

Linux に certbot 以下をインストールして、Let's Encrypt のサーバー証明書を取得します。

```
$ sudo apt install certbot
```

証明書発行時、対象ドメインの80番ポートを利用するので、実行するサーバーのFWの設定と HTTP Server が動いている場合は一旦停止する

```
$ sudo certbot certonly --standalone -t
```

途中、ライセンスの同意や連絡先の email アドレスの入力、対象ドメインの入力などをすると証明書が以下に生成される
```
/etc/letsencrypt/live/[対象ドメイン]/
cert.pem
chain.pem
fullchain.pem
privkey.pem
```

Nginx の場合 fullchain.pem を ssl_certificate に、privkey.pem を　ssl_certificate_key に指定する


### 1-2. Line Developper アカウント登録＋チャンネル作成

https://developers.line.me/ja/services/messaging-api/

作るもの
* 開発者アカウント
* プロバイダー
* チャンネル
* チャンネルアクセストークン

※詳細は割愛

### 1-3. S3 Bucket と AccessKeyID, AccessSecretKey を取得する。

* Bucket

  * guri-chan

* AccessKyID, AccessSecretKey は S3 guri-chan への権限を持った IAM にて作成する。

  詳細は割愛


## 2. Dcoker image ビルド
```
$ docker build -t guri-chan .
```

## 3. 実行

### 3-1. docker compose で動かす場合、

#### Line チャンネルアクセストークン、シークレット、と AWS アクセスキーとシークレットを .env に設定する。

```bash
CHANNEL_ACCESS_TOKEN="@@@ Line Developper で発行した チャンネルアクセストークン @@@"
CHANNEL_SECRET="@@@ Line Developper で発行したシークレット @@@"
AWS_REGION="@@@ AWS のリージョン @@@"
AWS_ACCESS_KEY_ID="@@@ AWS のアクセスキーＩＤ @@@"
AWS_SECRET_ACCESS_KEY="@@@ AWS のシークレットキー @@@"
```

#### 実行

```bash
$ docker compose up -d
```

### 3-2. docker で動かす場合

※aws config のプロファイルを「guri-chan」で登録している場合、defaul の場合「--profile guri-chan」は省略する
```
AWS_REGION="ap-northeast-1"
AWS_ACCESS_KEY_ID=$(aws --profile guri-chan configure get aws_access_key_id)
AWS_SECRET_ACCESS_KEY=$(aws --profile guri-chan configure get aws_secret_access_key)

export AWS_REGION AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY

docker run --name guri-chan --rm \
	-p 5001:5001 \
	-e APP_PORT=5001 \
	-e CHANNEL_ACCESS_TOKEN="Line Developper で発行した チャンネルアクセストークン" \
	-e CHANNEL_SECRET="Line Developper で発行したシークレット" \
	-e AWS_REGION=ap-northeast-1 \
	-e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
	-e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
	-d guri-chan:latest
```
