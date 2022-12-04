import os
from dotenv import load_dotenv
from supabase import create_client, Client
from collections import defaultdict
import haversine as hs
from haversine import Unit

from flask import Flask, request, Response, json

import firebase_admin
from firebase_admin import messaging, credentials


load_dotenv()

cred = credentials.Certificate("./gservice.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)

SUPABASE_PROJECT_URL: str = os.getenv('SUPABASE_PROJECT_URL')
SUPABASE_API_KEY: str = os.getenv('SUPABASE_API_KEY')
supabase: Client = create_client(
    supabase_url=SUPABASE_PROJECT_URL, supabase_key=SUPABASE_API_KEY)


def getJsonValues(data):
    res = defaultdict(list)
    for sub in data:
        for key in sub:
            res[key].append(sub[key])
    return (dict(res))


def flatten(l):
    return [item for sublist in l for item in sublist]


def getDistance(lat1, lat2):
    distance = hs.haversine(tuple(map(float, lat1.split(','))), tuple(
        map(float, lat2.split(','))), unit=Unit.MILES)
    return distance


@app.route('/users')
def getUsers():

    response = supabase.table('user_table').select('id', 'user_name').execute()
    response.count = len(response.data)
    return response.json()


@app.route('/login', methods=['POST'])
def userLogin():
    data = request.get_json()

    login_user_name = data['user_name']
    login_user_password = data['password']

    user_data = supabase.table('user_table').select(
        '*').eq('user_name', login_user_name).execute().data
    user_password = user_data[0]['password']

    if (login_user_password == user_password):
        return Response('Login Successful', status=200)

    return Response("Incorrect username and password", status=400)


@app.route('/getchildid', methods=['POST'])
def getChildId():
    data = request.get_json()

    parent_user_id = data['parent_user_id']

    user_type = supabase.table('user_table').select('user_type').eq(
        'id', parent_user_id).execute().data

    if (user_type and user_type[0]['user_type'] == 'parent'):

        tracked_user_id = supabase.table('track_location').select(
            '*').eq('user_id', parent_user_id).execute()
        tracked_user_id.count = len(tracked_user_id.data)

        return Response(tracked_user_id.json(), status=200)
    return Response("Bad Request", status=400)


@app.route('/getchildlocation', methods=['POST'])
def getChildLocation():
    data = request.get_json()

    parent_user_id = int(data['parent_user_id'])
    child_user_id = int(data['child_user_id'])

    parent_user_type = supabase.table('user_table').select('user_type').eq(
        'id', parent_user_id).execute().data
    child_user_type = supabase.table('user_table').select('user_type').eq(
        'id', child_user_id).execute().data

    if (parent_user_type and child_user_type and parent_user_type[0]['user_type'] == 'parent' and child_user_type[0]['user_type'] == 'child'):
        tracked_user_id = supabase.table('track_location').select(
            'tracking_user_id').eq('user_id', parent_user_id).execute().data
        print('check', list(getJsonValues(tracked_user_id).values()))
        if (child_user_id in flatten(list(getJsonValues(tracked_user_id).values()))):
            child_location = supabase.table('user_location').select(
                'lat_long').eq('user_id', child_user_id).execute().data
            child_location_lat_long = child_location[0]['lat_long'][-1]
            return Response(child_location_lat_long, status=200)
    return Response("Bad Request", status=400)


@app.route('/checkdistance', methods=['POST'])
def checkDistance():
    data = request.get_json()

    parent_user_id = int(data['parent_user_id'])
    child_user_id = int(data['child_user_id'])

    parent_user_type = supabase.table('user_table').select('user_type').eq(
        'id', parent_user_id).execute().data
    child_user_type = supabase.table('user_table').select('user_type').eq(
        'id', child_user_id).execute().data

    if (parent_user_type and child_user_type and parent_user_type[0]['user_type'] == 'parent' and child_user_type[0]['user_type'] == 'child'):
        parent_location = supabase.table('user_location').select(
            'lat_long').eq('user_id', parent_user_id).execute().data
        parent_location_lat_long = parent_location[0]['lat_long'][-1]

        tracked_user_id = supabase.table('track_location').select(
            'tracking_user_id').eq('user_id', parent_user_id).execute().data

        if (child_user_id in flatten(list(getJsonValues(tracked_user_id).values()))):

            child_location = supabase.table('user_location').select(
                'lat_long').eq('user_id', child_user_id).execute().data
            child_location_lat_long = child_location[0]['lat_long'][-1]

            distance = getDistance(
                parent_location_lat_long, child_location_lat_long)
            print(distance)
            # if (distance > 0.3):
            #     push = 0
            #     if (push):
            #         return Response(json.dumps({'message': "Push Notification successful"}), status=200)
            return Response(json.dumps({'distance': distance}), status=200)
    return Response("Bad Request", status=400)


@app.route("/push", methods=['POST'])
def push():
    # This registration token comes from the client FCM SDKs.
    # registration_token = 'YOUR_REGISTRATION_TOKEN'
    registration_token = request.json.get('sub_token')

    # See documentation on defining a message payload.
    message = messaging.Message(
        notification=messaging.Notification(
            title='Push notification successful',
            body='check'
        ),
        token=registration_token,
    )

    # Send a message to the device corresponding to the provided
    # registration token.
    response = messaging.send(message)
    # Response is a message ID string.
    print('Successfully sent message:', response)
    return Response(response, status=200)

# @app.route("/updatelocation", methods=['POST'])
# def updateLocation():

#     update_location = supabase.table('user_location').select(
#         '*').eq('user_name', login_user_name).execute().data


if __name__ == '__main__':
    app.run(debug=True)
