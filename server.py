from flask import Flask, render_template
from cinemas import get_films

app = Flask(__name__)


@app.route('/')
def films_list():
    films_data = get_films()
    return render_template('template.html', films=films_data)


@app.route('/test')
def test():
    with open('test.txt', 'r') as test_file:
        return test_file.read()

if __name__ == "__main__":
    app.run()
