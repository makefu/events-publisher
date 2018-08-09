from mastodon import Mastodon

def announce(text, cred):

    visibility = cred.get("visibility", "unlisted")
    mastodon = Mastodon(
        client_id=cred["client_id"],
        client_secret=cred["client_secret"],
        access_token=cred["access_token"],
        api_base_url=cred["url"],
    )
    if not cred.get('mock',False): mastodon.status_post(text, visibility=visibility)
