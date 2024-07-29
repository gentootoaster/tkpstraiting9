import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_links(url):
    response = requests.get(url)
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    links = []
    for link in soup.find_all('a', href=True):
        full_url = urljoin(url, link['href'])
        links.append(full_url)
    return links

def search_name_on_page(url, name):
    response = requests.get(url)
    if response.status_code != 200:
        return False
    
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()
    if name in text:
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > 2: 
                name_cell = cells[2].get_text()
                if name in name_cell:
                    print("Вот что я нашел:")
                    print(f"Рейтинг: {cells[0].get_text()}")
                    print(f"Какая-то лажа: {cells[1].get_text()}")
                    print(f"Имя: {cells[2].get_text()}")
                    print(f"Доки: {cells[3].get_text()}")
                    print(f"Средний балл: {cells[4].get_text()}")
                    return True
    return False

def search_name_on_website(base_url, name, max_pages=100):
    visited_pages = set()
    pages_to_visit = [base_url]
    found = False
    
    while pages_to_visit and len(visited_pages) < max_pages:
        current_url = pages_to_visit.pop(0)
        if current_url in visited_pages:
            continue
        
        print(f"Пим-пам-пом... {current_url}")
        visited_pages.add(current_url)
        
        if search_name_on_page(current_url, name):
            found = True
            break
        
        for link in get_links(current_url):
            if link not in visited_pages and urlparse(link).netloc == urlparse(base_url).netloc:
                pages_to_visit.append(link)
    
    if not found:
        print(f"Имя '{name}' не найдено на странице.")
    return found

base_url = 'https://tkpst.ru/applicants/rating9/'
name_to_search = 'Лобачев Арсений Сергеевич'

result = search_name_on_website(base_url, name_to_search)