
import facebook
def announce(text, cred):  # shackspace page
    # token requires publish_pages permission for shackspace page
    graph = facebook.GraphAPI(access_token=cred['access_token'], version="2.12")
    for group in cred['groups']:
        if not cred.get('mock',False): graph.put_object(group, "feed", message=text)
