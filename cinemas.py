import json
from concurrent import futures
import pytz
import datetime

from bs4 import BeautifulSoup
import requests

MAX_WORKERS = 20


def get_soup_from_afisha():
    afisha_url = 'https://www.afisha.ru/msk/schedule_cinema/'
    responce = requests.get(afisha_url)
    return BeautifulSoup(responce.text, 'html.parser')


def convert_html_to_film_info(film_html):
    return {'name': film_html.text, 'link': film_html.a['href']}


def get_films_from_afisha(soup, min_cinemas_count=30):
    all_films = soup.find_all(attrs={'class': 'object s-votes-hover-area collapsed'})
    films = [convert_html_to_film_info(film.find(attrs={'class': 'usetags'}))
             for film in all_films
             if len(film.find_all(attrs={'class': 'b-td-item'})) >= min_cinemas_count]
    return films


def get_soup_from_kinopoisk(film_name):
    kinopoisk_url = 'https://www.kinopoisk.ru/index.php'
    url_params = {'first': 'yes', 'kp_query': film_name['name']}
    responce = requests.get(kinopoisk_url, params=url_params)
    return BeautifulSoup(responce.text, 'html.parser')


def get_film_data(film_name):
    soup = get_soup_from_kinopoisk(film_name)
    rating_tag = soup.find(attrs={'class': 'rating_ball'})
    if rating_tag:
        rating = float(rating_tag.text)
    else:
        rating = 0
    votes_tag = soup.find(attrs={'class': 'ratingCount'})
    if votes_tag:
        votes = int(''.join(votes_tag.text.split()))
    else:
        votes = 0
    image_link = soup.find(attrs={'itemprop': 'image'}).attrs['src']
    author_html = soup.find(attrs={'itemprop': 'director'})
    author = {'name': author_html.a.text, 'link': 'https://www.kinopoisk.ru' + author_html.a['href']}
    synopsys = soup.find(attrs={'class': 'brand_words film-synopsys'}).text
    return {
        'film_name': film_name,
        'rating': rating,
        'votes': votes,
        'image_link': image_link,
        'author': author,
        'synopsys': synopsys
    }


def save_data_in_json(films_data):
    time = get_time()
    data_dict = {'time': time, 'films': films_data}
    with open('films.json', 'w', encoding='utf-8') as json_file:
        json.dump(data_dict, json_file)


def get_time():
    tz = pytz.timezone('Europe/Moscow')
    return str(datetime.datetime.now(tz))[:19]


def get_films(count=10):
    films_list = get_films_from_afisha(get_soup_from_afisha())
    workers = min(len(films_list), MAX_WORKERS)
    with futures.ThreadPoolExecutor(workers) as excecutor:
        films_with_data = list(excecutor.map(get_film_data, films_list))
    save_data_in_json(sorted(films_with_data, key=lambda x: x['rating'], reverse=True)[:count])


if __name__ == '__main__':
    get_films()
