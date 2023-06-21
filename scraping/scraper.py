import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from langdetect import detect

chrome_options = Options() # faster to start the driver just once, not once per call to contentfinder...
chrome_options.add_argument('--headless')
driver = webdriver.Chrome('chromedriver', options=chrome_options)

def contentfinder(url):#, driver):

    # Send a GET request to the URL and parse the HTML content with BeautifulSoup
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check if the page uses JavaScript
    try:
        if "javascript" in soup.find("html").get("class", []):
            # Use Selenium to load the JavaScript content and get the page source
            #driver = webdriver.Chrome()
            driver.get(url)
            html = driver.page_source
        else:
            html = requests.get(url).text
    except Exception:
        pass

    article = None
    t = soup.find('title')
    title = t.string if t is not None else None
    try:
        lang = detect(soup.body.get_text())
    except Exception:
        lang = None

    # Look for the <article>, <div>, or <section> tags that contain the main article content
    article = soup.find("article") or soup.find("div", class_="article") or soup.find("section", class_="article")

    # If the <article>, <div>, or <section> tags are not found, look for elements with specific CSS classes
    if not article:
        article = soup.find("div", class_="entry-content") or soup.find("div", class_="main-content")

    # If the <article>, <div>, or <section> tags are not found, look for the <main> tag
    if not article:
        article = soup.find("main")

    # If the <article>, <div>, <section>, or <main> tags are not found, use a content extraction library
    # if not article:
    #     doc = Document(response.text)
    #     article = BeautifulSoup(doc.summary(html_partial=True), "html.parser")
    
    driver.quit()

    # Returns the parsed article content
    return article, title, lang

def getpageobjects_p(url):

    data = []
    # Define a list of valid tag names
    valid_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    nextentry = ''
    article = contentfinder(url)[0]
    if article is None: return data
    for element in article.find_all():
        # Check if the element is part of the readable article content and has a valid tag name
        if element.name in valid_tags:
            # Print the name of the element and its text content
            nextentry = nextentry + element.get_text(strip=True) + '\n'
            if len(nextentry)>2000:
                if len(nextentry)>4000:
                    continue
                data.append({'text':nextentry, 'url':url})
                nextentry=''
            # print(element.name, ":", element.get_text(strip=True))

    #print('\n\n\n Got data from the urls! \n\n\n')

    return data

def getpagetext_p(url):
    # Define a list of valid tag names
    valid_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    i = 0
    for url in listofurls:
        nextentry = ''
        article = contentfinder(url)[0]
        if article is None: continue
        for element in article.find_all():
            # Check if the element is part of the readable article content and has a valid tag name
            if element.name in valid_tags:
                # Print the name of the element and its text content
                nextentry = nextentry + element.get_text(strip=True) + '\n'
                if len(nextentry)>2000:
                    if len(nextentry)>4000:
                        continue
                    return nextentry, listofurls.index(url)
                # print(element.name, ":", element.get_text(strip=True))

    #print('\n\n\n Got data from the urls! \n\n\n')
    return '', None

def contentfinder_noJS(url):

    timeout = 2

    #print('finding content for: ', url)

    # Send a GET request to the URL and parse the HTML content with BeautifulSoup
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        soup = BeautifulSoup(response.text, "html.parser")

        # Check if the page uses JavaScript
        try:
            if "javascript" in soup.find("html").get("class", []):
                pass
            else:
                html = requests.get(url).text
        except Exception:
            pass

        article = None
        t = soup.find('title')
        title = t.string if t is not None else None
        try:
            lang = detect(soup.body.get_text())
        except Exception:
            lang = None

        # Look for the <article>, <div>, or <section> tags that contain the main article content
        article = soup.find("article") or soup.find("div", class_="article") or soup.find("section", class_="article")

        # If the <article>, <div>, or <section> tags are not found, look for elements with specific CSS classes
        if not article:
            article = soup.find("div", class_="entry-content") or soup.find("div", class_="main-content")

        # If the <article>, <div>, or <section> tags are not found, look for the <main> tag
        if not article:
            article = soup.find("main")

        # If the <article>, <div>, <section>, or <main> tags are not found, use a content extraction library
        # if not article:
        #     doc = Document(response.text)
        #     article = BeautifulSoup(doc.summary(html_partial=True), "html.parser")

        # Returns the parsed article content
        return article, title, lang
    except requests.exceptions.Timeout:
        return None, None, None

def getpagetext(url):
    text = ''
    # Define a list of valid tag names
    valid_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    nextentry = ''
    article = contentfinder_noJS(url)[0]
    if article is None: return '', url
    for element in article.find_all():
        # Check if the element is part of the readable article content and has a valid tag name
        if element.name in valid_tags:
            # Print the name of the element and its text content
            text+=element.get_text(strip=True) + '\n'
            # print(element.name, ":", element.get_text(strip=True))
    #print('\n\n\n Got data from the urls! \n\n\n')
    return (text, url)