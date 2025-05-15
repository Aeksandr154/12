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
    """Registers a new user by saving credentials to the user file."""
    with open(USER_FILE, 'a') as f:
        f.write(f'{username}:{password}\n')


def authenticate_user(username, password):
    """Authenticates a user by checking credentials against the user file."""
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

    return render_template('index.html', summary=summary, image_url=image_url, search_history=search_history, show_history=show_history, username=session['username'])


if __name__ == "__main__":
    if not os.path.exists(USER_FILE):
        open(USER_FILE, 'a').close()
    app.run(debug=True)