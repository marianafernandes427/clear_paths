import requests

url = "weatherapi.com/weather/q/guimaraes-braga-portugal-2003073" # web scraping

api_key = "86ddf3e584f443a298a171037261904"

def get_current_weather(location):
    url = "http://api.weatherapi.com/v1/current.json"

    params = {
        "key": api_key,
        "q": location,
        "aqi": "no",
        "lang" : "pt"
    }

    response = requests.get(url, params=params)
    data = response.json()

    weather = {
        "Cidade": data["location"]["name"],
        "País": data["location"]["country"],
        "temp_c": data["current"]["temp_c"],
        "sensacao_termica_c": data["current"]["feelslike_c"],
        "wind_kph": data["current"]["wind_kph"],
        "condição": data["current"]["condition"]["text"]
    }

    return weather


# exemplo
print(get_current_weather("Guimarães"))


