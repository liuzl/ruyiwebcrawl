#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yuande Liu <miraclecome (at) gmail.com>

from __future__ import print_function, division


import urlparse
import requests
import hashlib

class CachePeriod(object):
    def __init__(self, batch_id, server):
        self.server = server
        self.batch_id = batch_id


    def exists(self, url):
        url_hash = hashlib.sha1(url).hexdigest()
        api_url = 'v1/cache/{}/{}'.format(url_hash, self.batch_id)
        get_api_url = urlparse.urljoin(self.server, api_url)
        response = requests.get(get_api_url, data={'exists': True})

        js = response.json()
        if js[u'success'] is False:
            return u''
        return js[u'exists']


    def get(self, url):
        url_hash = hashlib.sha1(url).hexdigest()
        api_url = 'v1/cache/{}/{}'.format(url_hash, self.batch_id)
        get_api_url = urlparse.urljoin(self.server, api_url)
        response = requests.get(get_api_url)

        js = response.json()
        if js[u'success'] is False:
            return u''

        return js[u'content']


    def post(self, url, content, groups=None, refresh=False):
        url_hash = hashlib.sha1(url).hexdigest()
        api_url = 'v1/cache/{}/{}'.format(url_hash, self.batch_id)
        post_api_url = urlparse.urljoin(self.server, api_url)
        data = {
            'groups': groups,
            'content': content,
            'refresh': refresh,
        }

        ret = False
        for _ in range(2):
            response = requests.post(post_api_url, data=data)
            if response.status_code != 200:
                ret = response.content
                continue

            js = response.json()
            if js['success'] is True:
                return True
            if u'error' in js:
                ret = js[u'error']
                continue
        return ret
