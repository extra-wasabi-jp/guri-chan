# guri-chan

https://qiita.com/kro/items/67f7510b36945eb9689b を参考に作成した<br/>
Line Messaging API の Bot アプリです。<br/>

Python + Flask で作りました。
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


## 2. Dcoker image ビルド
```
$ docker build -t guri-chan .
```

## 3. 実行
```
$ docker run --name guri-chan --rm \
	-p 5001:5001 \
	-e APP_PORT=5001 \
	-e CHANNEL_ACCESS_TOKEN="Line Developper で発行した チャンネルアクセストークン" \
	-e CHANNEL_SECRET="Line Developper で発行したシークレット" \
	-d guri-chan:latest
```
