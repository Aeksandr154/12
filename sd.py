
from flask import Flask, render_template, request, session, redirect, url_for
import wikipedia
import requests
from bs4 import BeautifulSoup
import re
import os


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'your_secret_key_here'

wikipedia.set_lang("ru")


USER_FILE = 'users.txt'


def get_wiki_info(search_term):
    try:
        page = wikipedia.page(search_term, auto_suggest=False)
        summary = wikipedia.summary(search_term, sentences=3, auto_suggest=False)
        image_url = find_image_url(page.url)

        return summary, image_url

    except wikipedia.exceptions.PageError:
        return "Страница не найдена.", None
    except wikipedia.exceptions.DisambiguationError as e:
        return "Неоднозначный запрос. Уточните запрос.", None
    except Exception as e:
        print(f"Произошла общая ошибка: {e}")
        return "Произошла ошибка при поиске.", None


def find_image_url(page_url):
    try:
        response = requests.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            img = infobox.find('img')
            if img and img.has_attr('src'):
                image_url = 'https:' + img['src']
                return image_url

        img = soup.find('img', {'src': re.compile(r'\.jpg|\.png|\.jpeg')})
        if img and img.has_attr('src'):
            image_url = 'https:' + img['src']
            return image_url

        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе страницы: {e}")
        return None
    except Exception as e:
        print(f"Ошибка при парсинге HTML: {e}")
        return None


def register_user(username, password):
    with open(USER_FILE, 'a') as f:
        f.write(f'{username}:{password}\n')


def authenticate_user(username, password):
    if not os.path.exists(USER_FILE):
        return False

    with open(USER_FILE, 'r') as f:
        for line in f:
            stored_username, stored_password = line.strip().split(':')
            if username == stored_username and password == stored_password:
                return True
    return False

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        register_user(username, password)
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверный логин или пароль')
    return render_template('login.html', error=None)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route("/", methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    summary = None
    image_url = None
    search_history = session.get('search_history', [])
    show_history = request.args.get('show_history') == 'true'

    if request.method == 'POST':
        search_term = request.form['search_term']
        summary, image_url = get_wiki_info(search_term)

        if search_term not in search_history:
            search_history.insert(0 , search_term)
            if len(search_history) > 5:
                search_history.pop()
            session['search_history'] = search_history



    html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Поисковик</title>
    <style>
        body {
            font-family: sans-serif;
            text-align: center;
        }
        .rainbow-text {
            font-size: 2em;
            font-weight: bold;
            display: inline-block;
        }
        .rainbow-text span {
            display: inline-block;
            animation: rainbow 2s linear infinite;
        }
        @keyframes rainbow {
            0% { color: red; }
            14% { color: orange; }
            28% { color: yellow; }
            42% { color: green; }
            57% { color: blue; }
            71% { color: indigo; }
            85% { color: violet; }
            100% { color: red; }
        }

        input[type="text"] {
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 5px;
            width: 50%;
            margin-bottom: 20px;
        }

        button {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }

        img {
            max-width: 500px;
            max-height: 400px;
            margin-top: 20px;
        }

        /* Style for the search history */
        .search-history {
            margin-top: 30px;
            text-align: left;
            width: 50%;
            margin-left: auto;
            margin-right: auto; /* Center the history */
        }

        .search-history h3 {
            font-size: 1.2em;
            margin-bottom: 10px;
        }

        .search-history ul {
            list-style: none;
            padding: 0;
        }

        .search-history li {
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }

    </style>
</head>
<body>
    <h1>Привет, {{ username }}!</h1>
    <a href="{{ url_for('logout') }}">Выйти</a>

    <div class="rainbow-text">
        <span>П</span>
        <span>о</span>
        <span>и</span>
        <span>с</span>
        <span>к</span>
        <span>о</span>
        <span>в</span>
        <span>и</span>
        <span>к</span>
    </div>

    <form method="POST">
        <input type="text" name="search_term" placeholder="Введите запрос">
        <button type="submit">Искать</button>
    </form>

    {% if summary %}
        <h2>Результат:</h2>
        <p>{{ summary }}</p>
    {% endif %}

    {% if image_url %}
        <img src="{{ image_url }}" alt="Изображение">
    {% endif %}

    <a href="/?show_history={% if show_history %}false{% else %}true{% endif %}">
        <button>
            {% if show_history %}Скрыть историю{% else %}Показать историю{% endif %}
        </button>
    </a>

    {% if show_history %}
        <div class="search-history">
            <h3>История поиска:</h3>
            <ul>
                {% for term in search_history %}
                    <li>{{ term }}</li>
                {% endfor %}
            </ul>
        </div>
    {% endif %}

</body>
</html>
"""

    html_content = html_content.replace("{{ username }}", session['username'])
    html_content = html_content.replace("{{ url_for('logout') }}", url_for('logout'))


    summary_block = f"<h2>Результат:</h2><p>{summary}</p>" if summary else ""
    image_block = f'<img src="{image_url}" alt="Изображение">' if image_url else ""

    show_history_url = f"/?show_history={'false' if show_history else 'true'}"
    show_history_button_text = "Скрыть историю" if show_history else "Показать историю"

    history_block = ""
    if show_history:
        history_items = "".join(f"<li>{term}</li>" for term in search_history)
        history_block = f"""
        <div class="search-history">
            <h3>История поиска:</h3>
            <ul>
                {history_items}
            </ul>
        </div>
        """

    html_content = html_content.replace("{% if summary %}\n        <h2>Результат:</h2>\n        <p>{{ summary }}</p>\n    {% endif %}", summary_block)
    html_content = html_content.replace("{% if image_url %}\n        <img src=\"{{ image_url }}\" alt=\"Изображение\">\n    {% endif %}", image_block)
    html_content = html_content.replace('<a href="/?show_history={% if show_history %}false{% else %}true{% endif %}">\n        <button>\n            {% if show_history %}Скрыть историю{% else %}Показать историю{% endif %}\n        </button>\n    </a>', f'<a href="{show_history_url}"><button>{show_history_button_text}</button></a>')
    html_content = html_content.replace('{% if show_history %}\n        <div class="search-history">\n            <h3>История поиска:</h3>\n            <ul>\n                {% for term in search_history %}\n                    <li>{{ term }}</li>\n                {% endfor %}\n            </ul>\n        </div>\n    {% endif %}', history_block)



    return html_content


if __name__ == "__main__":
    if not os.path.exists(USER_FILE):
        open(USER_FILE, 'a').close()
    app.run(debug=True)
