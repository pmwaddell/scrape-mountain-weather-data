from urllib.request import urlopen


url = f"http://www.mountain-forecast.com/peaks/Dhaulagiri/forecasts/8167"
html = urlopen(url).read().decode("utf-8")
print(html)
