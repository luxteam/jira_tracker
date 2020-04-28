from urllib.parse import urlencode
import urllib.request as urlrequest
import json


def notify(**kwargs):
    # send message to slack API
    return send(kwargs)

def send(webhook, payload):
    # send payload to slack API
    url = webhook
    opener = urlrequest.build_opener(urlrequest.HTTPHandler())
    payload_json = json.dumps(payload)
    data = urlencode({"payload": payload_json})
    req = urlrequest.Request(url)
    response = opener.open(req, data.encode('utf-8')).read()
    return response.decode('utf-8')