import requests
from bs4 import BeautifulSoup as soup
import os
import json

BASE_URL = 'https://archive.org'


'''
Saves a given string to a given dirname.
Creates the directory if it doesn't already exist.
'''
def save(text, dirname):
    if not os.path.exists(os.path.dirname(dirname)):
        os.makedirs(os.path.dirname(dirname))
    with open(dirname, 'w') as file:
        file.write(text)


'''
Scrapes date from a given link to a segment on archive.org.
Saves minute-by-minute snippets and segment metadata.
Returns a dictionary.
'''
def getSegment(link):
    res = requests.get(link)
    assert(res.status_code == 200)
    page = soup(res.text)
    segment = {'snippets': [], 'metadata': {}}
    # Fetch snippets
    for column in page.find_all('div', {'class': 'tvcol'}):
        time = column.find('div', {'class': 'sniptitle'}).text.strip()
        caption = column.find('div', {'class': 'snippet'}).text.strip()
        segment['snippets'].append([time, caption])
    # Fetch metadata
    meta_fields = {'Network', 'Duration', 'Source', 'Tuner', 'Scanned in', 'Tuner'}
    for metadata in page.find_all('dl', {'class': 'metadata-definition'}):
        meta_name = metadata.find('dt').text.strip()
        if meta_name in meta_fields:
            segment['metadata'][meta_name] = metadata.find('dd').text.strip()
        elif meta_name == 'TOPIC FREQUENCY':
            segment['metadata']['Topics'] = [a.text.strip() for a in metadata.find_all('a')]
    # Get Title
    title = page.find('div', {'class': 'tv-ttl'})
    segment['metadata']['Title'] = title.find('a').text
    segment['metadata']['Datetime'] = title.find('div').text
    return segment


'''
Makes a request to the Archive scraping API.
Returns loaded JSON data as a dictionary.
'''
def searchSegments(cursor=None, count=100):
    payload = {
        'q': 'TV-BLOOMBERG',
        'count': count,
        'fields': 'date,forumSubject,title,identifier',
        'sorts': 'date',
        'cursor': cursor,
    }
    res = requests.get(BASE_URL + '/services/search/v1/scrape', payload)
    assert(res.status_code == 200)
    return json.loads(res.text)


'''
Uses searchSegments until max_len segments are found or no cursor object is returned (meaning we have fetched all results).
'''
def searchAllSegments(max_len=100000):
    cursor = None
    all_segments = []
    i = 0
    while len(all_segments) < max_len:
        print(f'Fetching segments on page {i}, found {len(all_segments)} segments already')
        i += 1
        data = searchSegments(cursor, count=10000)
        all_segments += data['items']
        cursor = data.get('cursor')
        if not cursor:
            break
    count = len(all_segments)
    print(f'Found {count} segments, {data["total"] - count} remaining')
    return all_segments


'''
Given a list of segment objects from searchAllSegments, fetches data from page and saves to disk in JSON format.
'''
def downloadPages(segments, folder_name='Bloomberg_Transcripts'):
    for i, segment in enumerate(segments):
        link = BASE_URL + '/details/' + segment['identifier']

        try:
            segment_data = getSegment(link)
            show = segment_data['metadata']['Title']
            datetime = segment_data['metadata']['Datetime']
            datetime = datetime.replace(',','').replace(' ', '_').replace(':','')
            print(datetime)
            dirname = f'{folder_name}/{show}/{datetime}.json'
            save(json.dumps(segment_data), dirname)
        except Exception as e:
            print(f'WARNING: Failed to fetch segment {i} at {link} due to error {e}')


'''
Returns a list of filepaths to segment data stored locally on disk.
'''
def listLocalSegments(folder_name='Bloomberg_Transcripts'):
    local_segments = []
    for path, subdirs, files in os.walk(folder_name):
        if path.count(os.sep) == 1:
            for file in files:
                local_segments.append(os.path.join(path, file))
    return local_segments
