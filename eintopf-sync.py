import requests
import json

url = "https://radar.squat.net/api/1.2/search/events.json?fields=title,offline,date_time,body&facets[group][]=436012"
response = requests.get(url)

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

        # Print the formatted output
        print(f"Title: {title}")
        print(f"Time Start: {time_start}")
        print(f"Location: {location}")
        #print(f"Description: {body}")
        print('-' * 40)
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")

