shack_announce
==============

announce event-o-mat events

creds.json
==========

The credentials for the different services is the center-piece of the
announcer. Without credentials not much will happen.
Creds.json looks like this:

```json
{
  "mastodon": ... ,
  "facebook": ...
  ...
}
```

The following subsections describe how you can get each token.

# Mastodon
see `shack_announce/autenticate.py` , you need:
```json
{
  "mastodon":{
    "chaos.social": {
      "client_id": "",
      "client_secret": "",
      "access_token": "",
      "url": "https://chaos.social",
      "visibility": "unlisted"
    },
    "botsin.space": {
      "client_id": "",
      "client_secret": "",
      "access_token": "",
      "url": "https://botsin.space",
      "visibility": "public"
    }
  }
}
```
```python
from mastodon import Mastodon
url = "https://botsin.space"
user = "your-email"
pw = "your-pass"
app = Mastodon.create_app( "shack-publisher", api_base_url=url )
mastodon = Mastodon(client_id=app[0],client_secret=app[1],api_base_url=url)
log = mastodon.log_in(user,pw)
print(json.dumps({
  "client_id": app[0],
  "client_secret": app[1],
  "api_base_url": url,
  "access_token": log
},indent=4))

```


# Facebook
1. Create a new app (do not publish)
2. Create short-lived access token for the page via the API explorer
3. Create long-lived access token via the token debug page
4. use the token in the api explorer to GET `/3.1/<PAGE-ID>?fields=access_token`
   copy the never-expiring token (check via token debug page)
```json
{
  "facebook": {
    "access_token": "",
    "groups": [ 122027937823921 ]
  }
}
```
# Twitter
1. Become developer with application at https://developer.twitter.com
2. create new app, go to keys and tokens
3. create all 4 token and secrets

```json
"twitter": {
  "consumer_key": "A",
  "consumer_secret": "B",
  "token_key": "C",
  "token_secret": "D",
}
```
