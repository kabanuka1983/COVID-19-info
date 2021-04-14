import requests, time
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from config import *


def get_last_post_datetime_str(save=save_file):
    '''
    Возвращает дату и время последней публикации на канале
    Если дата последней публикации была более 2-х дней назад, возвращает системную дату минус 2 дня
    При отсутствии файла save_file, возвращает системную дату минус 2 дня
    save_file поврежден, возвращает системную дату
    '''
    try:
        with open(save) as file:
            fr = file.read()
            try:
                fr_dt = datetime.strptime(fr, "%d.%m.%Y %H:%M")
                td = datetime.now() - fr_dt
                if td > timedelta(days=2) or td < timedelta(0):
                    return f"{(date.today() - timedelta(days=2)).strftime('%d.%m.%Y')} 00:00"
                else:
                    return fr
            except Exception:
                print(f'Значения в файле "{save}" были изменены, дата обновления с {date.today().strftime("%d.%m.%Y")} 00:00')
                return f"{date.today().strftime('%d.%m.%Y')} 00:00"
    except FileNotFoundError:
        return f"{(date.today() - timedelta(days=2)).strftime('%d.%m.%Y')} 00:00"


def get_soup(url=url_interf, headers=headers):
    req = requests.get(url, headers=headers)
    return BeautifulSoup(req.text, "lxml")

def get_all_post_dict(soup, post_date):
    all_post_articles = soup.find_all(class_="col-13 article-time")
    all_post_dict = {}

    for art in all_post_articles:
        item_art = get_post_datetime(art)
        item_href = get_post_href(art)
        item_title = get_post_title(art)

        if str_to_datetime(item_art) > str_to_datetime(post_date):
            all_post_dict[item_art] = [item_href, item_title]
    return all_post_dict

def get_post_datetime(art):
    return f'{art.find("span").find_next_sibling().string} {art.find("span").string}'

def get_post_href(art):
    return f'{domain}{art.find_previous(class_="grid article").find(class_="article-link").get("href")}'

def get_post_title(art):
    return f'{art.find_previous(class_="grid article").find(class_="article-link").string.strip()}'

def str_to_datetime(str):
    return datetime.strptime(str, "%d.%m.%Y %H:%M")

def main():
    last_post_datetime_str = get_last_post_datetime_str()
    soup = get_soup()
    all_post_dict = get_all_post_dict(soup, last_post_datetime_str)

    if all_post_dict:
        all_pages_list = []
        while all_post_dict:
            all_pages_list.append(all_post_dict)
            url = f'{domain}{soup.find(class_="pager").find("a", class_=False).get("href")}'
            soup = get_soup(url, headers)
            all_post_dict = get_all_post_dict(soup, last_post_datetime_str)
        for page in reversed_list(all_pages_list):
            for post_date, post_href_title in reversed_dict(page).items():
                post_href = post_href_title[0]
                post_title = post_href_title[1]

                send_post(post_href, post_title)
                last_post_datetime_str = post_date
                time.sleep(10)
                with open(save_file, "w") as file:
                    file.write(last_post_datetime_str)
    else:
        print("Новостей нет")

def reversed_list(lst):
    lst.reverse()
    return lst

def reversed_dict(dct):
    return dict(reversed(dct.items()))

def send_post(post_href, post_title, token=token, channel_id=channel_id):
    urltg = "https://api.telegram.org/bot"
    urltg += token
    method = urltg + "/sendMessage"
    data = {
        "chat_id": channel_id,
        "text": f"{post_title}\n{post_href}",
        "disable_web_page_preview": disable_web_page_preview
        }

    r = requests.post(method, data=data)

main()
