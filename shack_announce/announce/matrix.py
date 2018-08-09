from matrix_client.api import MatrixHttpApi

def announce(text, cred):
    matrix = MatrixHttpApi(cred.get("url","https://matrix.org"),token=cred['access_token'])
    for room in cred['rooms']:
        roomid = matrix.get_room_id(room)
        matrix.join_room(roomid)
        if not cred.get('mock',False): matrix.send_message(roomid,text)
