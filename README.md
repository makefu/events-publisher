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
  "mastodon": {
    "client_id": "",
    "client_secret": "",
    "access_token": ""
  }
}
```

# Facebook
1. Create a new app (do not publish)
2. Create short-lived access token for the page via the API explorer
3. Create long-lived access token via the token debug page
4. use the token in the api explorer to GET `/3.1/<PAGE-ID>?fields=access_token`
   copy the never-expiring token (check via token debug page)
