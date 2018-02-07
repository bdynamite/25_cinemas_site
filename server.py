import tempfile

from flask import Flask, render_template
from werkzeug.contrib.cache import FileSystemCache
from cinemas_old import get_films

app = Flask(__name__)
temp_dir = tempfile.mkdtemp()
cache = FileSystemCache(cache_dir=temp_dir)


@app.route('/')
def films_list():
    films_data = get_films_from_cache()
    return render_template('template.html', **films_data)


def get_films_from_cache():
    films = cache.get('films')
    if films is None:
        films = get_films()
        cache.set('films', films, timeout=3 * 60 * 60)
    return films


if __name__ == '__main__':
    app.run()
