import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from readability import Document
from langdetect import detect
from bs4 import BeautifulSoup, Comment
from courlan import *

chrome_options = Options()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome('chromedriver', options=chrome_options)

# checks if an element contains any anchors, returns a list of links and the associated text
def anchorcheck(element):
    anchors = element.find_all('a')
    if anchors:
        anchorlist = []
        for anchor in anchors:
            if anchor.has_attr('href'):
                anchorlist.append([anchor.get_text(strip=True), anchor['href']])
        return anchorlist
    else:
        return None

def contentfinder(url, driver):

    ## should be set up in the main script
    # ==========
    # # Set up a headless Chrome browser instance with Selenium
    # chrome_options = Options()
    # chrome_options.add_argument('--headless')
    # driver = webdriver.Chrome('chromedriver', options=chrome_options)

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
    lang = detect(soup.body.get_text())

    # Look for the <article>, <div>, or <section> tags that contain the main article content
    article = soup.find("article") or soup.find("div", class_="article") or soup.find("section", class_="article")

    # If the <article>, <div>, or <section> tags are not found, look for elements with specific CSS classes
    if not article:
        article = soup.find("div", class_="entry-content") or soup.find("div", class_="main-content")

    # If the <article>, <div>, or <section> tags are not found, look for the <main> tag
    if not article:
        article = soup.find("main")

    # If the <article>, <div>, <section>, or <main> tags are not found, use a content extraction library
    if not article:
        doc = Document(response.text)
        article = BeautifulSoup(doc.summary(html_partial=True), "html.parser")
    
    driver.quit()

    # Returns the parsed article content
    return article, title, lang

def urlcheck(url, host=None):
    # host = get_host_and_path(url)[0]
    url = normalize_url(url)
    while True:
        if is_not_crawlable(url):
            return None
        elif is_navigation_page(url):
            return None
        elif validate_url(url)[0]:
            return url
        else:
            url = fix_relative_urls(host, url)
            continue

def anchorcheck(element):
    anchors = element.find_all('a')
    if anchors:
        anchorlist = []
        for anchor in anchors:
            if anchor.has_attr('href'):
                anchorlist.append([anchor.get_text(strip=True), anchor['href']])
        return anchorlist
    else:
        return None

def traverse(soup):

    dom_dictionary = {}

    if soup.name is not None:
        dom_dictionary['name'] = soup.name
        dom_dictionary['children'] = [traverse(child) for child in soup.children if not is_empty(child) and not isinstance(child, Comment)]
        dom_dictionary['content'] = ''
    else:
        dom_dictionary['name'] = ''
        dom_dictionary['children'] = []
        dom_dictionary['content'] = str(soup.string)

    return dom_dictionary

def article_to_tree(article, url, title):

    #print(article.prettify())

    # expects a soup object or None
    if article is None: return

    document = [0, url, None, None] # We don't need the # of headings/paragraphs, it can be inferred
    headings = [[0, 'root', title, -1, -1, []]] # _, tag name, text content, sub heading, next heading, paragraphs
    paragraphs = [] # _, tag name, text content, _

    parent_headings = [(None, 0)] # tag, index
    heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span']
    paragraph_tags = ['p', 'ul', 'ol', 'li', 'span']
    #print(traverse(article))
    #pretty(collapse(join(strip(prune(traverse(article))))))
    #print(collapse(join(strip(prune(traverse(article))))))
    flat = flatten(collapse(join(strip(prune(traverse(article))))))
    heading_paragraph_tree(headings, paragraphs, [0], flat['children'])

    #print(collapse(join(strip(prune(traverse(article))))))

    for i in range(len(headings)):
        if headings[i][3] == -1:
            headings[i][3] = None
        if headings[i][4] == -1:
            headings[i][4] = None
    
    return document, headings, paragraphs

