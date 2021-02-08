from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as soup
import os
import re
import json

def seleniumGet(url, headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("headless")
    driver = webdriver.Chrome('./chromedriver', options=options)
    driver.get(url)
    page = soup(driver.page_source)
    driver.close()
    return page


def getPosts(subreddit):
    BASE_URL = 'https://old.reddit.com'
    url = BASE_URL + f'/r/{subreddit}/'
    page = seleniumGet(url)
    posts = []
    for post in page.find_all('div', {'class': 'top-matter'}):
        try:
            anchor = post.find('a', {'class': 'comments'})
            comment_text = anchor.text
            posts.append({
                'title': post.find('a', {'class': 'title'}).text,
                'comment_link': anchor['href'],
                'num_comments': int(re.search('\d*', comment_text).group())
            })
        except Exception as e:
            print(e)
            # POST WITH ERRORS ARE ADS!
            # Ads dont have comment classes, throwing a nonetype error.
            pass
    return posts

def parseThread(thread):
    comments = []
    for comment in thread.find_all('div', {'class': 'comment'}):
        entry = comment.find('div', {'class', 'entry'}, recursive=False)
        text = entry.find('div', {'class': 'usertext-body'}).text
        upvotes = entry.find('span', {'class': 'score unvoted'})
        if upvotes:
            try:
                upvotes = int(re.search('\d*', upvotes.text).group())
            except:
                upvotes = None
        if upvotes is not None and upvotes > 3:
            subthread = comment.find('div', {'class': 'child'}, recursive=False)
            comments.append({
                'upvotes': upvotes,
                'text': text,
                'child': parseThread(subthread),
            })
    if len(comments) == 0:
        return None
    return comments

if __name__ == '__main__':
#     subreddit = 'wallstreetbets'
    subreddit = 'investing'
    posts = getPosts(subreddit)
    for i, post in enumerate(posts):
        thread = seleniumGet(post['comment_link'], headless=True)
        post['thread'] = parseThread(thread)
        with open(f'post_{i}.json', 'w') as file:
            file.writelines(json.dumps(post))
        if i > 3:
            # Exit early for the demo.
            break
