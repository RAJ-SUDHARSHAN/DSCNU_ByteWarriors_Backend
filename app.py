import os
from dotenv import load_dotenv
from supabase import create_client, Client
from collections import defaultdict

from flask import Flask, request, Response

load_dotenv()
app = Flask(__name__)
SUPABASE_PROJECT_URL: str = os.getenv('SUPABASE_PROJECT_URL')
SUPABASE_API_KEY: str = os.getenv('SUPABASE_API_KEY')
# supabase: Client = create_client(supabase_url = "https://bjohjhosfijhzqnrbvug.supabase.co", supabase_key= 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJqb2hqaG9zZmlqaHpxbnJidnVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NzAwOTQxNjYsImV4cCI6MTk4NTY3MDE2Nn0.4bcyNUramrQ7zczf0M32pi05BwfODesDK12kYTVYTb4')
supabase: Client = create_client(
    supabase_url=SUPABASE_PROJECT_URL, supabase_key=SUPABASE_API_KEY)

# print('url: ', SUPABASE_PROJECT_URL)
# print('key: ', SUPABASE_API_KEY)


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
        'id', parent_user_id).execute().data[0]['user_type']

    if (user_type == 'parent'):
        tracked_user_id = supabase.table('track_location').select(
            '*').eq('user_id', parent_user_id).execute()
        tracked_user_id.count = len(tracked_user_id.data)
        return Response(tracked_user_id.json(), status=200)
    return Response("Bad Request", status=400)

def getJsonValues(data):
    res = defaultdict(list)
    for sub in data:
        for key in sub:
            res[key].append(sub[key])
    return (dict(res))

def flatten(l):
    return [item for sublist in l for item in sublist]

@app.route('/getchildlocation', methods=['POST'])
def getChildLocation():
    data = request.get_json()

    parent_user_id = int(data['parent_user_id'])
    child_user_id = int(data['child_user_id'])

    parent_user_type = supabase.table('user_table').select('user_type').eq(
        'id', parent_user_id).execute().data[0]['user_type']
    child_user_type = supabase.table('user_table').select('user_type').eq(
        'id', child_user_id).execute().data[0]['user_type']

    if (parent_user_type == 'parent' and child_user_type == 'child'):
        tracked_user_id = supabase.table('track_location').select(
            'tracking_user_id').eq('user_id', parent_user_id).execute().data

        if (child_user_id in flatten(list(getJsonValues(tracked_user_id).values()))):
            child_location = supabase.table('user_location').select(
                'lat_long').eq('user_id', child_user_id).execute().data
            return Response(child_location[0]['lat_long'][-1], status=200)
    return Response("Bad Request", status=400)


if __name__ == '__main__':
    app.run(debug=True)