def heading_paragraph_tree(headings, paragraphs, parents, elements):

    if len(elements) == 0: return
    #print(f"at {elements[0]=}, {parents=}, {headings=}")

    if not len(parents):
        headings.append([0, elements[0]['name'], elements[0]['content'], -1, -1, []])
        parents = [0]
        heading_paragraph_tree(headings, paragraphs, parents, elements[1:])
        return

    if elements[0]['name'] in ['p', 'ul', 'ol', 'li', 'span']:
        paragraphs.append([0, elements[0]['name'], elements[0]['content'], []])
        headings[parents[0]][5].append(len(paragraphs)-1)
        heading_paragraph_tree(headings, paragraphs, parents, elements[1:])
        return
    
    if elements[0]['name'] in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        # compare tag to parent tags, until equivalent or greater, then, 
        # if parent sub-heading = -1, make it this heading, else follow next heading values
        # add heading to headings, push to front of parents, and recurse
        while tag_rank(elements[0]['name'], headings[parents[0]][1]) <= 0 and len(parents) > 0:
            parents = parents[1:]
        
        headings.append([0, elements[0]['name'], elements[0]['content'], -1, -1, []])
        
        if headings[parents[0]][3] == -1:
            headings[parents[0]][3] = len(headings)-1
        else:
            previous = headings[parents[0]][3]
            while not headings[previous][4] == -1:
                previous = headings[previous][4]
            headings[previous][4] = len(headings)-1
        parents = [len(headings)-1] + parents
        heading_paragraph_tree(headings, paragraphs, parents, elements[1:])
        return
    
    heading_paragraph_tree(headings, paragraphs, parents, elements[1:])


def is_empty(string):

    return string in [None, '\n', '', ' ', 'None', '\n×', ]

def prune(dom_dictionary):

    children = []

    for child in dom_dictionary['children']:
        children.append(prune(child))

    dom_dictionary['children'] = list(filter(lambda x: x is not None, children))

    if len(dom_dictionary['children']) == 0 and is_empty(dom_dictionary['content']):
        return None
    
    if dom_dictionary['name'] in ['figcaption']: # put useless text-containing tags here
        return None

    return dom_dictionary

def collapse(dom_dictionary):

    children = []

    for child in dom_dictionary['children']:
        children.append(collapse(child))

    dom_dictionary['children'] = children

    if len(dom_dictionary['children']) == 1: 
        return dom_dictionary['children'][0]

    return dom_dictionary

def strip(dom_dictionary):

    children = []

    for child in dom_dictionary['children']:
        children.append(strip(child))

    children_v2 = []

    for child in children:
        if child['name'] in ['a', 'b', 'strong', 'i', 'mark', 'em']:
            children_v2.append(child['children'][0])
        else:
            children_v2.append(child)

    dom_dictionary['children'] = children_v2

    return dom_dictionary

def join(dom_dictionary):

    children = []
    for child in dom_dictionary['children']:
        children.append(join(child))

    if all(map(lambda x: x['name'] == '' and not is_empty(x['content']), children)) and len(children) != 0:
        for child in children:
            dom_dictionary['content'] += child['content']
        dom_dictionary['children'] = []
        return dom_dictionary
    
    else:
        dom_dictionary['children'] = []
        joining = False
        for child in children:
            if child['name'] != '': 
                joining = False
                dom_dictionary['children'].append(child)
                continue
            if not joining:
                dom_dictionary['children'].append(child)
                joining = True
                continue
            dom_dictionary['children'][-1]['content'] += child['content']
        return dom_dictionary
            
    #dom_dictionary['children'] = children
    #return dom_dictionary

def flatten(dom_dictionary, d=0):

    children = []
    for child in dom_dictionary['children']:
        children += flatten(child, d=d+1)

    if d == 0:
        dom_dictionary['children'] = children
        return dom_dictionary
    
    if dom_dictionary['content'] == '':
        return children

    dom_dictionary['children'] = children
    
    return [dom_dictionary]

def tag_rank(tag, parent_tag):

    tags = ['root', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    try:
        idx1 = tags.index(tag)
        idx2 = tags.index(parent_tag)
    except ValueError:
        return 0

    return idx1 - idx2

def scrape_url(url, driver=driver):

    #response = requests.get(url)
    #soup = BeautifulSoup(response.text, "html.parser")

    try:
        soup, title, lang = contentfinder(url, driver)
    except Exception as e:
        print(e)
        print(f'failure to scrape {url}')
        return [], ([], [], [])

    if lang != 'en': 
        print(f'failure to scrape {url}: language {lang}')
        return [], ([], [], [])

    anchors = anchorcheck(soup)
    anchors = anchors if anchors is not None else []
    urls = []
    host = get_host_and_path(url)[0]
    #print(host)

    for anchor in anchors:
        url_ = urlcheck(anchor[1], host)
        if url_: urls.append([anchor[0], url_])

    try: 
        res = article_to_tree(soup, url, title)
    except Exception:
        print(f'failure to scrape {url}')
        return urls, ([], [], [])
    
    return urls, res #soup_scraper(soup)