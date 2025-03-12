#!/bin/env python

import requests
import json
from bs4 import BeautifulSoup
import os

# Read environment variables (fail if missing)
EINTOPF_URL = os.environ["EINTOPF_URL"]
RADAR_GROUP_ID = os.environ["RADAR_GROUP_ID"]
EINTOPF_AUTHORIZATION_TOKEN = os.environ["EINTOPF_AUTHORIZATION_TOKEN"]

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
    response = requests.post(EINTOPF_URL, json=payload, headers={
      "Authorization": EINTOPF_AUTHORIZATION_TOKEN,
      "Content-Type": "application/json"
   })

    if response.status_code == 200:
        return True
    else:
        return False

print("Beginning scraping Radar api ...")

response = requests.get("https://radar.squat.net/api/1.2/search/events.json?fields=title,offline,date_time,body&facets[group][]=" + RADAR_GROUP_ID)

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

