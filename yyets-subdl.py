#!/usr/bin/env python
# encoding: utf-8
# yyets-subdl.py - command-line downloader for YYeTs subtitles

import os
import sys
import shutil
import zipfile

# pip install requests
import requests


def query(keyword):
    request_url = 'http://www.yyets.com/php/search/api'
    request_params = dict(keyword=keyword)
    response = requests.get(request_url, params=request_params)
    if response.status_code == requests.codes.ok:
        items = response.json()['data']
        choices = [x for x in items if x['type'] == 'subtitle']
        return choices
    else:
        raise Exception('HTTP status_code=%s' % response.status_code)
    return []


def ask(choices):
    for idx, choice in enumerate(choices):
        print '%2d. %s' % (idx+1, choice['title'])
        print '    %s' % choice['version']
    answers = raw_input('What items do you want? (seperated by commas) [1] ')
    if answers: return map(lambda x: int(x)-1, answers.split(r','))
    else: return [0]


def download(items):
    files = []
    for item in items:
        # item_url = 'http://www.yyets.com/%s/%s' % (item['type'], item['itemid'])
        download_url = 'http://www.yyets.com/%s/index/download?id=%s' % (item['type'], item['itemid'])
        download_filename = '%s.zip' % (item['version'].split(';')[0] or item['title'])
        command_line = "curl -L '%s' > '%s'" % (download_url, download_filename)
        print command_line
        os.system(command_line.encode('utf-8'))
        files.append(download_filename)
    return files


def extract(files):
    for filepath in files:
        print 'Examining %s' % filepath
        if not 'zip' in os.path.splitext(filepath)[1].lower():
            continue
        extract_success = False
        with zipfile.ZipFile(filepath) as archive:
            for item in archive.namelist():
                filename = os.path.split(item)[1]
                extension = os.path.splitext(filename)[1].lower()

                try: filename = filename.decode('gb2312')
                except: pass

                try: filename = filename.encode('utf-8')
                except: pass

                found = False
                target_lang = u'繁体&英文'.encode('utf-8')
                if ('ass' in extension) and (target_lang in filename):
                    # zipfile.extract() makes filename escaped with '%xx'
                    with archive.open(item, 'r') as infile, open(filename, 'wb') as outfile:
                        shutil.copyfileobj(infile, outfile)
                        extract_success = True
                    print 'Extracted %s' % filename
        if extract_success:
            os.remove(filepath)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: %s <keyword>' % sys.argv[0]
        print "Example: %s 'Person of Interest S04E01'" % sys.argv[0]
        sys.exit(1)
    keyword = sys.argv[1]
    choices = query(keyword)
    chosen_ids = ask(choices)
    chosens = [choices[idx] for idx in chosen_ids]
    files = download(chosens)
    extract(files)
