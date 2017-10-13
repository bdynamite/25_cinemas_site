import json
from concurrent import futures
import pytz
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import random

from bs4 import BeautifulSoup
import requests

MAX_WORKERS = 20
PROXY_URL = 'http://www.freeproxy-list.ru/api/proxy'
AGENT_LIST = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12 AppleWebKit/602.4.8',
    'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64)',
    'Opera/9.80 (Windows NT 6.2; WOW64) Presto/2.12.388 Version/12.17'
]
sched = BlockingScheduler()


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


def get_soup_from_kinopoisk(film_name, proxy_list):
    kinopoisk_url = 'https://www.kinopoisk.ru/index.php'
    url_params = {'first': 'yes', 'kp_query': film_name['name']}

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Agent:{}'.format(random.choice(AGENT_LIST))
    }
    proxy = {'http': random.choice(proxy_list)}

    responce = requests.get(kinopoisk_url, params=url_params, headers=headers, proxies=proxy)
    return BeautifulSoup(responce.text, 'html.parser')


def get_film_data(film_name):
    soup = get_soup_from_kinopoisk(film_name, get_proxies())
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
    return (sorted(films_with_data, key=lambda x: x['rating'], reverse=True)[:count])


def get_proxies():
    params = {'anonymity': 'true', 'token': 'demo'}
    request = requests.get(PROXY_URL, params=params).text
    proxies_list = request.split('\n')
    return proxies_list


if __name__ == '__main__':
    sched.add_job(get_films, 'interval', minutes=10)
    sched.start()
