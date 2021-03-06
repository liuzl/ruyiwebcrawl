#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yuande Liu <miraclecome (at) gmail.com>

from __future__ import print_function, division

import os
import sys
import re
import json
import base64
import traceback
import requests
import time

import lxml.html

from downloader.caches3 import CacheS3
from downloader.downloader_wrapper import DownloadWrapper
from downloader.downloader_wrapper import Downloader

from settings import REGION_NAME

from crawlerlog.cachelog import get_logger
from datetime import datetime

def process(url, batch_id, parameter, manager, *args, **kwargs):
    if not hasattr(process, '_downloader'):
        domain_name =  Downloader.url2domain(url)
        headers = {"Host": domain_name}
        setattr(process, '_downloader', DownloadWrapper('s3', headers, REGION_NAME))
    if not hasattr(process, '_cache'):
        setattr(process, '_cache', CacheS3(batch_id.split('-', 1)[0]+'-json'))

    method, gap, js, timeout, data = parameter.split(':')
    gap = int(gap)
    timeout= int(timeout)

    today_str = datetime.now().strftime('%Y%m%d')
    get_logger(batch_id, today_str, '/opt/service/log/').info('start download content')
    content = process._downloader.downloader_wrapper(url,
        batch_id,
        gap,
        timeout=timeout,
        encoding='gb18030')

    if kwargs and kwargs.get("debug"):
        print(len(content), "\n", content[:1000])

    if content is False:
        return False

    get_logger(batch_id, today_str, '/opt/service/log/').info('start parsing content')
    begin = content.find('<div class="mainbox">')
    end = content.find('<div id="footer">', begin)
    tree = lxml.html.fromstring(content[begin:end])
    title = tree.xpath('//div[@class="content"]/h4/text()')
    if isinstance(title, list) and len(title) > 0:
        title = title[0]
    else:
        title = None
    public_date = tree.xpath('//div[@class="content"]/h5/text()')
    if isinstance(public_date, list) and len(public_date) > 0:
        public_date = public_date[0]
    else:
        public_date = None
    body = tree.xpath('//div[@class="content"]//pre/text()')
    if isinstance(body, list) and len(body) > 0:
        body = body[0]
    else:
        body = None
    notice_content = json.dumps({'url': url, 'title': title, 'public_date': public_date, 'body': body})

    get_logger(batch_id, today_str, '/opt/service/log/').info('start post json')
    ret = process._cache.post(url, notice_content)
    return ret
