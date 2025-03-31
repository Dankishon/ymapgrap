import csv
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class CoordinateGrabber:

    def __init__(self, org_type, lat_range, lon_range, step=0.02, per_cell_limit=20):
        self.org_type = org_type
        self.lat_range = lat_range
        self.lon_range = lon_range
        self.step = step
        self.per_cell_limit = per_cell_limit
        self.results = []
        self.seen_links = set()

    def grab_data(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=ru-RU')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        for lat in self.lat_range:
            for lon in self.lon_range:
                print(f"\n📍 Координаты: lat={lat}, lon={lon}")
                url = f"https://yandex.ru/maps/?ll={lon},{lat}&z=14"
                driver.get(url)
                sleep(5)

                try:
                    driver.add_cookie({'name': 'yandex_gid', 'value': '213'})
                    driver.add_cookie({'name': 'spravka', 'value': 'lang=ru_RU'})
                    driver.refresh()
                    sleep(3)

                    search_input = driver.find_element(By.CLASS_NAME, 'input__control')
                    search_input.clear()
                    search_input.send_keys(self.org_type)
                    sleep(1)
                    search_input.send_keys(Keys.RETURN)
                    print(f"🔍 Поиск: {self.org_type}")
                    sleep(6)

                    org_links = set()
                    for _ in range(10):
                        driver.execute_script("window.scrollBy(0, 2000);")
                        sleep(2)
                        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/org/"]')
                        for el in elements:
                            href = el.get_attribute("href")
                            if href and "/org/" in href and all(x not in href for x in ["/gallery", "/reviews"]):
                                org_links.add(href)
                        if len(org_links) >= self.per_cell_limit:
                            break

                    new_links = list(org_links - self.seen_links)
                    print(f"🔗 Новых карточек: {len(new_links)}")
                    self.seen_links.update(new_links)

                    for i, link in enumerate(new_links, 1):
                        print(f"➡️ [{i}/{len(new_links)}] {link}")
                        driver.get(link)
                        sleep(4)
                        soup = BeautifulSoup(driver.page_source, "html.parser")

                        name = self.get_text(soup, 'orgpage-header-view__header')
                        address = self.get_text(soup, 'orgpage-header-view__address')
                        phone = self.get_phone(driver)
                        site = self.get_site(soup)
                        rating = self.get_rating(soup)
                        hours = self.get_hours(soup)

                        self.results.append({
                            "Название": name,
                            "Адрес": address,
                            "Телефон": phone,
                            "Сайт": site,
                            "Рейтинг": rating,
                            "Часы работы": hours,
                            "Ссылка": link,
                            "lat": lat,
                            "lon": lon
                        })

                except Exception as e:
                    print(f"❌ Ошибка в точке {lat}, {lon}: {e}")

        driver.quit()
        self.save_csv()

    def get_text(self, soup, class_name):
        try:
            block = soup.find(class_=class_name)
            return block.get_text(strip=True) if block else ""
        except:
            return ""

    def get_phone(self, driver):
        try:
            try:
                show_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Показать телефон')]")
                driver.execute_script("arguments[0].click();", show_btn)
                sleep(1)
            except NoSuchElementException:
                pass

            phone_element = driver.find_element(By.CSS_SELECTOR, 'a[href^="tel:"]')
            return phone_element.text.strip() if phone_element else "Нет телефона"
        except:
            return "Нет телефона"

    def get_site(self, soup):
        try:
            site_link = soup.find("a", href=lambda href: href and href.startswith("http"), text=lambda t: t and "сайт" in t.lower())
            if site_link:
                return site_link["href"]
            contact_block = soup.select_one('.orgpage-contact-item-view__content')
            if contact_block:
                http_links = contact_block.select('a[href^="http"]')
                return http_links[0]["href"] if http_links else "Нет сайта"
            return "Нет сайта"
        except:
            return "Ошибка"

    def get_rating(self, soup):
        try:
            rating_tag = soup.select_one('span.business-rating-badge-view__rating-text')
            return rating_tag.get_text(strip=True) if rating_tag else "Нет рейтинга"
        except:
            return "Ошибка"

    def get_hours(self, soup):
        try:
            items = soup.select('div.business-working-status-view__day')
            return "; ".join(item.get_text(strip=True) for item in items) if items else "Нет данных"
        except:
            return "Ошибка"

    def save_csv(self):
        keys = ["Название", "Адрес", "Телефон", "Сайт", "Рейтинг", "Часы работы", "Ссылка", "lat", "lon"]
        with open("results.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.results)
        print("💾 CSV сохранён: results.csv")


def main():
    org_type = input("Тип организации (например, Стоматология): ")

    # 📍 Координатная сетка по Москве
    lat_range = [round(x, 4) for x in frange(55.55, 55.95, 0.02)]
    lon_range = [round(x, 4) for x in frange(37.35, 37.85, 0.02)]

    grabber = CoordinateGrabber(org_type, lat_range, lon_range, step=0.02, per_cell_limit=20)
    grabber.grab_data()


def frange(start, stop, step):
    while start < stop:
        yield start
        start += step


if __name__ == '__main__':
    main()
