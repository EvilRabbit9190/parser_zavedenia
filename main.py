import json, requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

parser_links = []
website = "https://burgas.zavedenia.com"
data = {"restaurants": []}
pages = 7

def get_links():
    """
        Get all links restaurants
    """
    for page in range(1, pages + 1):
        url = f"{website}/restaurant_9/{page}"
        response = requests.get(url).text
        soup = BeautifulSoup(response, "lxml")
        links = soup.find_all("a", class_="item-link-desktop")

        for link in links:
            parser_links.append(link.get("href"))

def parser_info():
    """
        Parsing information about restaurant
    """
    options = webdriver.ChromeOptions()
    options.headless = True

    browser = webdriver.Chrome(
        executable_path="browser/chromedriver.exe",
        options=options
    )

    for idx, link in enumerate(parser_links):
        print('Index: ', idx)
        url = f"{website}{link}"
        print(url)
        browser.get(url)

        try:
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "zavedenie-title"))
            )
            # Click Phone link
            try:
                browser.execute_script("const phone_block = document.querySelector('.phone-venue').click();")
            except Exception as exc:
                pass
            # Click See more
            try:
                browser.execute_script("const main_block_about = document.querySelector('.profile-additional-info'); const sub_block_about = main_block_about.querySelector('.section'); const more_about = sub_block_about.querySelector('a').click();")
            except Exception as exc:
                pass
        except Exception as exc:
            print("Exceptio title restaurant", exc)
        
        
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')

        summary = soup.find("div", {"class": "summary"})
        stats = summary.find("div", {"class": "venue-stats"})
        zavedenie_title = stats.find("h1", {"id": "zavedenie-title"}).text
        category = stats.find("h2", {"class": "type"}).find("a").getText().strip()
        logo = summary.find("img", {"class": "profile-logo"})["src"]

        # ========== Rating Socials ==========
        rating_socials = stats.find("div", {"class": "venue-rating-socials"})
        rating = rating_socials.find(attrs={"title": "Rating"}).getText().strip()
        visits_block = rating_socials.find(attrs={"title": "Visits"})
        visits = visits_block.findChildren("span", recursive=False)[1].getText().strip()
        votes_up = rating_socials.find("span", {"id": "votes-up"}).getText().strip()
        votes_down = rating_socials.find("span", {"id": "votes-down"}).getText().strip()


        # ========== General Info ==========
        general_info_block = soup.find("div", {"class": "general-info"})
        general_info = general_info_block.find_all("p", {"class": "ellipsis"})
        places = general_info[0].getText().strip()
        prices = general_info[1].getText().strip()
        openRest = general_info[2].getText().strip()
        phone_block = general_info_block.find_all("a", {"class": "phone-venue"})
        phone = None
        if len(phone_block) == 1:
            phone = phone_block[0].getText().strip()
        elif len(phone_block) > 1:
            phone = []
            for element in phone_block:
                phone.append(element.getText().strip())
        else:
            phone = None


        # ========== Additional information ==========
        additional_info = soup.find("div", {"class": "profile-additional-info"})
        about_rest = additional_info.find("div", {"class": "row section"}).find("p").getText().strip().replace("... Скрий описанието", "")
        section_half = additional_info.find_all("div", {"class": "section-half"})

        left_section_h3 = section_half[0].find_all("h3", {"class": "caption"})
        left_section_p = section_half[0].find_all("p", {"class": "text-small"})
        if len(section_half) == 2:
            right_section_h3 = section_half[1].find_all("h3", {"class": "caption"})
            right_section_p = section_half[1].find_all("p", {"class": "text-small"})
            for h3, p in zip(right_section_h3, right_section_p):
                h3 = h3.getText().strip()
                p = p.getText().strip()
                if h3 == 'кухня':
                    kitchen = p
                elif h3 == 'Екстри':
                    extras = p

        type_restaurant = None
        suitable = None
        kitchen = None
        extras = None
        music = None

        for h3, p in zip(left_section_h3, left_section_p):
            h3 = h3.getText().strip()
            p = p.getText().strip()
            if h3 == 'Подходящо За':
                suitable = p
            elif h3 == 'Тип Заведение':
                type_restaurant = p
            elif h3 == 'Музика':
                music = p

        last_idx = None

        if len(parser_links) == idx + 1:
            last_idx = "End"

        add_to_file(zavedenie_title, category, logo, rating, visits, votes_up, votes_down, places, 
                    prices, openRest, phone, about_rest, suitable, music, type_restaurant, kitchen, extras, last_idx)

    browser.quit()

def add_to_file(name, category, logo, rating, visits, votes_up, votes_down, places,
                prices, openRest, phone, about_rest, suitable, music, type_restaurant, kitchen, extras, idx = None):
    """
        Add to csv file
    """

    if not phone:
        phone = "None"
    elif type(phone) == str:
        pass
    elif type(phone) == list:
        phone = f"{phone[0]}, {phone[1]}"

    data["restaurants"].append({
        'name': f"{str(name)}",
        'category': f"{str(category)}",
        'image': f'{str(logo)}',
        'rating': f'{str(rating)}',
        'visits': f'{str(visits)}',
        'votes_up': f'{str(votes_up)}',
        'votes_down': f'{str(votes_down)}',
        'places': f'{str(places)}',
        'prices': f'{str(prices)}',
        'open': f'{str(openRest)}',
        'phone': f'{phone}',
        'about_rest': f'{str(about_rest)}',
        'suitable': f'{"None" if suitable == None else str(suitable)}',
        'music': f'{"None" if music == None else str(music)}',
        'type_restaurant': f'{"None" if type_restaurant == None else str(type_restaurant)}',
        'kitchen': f'{"None" if kitchen == None else str(kitchen)}',
        'extras': f'{"None" if extras == None else str(extras)}'
    })
    
    if idx == "End":
        json_string = json.dumps(data)
        
        with open('result/restaurants_info.json', 'w', encoding='utf-8') as file:
            file.write(json_string)
            file.close()

get_links()

print(len(parser_links))

parser_info()
