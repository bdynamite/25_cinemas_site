import json

from flask import Flask, render_template
from cinemas import get_films
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
sched = BackgroundScheduler()
sched.add_job(get_films, 'interval', minutes=10)


@app.route('/')
def films_list():
    with open('films.json', 'r', encoding='utf-8') as json_data:
        films_data = json.load(json_data)
    return render_template('template.html', **films_data)

if __name__ == "__main__":
    sched.start()
    app.run()
