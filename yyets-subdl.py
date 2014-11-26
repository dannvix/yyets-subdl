#!/usr/bin/env python
# encoding: utf-8
# yyets-subdl.py - command-line downloader for YYeTs subtitles

import os
import sys
import json
import urllib
import urllib2
import shutil
import zipfile

# PROXY = None
PROXY = ('proxy.hinet.net', '80')

try:
    # pip install rarfile
    # brew install unrar
    import rarfile
except ImportError, e:
    rarfile = None

try:
    # for colorful terminal
    # pip install blessings
    from blessings import Terminal
except ImportError, e:
    # fallback
    class Terminal(object):
        def __getattr__(self, name):
            def _missing(*args, **kwargs):
                return ''.join(args)
            return _missing


# globals
t = Terminal()


def query(keyword):
    url = 'http://www.yyets.com/php/search/api'
    params = urllib.urlencode(dict(keyword=keyword))
    request = '%s?%s' % (url, params)

    urlopen = urllib2.urlopen
    if PROXY:
        proxy = ':'.join(PROXY)
        proxy_opener = urllib2.build_opener(urllib2.ProxyHandler(dict(http=proxy)))
        urlopen = proxy_opener.open
    page = urlopen(request).read()

    items = json.loads(page)['data']
    choices = [x for x in items if x['type'] == 'subtitle']
    return choices


def ask(choices):
    for idx, choice in enumerate(choices):
        num = t.red(str(idx+1).rjust(2))
        title = t.yellow(choice['title'])
        version = t.white(choice['version'])

        print '%s. %s' % (num, title)
        print '    %s' % version
    answers = raw_input('What items do you want? (seperated by commas) [1] ')
    if answers: return map(lambda x: int(x)-1, answers.split(r','))
    else: return [0]


def download(items):
    proxy_opts = ''
    if PROXY:
        proxy_opts = '--proxy http://{host}:{port}'.format(host=PROXY[0], port=PROXY[1])

    files = []
    for item in items:
        # item_url = 'http://www.yyets.com/%s/%s' % (item['type'], item['itemid'])
        download_url = 'http://www.yyets.com/%s/index/download?id=%s' % (item['type'], item['itemid'])
        download_filename = '%s.zip' % (item['version'].split(';')[0] or item['title'])
        command_line = "curl {proxy} -L '{url}' > '{outfile}'".format(proxy=proxy_opts, url=download_url, outfile=download_filename)
        print command_line
        os.system(command_line.encode('utf-8'))
        files.append(download_filename)
    return files


def extract(files, lang='', ext=''):
    for filepath in files:
        print 'Examining %s' % filepath
        extract_success = False
        archive = None
        try:
            # first we assume it's a Zip archive
            archive = zipfile.ZipFile(filepath)
        except zipfile.BadZipfile:
            if rarfile:
                # seems not a Zip, let's try RAR
                # https://rarfile.readthedocs.org/en/latest/api.html
                archive = rarfile.RarFile(filepath)
        if archive:
            for item in archive.namelist():
                filename = os.path.split(item)[1]
                extension = os.path.splitext(filename)[1].lower()

                try: filename = filename.decode('gb2312')
                except: pass

                try: filename = filename.encode('utf-8')
                except: pass

                target_lang = lang.encode('utf-8')
                if (ext in extension) and (target_lang in filename):
                    # zipfile.extract() makes filename escaped with '%xx'
                    with archive.open(item, 'r') as infile, open(filename, 'wb') as outfile:
                        shutil.copyfileobj(infile, outfile)
                        extract_success = True
                    print 'Extracted %s' % filename
            archive.close()
        else:
            print 'Cannot unpack %s' % filename
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
    extract(files, lang=u'繁体&英文', ext='ass')
