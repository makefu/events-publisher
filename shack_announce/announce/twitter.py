from twitter import *

def announce(text,cred):
    api = Twitter(auth=OAuth( cred['token_key'],
                        cred['token_secret'],
                        cred['consumer_key'],
                        cred['consumer_secret']))
    if not cred.get('mock',False): api.statues.update(status=text)
