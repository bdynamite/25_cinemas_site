from concurrent import futures
import pytz
import datetime
import random
import functools

from bs4 import BeautifulSoup
import requests

MAX_WORKERS = 20
PROXY_URL = 'https://webanetlabs.net/freeproxylist/proxylist_at_04.02.2018.txt'
AGENT_LIST = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12 AppleWebKit/602.4.8',
    'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64)',
    'Opera/9.80 (Windows NT 6.2; WOW64) Presto/2.12.388 Version/12.17'
]


def get_soup_from_afisha():
    afisha_url = 'https://www.afisha.ru/msk/schedule_cinema/'
    response = requests.get(afisha_url)
    return BeautifulSoup(response.text, 'html.parser')


def convert_html_to_film_info(film_html):
    return {'name': film_html.text, 'link': film_html.a['href']}


def get_films_from_afisha(soup, min_cinemas_count=30, max_count=10):
    all_films = soup.find_all(attrs={'class': 'object s-votes-hover-area collapsed'})
    films = [convert_html_to_film_info(film.find(attrs={'class': 'usetags'}))
             for film in all_films
             if len(film.find_all(attrs={'class': 'b-td-item'})) >= min_cinemas_count]
    return films[:max_count]


def get_soup_from_kinopoisk(film_name, proxies):
    kinopoisk_url = 'https://www.kinopoisk.ru/index.php'
    url_params = {'first': 'yes', 'kp_query': film_name['name']}
    headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Agent:{}'.format(random.choice(AGENT_LIST))
        }
    proxy_url = {'http': random.choice(proxies)}
    response = requests.get(kinopoisk_url, params=url_params, headers=headers, proxies=proxy_url)
    return BeautifulSoup(response.text, 'html.parser')


def get_film_data(film_name, soup):
    if not soup:
        return
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


def get_time():
    tz = pytz.timezone('Europe/Moscow')
    return datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')


def get_films():
    films_list = get_films_from_afisha(get_soup_from_afisha())
    workers = min(len(films_list), MAX_WORKERS)
    proxies_list = get_proxies()
    with futures.ThreadPoolExecutor(workers) as executor:
        soups_from_kinopoisk = list(executor.map(functools.partial(get_soup_from_kinopoisk,
                                                                   proxies=proxies_list), films_list))
    films_data = [get_film_data(film, soup) for film, soup in zip(films_list, soups_from_kinopoisk)]
    top_films = sorted(films_data, key=lambda x: x['rating'], reverse=True)
    return {'time': get_time(),
            'films': top_films}


def get_proxies():
    response = requests.get(PROXY_URL).text
    return response.split('\r\n')[1:-1]


if __name__ == '__main__':
    films = get_films()
