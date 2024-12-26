#!/bin/env python

import requests
import json
from bs4 import BeautifulSoup

print("hello world")
sys.exit()

# Eintopf config
# Get Authorization token through login request
# http://localhost:3333/api/v1/swagger#/auth/login
eintopf_url = "https://karlsunruh.project-insanity.org"
eintopf_api_endpoint = eintopf_url + "/api/v1/events/"
eintopf_headers = {
    "Authorization": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjJlZTA3MDgzLTVjYzktNGM5MS04ZThkLTFkNjhkNzZhZDc5YiIsIm5iZiI6MTQ0NDQ3ODQwMH0.hDQiwXBpIfEiOLP1QAXb9q8eQeaslIHlLN3CBdkHzQKdH0eZZCViEooIyKdZmoncQ0NQAExaitUbFnn6HcAITy8buBhIep6g0fRrfnTgqYOwelhJCXKySUwLe72sEthElaOfISKhvS9Tss4zd3NkNIfFDBVXMnmtOUXmrmlt7Z-5y9p4IiftqBKRA-Md4Uc6iiylSPi7ZZ0r23p2NrYJMyTiWS7-PfhNUt8GJ7HXjmX08VDTQs2lBnQH4c5n1lLCRkUUGpSgPg_2yBnSWN3z_3gQ_mOBNbvYTI2rc4i5fh6eQMIp4B5iL4Kt4Ebe-ikwQFXQ2INWCmemtQtB2pyVMg",
    "Content-Type": "application/json"
}

# Radar config
radar_group_id = "436012"
radar_api_endpoint = "https://radar.squat.net/api/1.2/search/events.json?fields=title,offline,date_time,body&facets[group][]=" + radar_group_id

def strip_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

def eintopf_post_event(title, location, description, time_start, time_end):
    payload = {
        "address": "Karlsruhe",
        "category": "",
        "description": strip_html_tags(description),
        "image": "",
        "involved": [
            {
                "description": "Anonymous",
                "name": "Anonymous"
            }
        ],
        "lat": 0,
        "lng": 0,
        "location": location,
        "name": title,
        "organizers": ["Anonymous"],
        "ownedBy": ["Anonymous"],
        "published": True,
        "start": time_start,
        "end": time_end,
        "tags": ["karlsruhe"],
        "topic": "Veranstaltung"
    }
    response = requests.post(eintopf_api_endpoint, json=payload, headers=eintopf_headers)

    if response.status_code == 200:
        return True
    else:
        return False

response = requests.get(radar_api_endpoint)

if response.status_code == 200:
    data = response.json()
    events = data["result"]

    radar_events = []

    for event in events:

        event = events[event]
        title = event["title"]
        time_start = event["date_time"][0]["time_start"]
        time_end = event["date_time"][0]["time_end"]
        location = event["offline"][0]['title']
        description = event["body"]['value']

        if eintopf_post_event(title, location, description, time_start, time_end):
            print("Event successfully added:")
            print(f"Title: {title}")
            print(f"Time Start: {time_start}")
            print(f"Location: {location}")
            print('-' * 40)
        else:
            print("Submitting event failed")
            sys.exit(1)
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")

