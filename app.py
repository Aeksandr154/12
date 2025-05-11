
from flask import Flask, render_template, request
import wikipedia
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

wikipedia.set_lang("ru")


def get_wiki_info(search_term):
    try:
        page = wikipedia.page(search_term, auto_suggest=False)
        summary = wikipedia.summary(search_term, sentences=3, auto_suggest=False)
        image_url = find_image_url(page.url)  # Используем функцию для поиска URL картинки

        return summary, image_url

    except wikipedia.exceptions.PageError:
        return "Страница не найдена.", None
    except wikipedia.exceptions.DisambiguationError as e:
        return "Неоднозначный запрос. Уточните запрос.", None
    except Exception as e:
        print(f"Произошла общая ошибка: {e}")
        return "Произошла ошибка при поиске.", None


def find_image_url(page_url):
    """Парсит HTML страницы Wikipedia, чтобы найти подходящий URL изображения.

    Args:
        page_url (str): URL страницы Wikipedia.

    Returns:
        str: URL изображения или None, если не найдено.
    """
    try:
        response = requests.get(page_url)
        response.raise_for_status()  # Проверка HTTP статуса
        soup = BeautifulSoup(response.content, 'html.parser')

        # Ищем изображение в таблице infobox (обычно содержит основное изображение)
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            img = infobox.find('img')
            if img and img.has_attr('src'):
                image_url = 'https:' + img['src']  # Полный URL (добавляем https:)
                return image_url

        # Если не нашли в infobox, ищем первое изображение на странице
        img = soup.find('img', {'src': re.compile(r'\.jpg|\.png|\.jpeg')}) # Ищем jpg, png, jpeg
        if img and img.has_attr('src'):
            image_url = 'https:' + img['src']
            return image_url

        return None  # Если ничего не нашли
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе страницы: {e}")
        return None
    except Exception as e:
        print(f"Ошибка при парсинге HTML: {e}")
        return None


@app.route("/", methods=['GET', 'POST'])
def index():
    summary = None
    image_url = None

    if request.method == 'POST':
        search_term = request.form['search_term']
        summary, image_url = get_wiki_info(search_term)

    return render_template('index.html', summary=summary, image_url=image_url)


if __name__ == "__main__":
    app.run(debug=True)