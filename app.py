import os
from dotenv import load_dotenv
from supabase import create_client, Client
from collections import defaultdict
import haversine as hs
from haversine import Unit

from flask import Flask, request, Response, json
from flask_cors import CORS, cross_origin

import firebase_admin
from firebase_admin import messaging, credentials


load_dotenv()

cred = credentials.Certificate("./gservice.json")
# cred = credentials.Certificate("/home/RajSudharshan/DSCNU_ByteWarriors/gservice.json")
firebase_admin.initialize_app(cred)


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

SUPABASE_PROJECT_URL: str = os.getenv('SUPABASE_PROJECT_URL')
SUPABASE_API_KEY: str = os.getenv('SUPABASE_API_KEY')
supabase: Client = create_client(supabase_url="https://bjohjhosfijhzqnrbvug.supabase.co",
                                 supabase_key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJqb2hqaG9zZmlqaHpxbnJidnVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NzAwOTQxNjYsImV4cCI6MTk4NTY3MDE2Nn0.4bcyNUramrQ7zczf0M32pi05BwfODesDK12kYTVYTb4')
# supabase: Client = create_client(
#     supabase_url=SUPABASE_PROJECT_URL, supabase_key=SUPABASE_API_KEY)


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

# @app.route("/push", methods=['POST'])


def pushNotify(token):
    # This registration token comes from the client FCM SDKs.
    # registration_token = 'YOUR_REGISTRATION_TOKEN'
    registration_token = token

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
    return response


@app.route('/users')
@cross_origin()
def getUsers():

    response = supabase.table('user_table').select('id', 'user_name').execute()
    response.count = len(response.data)
    return response.json()


@app.route('/login', methods=['POST'])
@cross_origin()
def userLogin():
    data = request.get_json()

    login_user_name = data['user_name']
    login_user_password = data['password']

    user_data = supabase.table('user_table').select(
        'id', 'password').eq('user_name', login_user_name).execute().data

    if (user_data):
        print(user_data[0]['id'])
        user_password = user_data[0]['password']

        if (login_user_password == user_password):
            return Response(json.dumps({'message': 'Login Successful', 'user_id': user_data[0]['id'], 'user_name': login_user_name}), status=200)

    return Response(json.dumps({'message': "Incorrect username and password"}), status=200)


@app.route('/getchildid', methods=['POST'])
@cross_origin()
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
    return Response(json.dumps({'message': "Bad Request"}), status=200)


@app.route('/getchildlocation', methods=['POST'])
@cross_origin()
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
            return Response(json.dumps({'location': child_location_lat_long}), status=200)
    return Response(json.dumps({'message': "Bad Request"}), status=200)


@app.route('/checkdistance', methods=['POST'])
@cross_origin()
def checkDistance():
    data = request.get_json()
    registration_token = (data['token'])

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
            if (distance > 0.3):
                push_response = pushNotify(registration_token)
                if (push_response):
                    return Response(json.dumps({'message': "Push Notification successful", 'response': push_response, 'distance': distance}), status=200)
            return Response(json.dumps({'message': "invalid token"}), status=200)
    return Response(json.dumps({'message': "Bad Request"}), status=200)


@app.route("/updatelocation", methods=['POST'])
@cross_origin()
def updateLocation():

    data = request.get_json()

    user_id = int(data['user_id'])
    user_lat_long = data['lat_long']

    user_loc_data = supabase.table('user_location').select(
        'lat_long').eq("user_id", user_id).execute().data

    if (user_loc_data == None):
        return Response(json.dumps({'message': "No Data Available"}), status=200)
    elif (user_loc_data):
        loc_arr = user_loc_data[0]['lat_long']
        loc_arr.append(str(user_lat_long))

        if (len(loc_arr) > 5):
            del loc_arr[0]
        try:
            data = supabase.table('user_location').update(
                {'lat_long': loc_arr}).eq("user_id", user_id).execute()
        except Exception as e:
            print('inside exception', e)
        return Response(json.dumps({'message': "Data Available"}), status=200)
    return Response(json.dumps({'message': "No Data Available"}), status=200)


@app.route('/addchilduser', methods=['POST'])
@cross_origin()
def addChildUser():

    data = request.get_json()

    parent_user_id = int(data['parent_user_id'])
    child_user_id = int(data['child_user_id'])

    parent_user_type = supabase.table('user_table').select('user_type').eq(
        'id', parent_user_id).execute().data
    child_user_type = supabase.table('user_table').select('user_type').eq(
        'id', child_user_id).execute().data

    if (parent_user_type and child_user_type and parent_user_type[0]['user_type'] == 'parent' and child_user_type[0]['user_type'] == 'child'):
        try:
            data = supabase.table('track_location').insert(
                {"user_id": parent_user_id, 'tracking_user_id': child_user_id}).execute()
        except Exception as e:
            print('inside exception', e)
        return Response(json.dumps({'message': "successfully added child user"}), status=200)

    return Response(json.dumps({'message': "No Data Available"}), status=200)


@app.route('/addtoken', methods=['POST'])
@cross_origin()
def addToken():

    data = request.get_json()

    user_id = int(data['user_id'])
    token = (data['token'])

    user_data = supabase.table('user_table').select('*').eq(
        'id', user_id).execute().data
    if (user_data):
        try:
            check_user = supabase.table('user_location').select('user_id').eq(
                'user_id', user_id).execute().data

            if (check_user == []):
                print('inside none')
                data = supabase.table('user_location').insert(
                    {"user_id": user_data[0]['id'], 'user_token': token}).execute()
            else:
                print('inside else')
                data = supabase.table('user_location').update(
                    {"user_id": user_data[0]['id'], 'user_token': token}).eq("user_id", user_id).execute()
        except Exception as e:
            print('inside exception', e)
        return Response(json.dumps({'message': "successfully added child user"}), status=200)

    return Response(json.dumps({'message': "No Data Available"}), status=200)


if __name__ == '__main__':
    app.run(debug=True)
