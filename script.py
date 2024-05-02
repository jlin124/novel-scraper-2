from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from PIL import Image
import os
from pathlib import Path
from selenium.webdriver.common.keys import Keys
from time import sleep
import re # importing regex for pattern matching
from tqdm import tqdm
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException


def initialize_browser():
    option = ChromeOptions()
    option.add_argument("--window-size=1920, 1200") # Setting window size
    option.add_argument('--ssl-version-max=tls1.2')
    #option.add_argument('--ignore-certificate-errors-spki-list') # ignoring SSL Errors
    option.add_argument('--ignore-ssl-errors') # ignoring SSL Errors
    option.add_argument('log-level=2') # suppressing all infos, warning, errors

    #Using a user agent to avoid the bot detecting script
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36' 
    option.add_argument('user-agent={0}'.format(user_agent))

    return webdriver.Chrome(options=option) #returning chrome webdriver

# Allowing the user to input into the search bar
def search_novel(browser, user_search):
    # Locates the search bar
    search_bar = browser.find_element(By.XPATH, '/html/body/main/article/div/form/div/input')
    search_bar.click()
    search_bar.clear()
    search_bar.send_keys(user_search)
    search_bar.send_keys(Keys.RETURN)
    # waiting for the results to load
    wait = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/main/article/div/section[1]')))

# Function to find the novels in the search result & return the link when selected
def find_novel(browser, user_search):
    limit = len(browser.find_elements(By.XPATH,'/html/body/main/article/div/section[1]'))
    while limit > 0:
        WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/main/article/div/section[1]')))
        if browser.find_elements(By.XPATH, '/html/body/main/article/div/section[1]/ul/li'):
            for name in browser.find_elements(By.XPATH, '/html/body/main/article/div/section[1]/ul/li'):
                # retrieving the novel titles found
                title = name.find_element(By.TAG_NAME, 'h4').text
                if re.sub(r'\W+', '', user_search).lower() in re.sub(r'\W+', '', title).lower():
                    print(title + '\n')
                    search_input = input("Is this what you are searching for? (y/n): ")
                    if search_input.lower() == 'y':
                        link = name.find_element(By.TAG_NAME, 'a').get_attribute('href')
                        print('Ok, accessing... ' + link)
                        browser.get(link) # Accessing the link
                        return False
                    else:
                        print("Loading new title...\n")
                    limit -= 1
        elif browser.find_elements(By.XPATH, '/html/body/main/article/div/section[1]/center'):
            print('No novel could be found under that name.')
            print('Please try again with a different title. \n')
            return True
    return True

def get_ch_num(browser):
    return browser.find_element(By.XPATH, '/html/body/main/article/header/div[2]/div[2]/div[2]/span[1]/strong').text

def get_title(browser):
    return browser.find_element(By.XPATH, '/html/body/main/article/header/div[2]/div[2]/div[1]/h1').text

def get_img(browser, title):
    img = browser.find_element(By.XPATH, '/html/body/main/article/header/div[2]/div[1]/figure/img').screenshot(title+'.png')

def navigate_list(browser):
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/article/div/nav/a[1]'))).click()

def get_pages(browser):
    links = []
    while True:
        try:
            links.append(browser.current_url)
            browser.find_element(By.CLASS_NAME, "PagedList-skipToNext").click()
        except(ElementNotVisibleException, NoSuchElementException):
            print("links: ", links)
            break
    return links

def get_links(browser, filename):
    with open(filename, 'a+') as f:
        for item in tqdm(browser.find_elements(By.XPATH, '/html/body/main/article/section/ul/li')):
            f.write(item.find_element(By.TAG_NAME, 'a').get_attribute('href') + "\n")
        print('\nRetrieving next page')

def download_chapters(browser, novel_title):
    with open('chapter_links.txt', 'r') as f:
        url = f.readlines()
        for urls in tqdm(url, desc="Downloading chapters"):
            browser.get(urls)
            title = browser.find_elements(By.CLASS_NAME, 'chapter-title')
            chapter_title = str(title[0].text).replace(': ', ' - ').replace('?', '').replace('*', '')
            ch_title = novel_title + chapter_title + '.txt'
            
            os.makedirs(os.path.dirname(ch_title), exist_ok=True)
            with open(ch_title, 'w+', encoding='utf-8') as c:
                c.write(chapter_title + '\n\n')
                for content in browser.find_elements(By.TAG_NAME, 'p'):
                    c.write(str(content.text) + '\n')


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    browser = initialize_browser() # Initializing the web browser
    browser.get('https://www.lightnovelworld.co/search') #Accessing the initial link
    found = True # Initializing found status as True
    while found: # Looping until novel is found
        user_search = input("Enter the novel name (at least 3 characters): ")
        if len(user_search) < 3:
            print("Please enter at least 3 characters.")
            continue

        search_novel(browser, user_search)
        found = find_novel(browser, user_search) # Finding the novel in search results
    #print("new string", novel_title)
    if found == False:
        number = get_ch_num(browser)
        print("The number of chapters found: ", number)
        title = get_title(browser)
        novel_title = title.replace('\'', '') + '\\'
        get_img(browser, title)
        navigate_list(browser)
        page = get_pages(browser)
        print("\nRetrieving chapter links\n")
        for p in page:
            browser.get(p)
            get_links(browser, 'chapter_links.txt')
        print("\nDownloading all chapters of", title, '\n')
        download_chapters(browser, novel_title)

        print("Content saved successfully.")
    os.rename('C:\\Users\\jlin\\pycode\\'+title+'.png', 'C:\\Users\\jlin\\pycode\\'+ novel_title + title +'.png')
    try:
        os.remove('chapter_links.txt')
        print('Successfully removed chapter_links.txt')
    except:
        print('failed to remove chapter_links.txt')

    sleep(2)
    browser.quit()
    exit(0)

if __name__ == "__main__":
    main()
