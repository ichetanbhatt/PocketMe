# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render, redirect
import ast, json
import requests
import firebase_admin
from firebase_admin import credentials, db
from django.conf import settings

# Imp Keys
SLACK_TOKEN = settings.SLACK_TOKEN
POCKET_API_KEY = settings.POCKET_CONSUMER_KEY

# FireBase Configs
cred = credentials.Certificate('slackreads-firebase-adminsdk-xnduc-2082689e0f.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://slackreads.firebaseio.com'
})
ref = db.reference('')
cache_ref = db.reference('/cache')



# Slack Functions
# Register for app via Slack
def slashcmd(request):
    if request.method == 'POST':
        message = request.POST.get('text')
        data = {
            "text": "Yo,Seems like you wish to register for awesomeness?",
            "attachments": [
                {
                    "fallback": "Required plain-text summary of the attachment.",
                    "color": "#a233e1",
                    "title": "SlackReads",
                    "title_link": "https://api.slack.com/",
                    "text": "After accepting it you will receive a link, please use to register yourself.",
                    "callback_id": "register_txt",
                    "actions": [
                        {
                            "name": "register",
                            "text": "Yes",
                            "type": "button",
                            "value": "Yes",
                            "style": "primary"
                        },
                    ],
                    "thumb_url": "http://example.com/path/to/thumb.png",
                    "footer": "SlackReads",
                    "footer_icon": "https://raw.githubusercontent.com/ketanbhatt/block-slack-users/master/icons/icon25"
                                   "6.png",
                    # "ts": 123456789
                }
            ]
        }
    return JsonResponse(data, status=200)


# Button Responses
def btn_response(request):
    if request.method == 'POST':
        payload = json.loads(request.POST.get('payload'))
        user_id = payload.get('user').get('id')
        team_id = payload.get('team').get('id')
        print user_id, team_id
        url = "http://724554db.ngrok.io/auth?u_id=" + user_id + "&t_id=" + team_id
        # Response to send after button click
        data = {
            "response_type": "ephemeral",
            "replace_original": True,
            "attachments": [
                {
                    "fallback": "Required plain-text summary of the attachment.",
                    "color": "#36a64f",
                    "title": "Register at SlackReads",
                    "title_link": url,
                    "text": "Click the Above Link to Register",
                    "callback_id": "register_txt",
                    "footer": "SlackReads",
                    "footer_icon": "https://raw.githubusercontent.com/ketanbhatt/block-slack-users/master/icons/icon25"
                                   "6.png",
                }
            ]
        }
        return JsonResponse(data, status=200)


# First Time Required for Slack Event to verify
def hit(request):
    if request.method == 'POST':
        # Required for Setting up App First for Slack
        response = ast.literal_eval(request.body)
        data = {
            'challenge': response.get('challenge'),
        }
        return JsonResponse(data, status=200)


# Returns on every Reaction Event
def event(request):
    if request.method == 'POST':
        response = ast.literal_eval(request.body)
        # print response
        # Check if reaction is spiral_note
        team = response.get('team_id')
        user = response.get('event').get('user')
        ts = response.get('event').get('item').get('ts')
        channel = response.get('event').get('item').get('channel')
        emo_reaction = response.get('event').get('reaction')
        split_ts = ts.split('.')
        new_ts = split_ts[0] + "" + split_ts[1]
        # Check If reaction is 'spiral_note_pad'
        if emo_reaction == 'spiral_note_pad':
            # Check if user is registered
            db_ref = (ref.child(team).child(user)).get()
            if type(db_ref) is dict:
                code = db_ref.get('code')
                print ("User is Registered")
                # Check for URL in message
                url = "https://slack.com/api/channels.history?token={slack_token}&channel={channel}" \
                      "&latest={latest}&inclusive=true&count=1".format(
                    slack_token=SLACK_TOKEN,
                    channel=channel, latest=ts)
                h_response = requests.get(url)
                text = json.loads(h_response.content)
                message = text.get('messages')[0].get('text')
                message = message[1:-1]
                print message
                # Save message link in cache
                query = team+"_"+user+"_"+new_ts
                cache_check = cache_ref.get().get(query)
                if type(cache_check) is dict:
                    print ("Added")
                    return HttpResponse(status=200)
                else:
                    print (2)
                    # check = cache_ref.get().get(query).get('added')
                    cache_ref.child(query).set({
                        'added': False,
                    })
                    save(team, user, message, query)
            else:
                print ('Unregistered User')
                return HttpResponse(status=200)
        return HttpResponse("Text")
    return HttpResponse(status=200)


# DB Test View
def db(request):
    id = "123455"
    test = cache_ref.get().get('yz')
    print type(test),test
    # test.set(
    #     {
    #         "link": "Test",
    #     }
    # )
    return HttpResponse("yo")


# Pocket Functions
def save(team, user, message, query):
        db_ref = (ref.child(team).child(user)).get()
        token = db_ref.get('p_token')
        add_url = 'https://getpocket.com/v3/add'
        add_data = {
            'url': message,
            'consumer_key': POCKET_API_KEY,
            'access_token': token
        }
        cache_ref.child(query).update({
            'added': True,
        })
        save_post = requests.post(add_url, add_data)
        print ('****Added****')
        return HttpResponse(status=200)


# First Time when someone hits /auth, Auth process is started and code is generated and user is redirected to URI
def auth(request):
    # Get u_id and t_id
    u_id = request.GET.get('u_id')
    t_id = request.GET.get('t_id')
    url = 'https://getpocket.com/v3/oauth/request'
    redirect_uri = "http://724554db.ngrok.io/redirect"
    data = {
        'consumer_key': POCKET_API_KEY,
        'redirect_uri': redirect_uri
    }
    print u_id, t_id
    # Generate Pocket Code
    test = requests.post(url, data)
    code = test.content
    code = code[5:]
    # Store Team Id and User ID from Slack
    slack_ref = ref.child(t_id)
    team_ref = slack_ref.child(u_id)
    team_ref.set({
        'code': code,
    })
    new_redirect_uri = 'http://724554db.ngrok.io/redirect?id=' + u_id + '.' + t_id  # Enter the Redirect URI
    # Redirect required for token generation
    auth_url = "https://getpocket.com/auth/authorize?request_token={code}&redirect_uri={new_redirect_uri}".format(
        code=code, new_redirect_uri=new_redirect_uri)
    return redirect(auth_url)


# Generate Token and Saves into DB
def auth_redirect(request):
    print request.GET
    # Fetch t_id and u_id
    ids = request.GET.get('id')
    u_id = (ids.split("."))[0]
    t_id = (ids.split("."))[1]
    print u_id, t_id
    # Fetch code from DB
    db_ref = ref.child(t_id).child(u_id)
    query = db_ref.get()
    code = query.get('code')
    url = 'https://getpocket.com/v3/oauth/authorize'
    data = {
        'consumer_key': POCKET_API_KEY,
        'code': code
    }
    auth_token = (requests.post(url, data)).content
    access_token, username = auth_token.split("&")
    token = access_token[13:]
    username = username[9:]
    # Store Pocket Token in DB
    db_ref.update({
        'p_token': token
    })
    print ('Yuhooooo, \n Token Generated')
    return HttpResponse('You are Registered, Go on and Save awesomeness from Slack')


def index(request):
    if request.method == 'GET':
        return HttpResponse("<h1>Welcome To Slack Reads </h1>")


