#!/bin/env python

import requests
import json
from bs4 import BeautifulSoup
import os
import sys

# Read environment variables (fail if missing)
EINTOPF_URL = os.environ["EINTOPF_URL"]
RADAR_GROUP_ID = os.environ["RADAR_GROUP_ID"]
EINTOPF_AUTHORIZATION_TOKEN = os.environ["EINTOPF_AUTHORIZATION_TOKEN"]

def strip_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

def query_categories():
    response = requests.get(EINTOPF_URL + "/api/v1/categories/?filters=%7B%7D", headers={
      "Authorization": EINTOPF_AUTHORIZATION_TOKEN,
      "Content-Type": "application/json"
   })

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return False

def eintopf_create_category(name):
    payload = {
        "description": name,
        "headline": name,
        "name": name
    }
    response = requests.post(EINTOPF_URL + "/api/v1/categories/", json=payload, headers={
      "Authorization": EINTOPF_AUTHORIZATION_TOKEN,
      "Content-Type": "application/json"
   })

    if response.status_code == 200:
        data = response.json()
        return data['id']
    else:
        return False

def ensure_and_get_categoryid(category):
    available_categories = query_categories()
    
    for entry in available_categories:
        if entry["name"].lower() == category:
            # Return the matching category ID
            return entry["id"]
    
    # If no matching category is found, create a new one
    category_id = eintopf_create_category(category)
    return category_id

def eintopf_post_event(event: dict):
    payload = {
        "address": "Karlsruhe",
        "category": event['category_id'],
        "description": strip_html_tags(event['description']),
        "image": "",
        "involved": [
            {
                "description": "Anonymous",
                "name": "Anonymous"
            }
        ],
        "lat": 0,
        "lng": 0,
        "location": event['location'],
        "name": event['title'],
        "organizers": [ event['organizer'] ],
        "ownedBy": [ event['organizer'] ],
        "published": True,
        "start": event['time_start'],
        "end": event['time_end'],
        "tags": ["karlsruhe"],
        "topic": event['topic_id'],
    }
    response = requests.post(EINTOPF_URL + "/api/v1/events/", json=payload, headers={
      "Authorization": EINTOPF_AUTHORIZATION_TOKEN,
      "Content-Type": "application/json"
   })

    if response.status_code == 200:
        return True
    else:
        return False

print("Beginning scraping Radar api ...")

response = requests.get("https://radar.squat.net/api/1.2/search/events.json", params={
  "fields": "title,offline,date_time,body,category,uuid,og_group_ref",
  "facets[group][]=": RADAR_GROUP_ID
})

if response.status_code == 200:
    data = response.json()
    events = data["result"]

    radar_events = []

    for event in events:

        event = events[event]
        categories = [cat["name"] for cat in event.get("category", [])]
        category_id = ensure_and_get_categoryid(categories[0])
        new_event = {
            'title': event["title"],
            'time_start': event["date_time"][0]["time_start"],
            'time_end': event["date_time"][0]["time_end"],
            'location': event["offline"][0]['title'],
            'description': event["body"]['value'],
            'category_id': category_id,
            'topic_id': "003387f0-9f28-44e4-ab41-808007bc6586",
            'uuid': event["uuid"],
            'organizer': event["og_group_ref"][0]["title"]
        }

        if eintopf_post_event(new_event):
            print("Event successfully added:")
            print(f"Title: {new_event['title']}")
            print(f"Time Start: {new_event['time_start']}")
            print(f"Location: {new_event['location']}")
            print(f"Category: {categories[0]} ({new_event['category_id']})")
            print(f"Topic: Sonstiges ({new_event['topic_id']})")
            print(f"UUID: {new_event['uuid']}")
            print(f"Organizer: {new_event['organizer']}")
            print('-' * 40)
        else:
            print("Submitting event failed")
            sys.exit(1)
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")

