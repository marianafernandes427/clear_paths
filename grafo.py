import requests

api_key = "86ddf3e584f443a298a171037261904"

def get_current_weather(location):
    url = "http://api.weatherapi.com/v1/current.json"

    params = {
        "key": api_key,
        "q": location,
        "aqi": "no",
        "lang": "pt"
    }

    data = requests.get(url, params=params).json()

    weather = {
        "city": data["location"]["name"],
        "country": data["location"]["country"],
        "temp_c": data["current"]["temp_c"],
        "feelslike_c": data["current"]["feelslike_c"],
        "wind_kph": data["current"]["wind_kph"],
        "rain": 1 if "rain" in data["current"]["condition"]["text"].lower() else 0,
        "condition": data["current"]["condition"]["text"]
    }

    return weather


def assign_weather_to_graph(G, weather):
    for node in G.nodes:
        G.nodes[node]["temp"] = weather["temp_c"]
        G.nodes[node]["wind"] = weather["wind_kph"]
        G.nodes[node]["rain"] = weather["rain"]
        G.nodes[node]["condition"] = weather["condition"]
        