import requests
import random
from bs4 import BeautifulSoup

def get_image_link(search):
    url = "https://www.google.com/search?q={}&site=webhp&tbm=isch".format(search)
    d = requests.get(url).text
    tags = BeautifulSoup(d,'html.parser').find_all('img')
    urls = [img['src'] for img in tags if img['src'].startswith("http")]

    return random.choice(urls)
