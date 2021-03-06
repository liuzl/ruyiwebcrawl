#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yingqi Wang <yingqi.wang93 (at) gmail.com>


from __future__ import print_function, division
import sys
import json
import urllib
import re
import urlparse
from datetime import datetime
from lxml import etree
from downloader.cacheperiod import CachePeriod
from downloader.downloader_wrapper import Downloader
from downloader.downloader_wrapper import DownloadWrapper

from crawlerlog.cachelog import get_logger
from settings import REGION_NAME, CACHE_SERVER

reload(sys)
sys.setdefaultencoding('utf-8')
SITE = 'http://china.chemnet.com'
# SERVER = 'http://192.168.1.179:8000'
def process(url, batch_id, parameter, manager, other_batch_process_time, *args, **kwargs):
    if not hasattr(process, '_downloader'):
        domain_name =  Downloader.url2domain(url)
        headers = {'Host': domain_name}
        setattr(process, '_downloader', DownloadWrapper(None, headers))
    if not hasattr(process, '_cache'):
        head, tail = batch_id.split('-')
        setattr(process, '_cache', CachePeriod(batch_id, CACHE_SERVER))

    if not hasattr(process, '_regs'):
        setattr(process, '_regs', {
            'main': re.compile(r'http://china.chemnet.com/hot-product/(\w|\d+).html'),
            'prd': re.compile(r'http://china.chemnet.com/product/pclist--(.+?)--0.html'),
            'comps': re.compile(r'http://china.chemnet.com/product/search.cgi')
        })
    def safe_state(statement):
        return statement[0] if statement else ''

    def xpath_string(n):
        return "//*[@id=\"main\"]/div[1]/div[1]/table/tr[" + str(n) + "]/td[2]/text()"
        
    method, gap, js, timeout, data = parameter.split(':')
    gap = float(max(0, float(gap) - other_batch_process_time))
    timeout= int(timeout)
    compspat = 'http://china.chemnet.com/product/search.cgi?skey={};use_cas=0;f=pclist;p={}'
    today_str = datetime.now().strftime('%Y%m%d')

    # if kwargs and kwargs.get("debug"):
    #     get_logger(batch_id, today_str, '/opt/service/log/').info('start download')
    content = process._downloader.downloader_wrapper(url,
        batch_id,
        gap,
        timeout=timeout,
        # encoding='gb18030',
        refresh=True
        )
    # print(content)
    if content == '':
        get_logger(batch_id, today_str, '/opt/service/log/').info(url + ' no content')
        return False
    

    # if kwargs and kwargs.get("debug"):
    get_logger(batch_id, today_str, '/opt/service/log/').info('start parsing url')

    for label, reg in process._regs.iteritems():
        m = reg.match(url)
        if not m:
            continue
        page = etree.HTML(content.replace('<sub>', '').replace('</sub>', ''))
        if label == 'main':
            # print("add chems")
            chems = page.xpath("//*[@id=\"main\"]/div[1]/div[2]/dl/dd/ul/li/p[2]/a/@href")  # links for chems in main page
            chems = [ urlparse.urljoin(SITE, chem) for chem in chems]
            get_logger(batch_id, today_str, '/opt/service/log/').info('adding chems urls into queue')
            manager.put_urls_enqueue(batch_id, chems)
            return True

        elif label == 'prd':
            chem_uri = m.group(1)
            chem_name = page.xpath("//*[@id=\"main\"]/div[1]/div[1]/table/tr[1]/td[2]/text()")[0]
            get_logger(batch_id, today_str, '/opt/service/log/').info(chem_name + " main page")
            
            comps = page.xpath("//*[@id=\"main\"]/div[2]/div[2]/dl/dd/form/table/tr[1]/td[2]/a[1]")
            pagetext = page.xpath("//*[@id=\"main\"]/div[2]/div[2]/dl/dd/h6/div/text()[1]")
            # print(pagetext[0])
            total = int(re.compile(r'共有(\d+)条记录').search(pagetext[0].encode('utf-8')).group(1))
            total = total // 10 + 1 if total % 10 != 0 else total // 10
            dic = {
                            u'source': url,
                            u'中文名称': page.xpath(xpath_string(1))[0] if page.xpath(xpath_string(1)) else '',
                            u'英文名称': page.xpath(xpath_string(2))[0] if page.xpath(xpath_string(2)) else '',
                            u'中文别名': page.xpath(xpath_string(3))[0] if page.xpath(xpath_string(3)) else '',
                            u'CAS_RN': page.xpath(xpath_string(4))[0] if page.xpath(xpath_string(4)) else '',
                            u'EINECS': page.xpath(xpath_string(5))[0] if page.xpath(xpath_string(5)) else '',
                            u'分子式': page.xpath(xpath_string(6))[0] if page.xpath(xpath_string(6)) else '',
                            u'分子量': page.xpath(xpath_string(7))[0] if page.xpath(xpath_string(7)) else '',
                            u'危险品标志': page.xpath(xpath_string(8))[0].strip() if page.xpath(xpath_string(8)) else '',
                            u'风险术语': page.xpath(xpath_string(9))[0].strip() if page.xpath(xpath_string(9)) else '',
                            u'安全术语': page.xpath(xpath_string(10))[0].strip() if page.xpath(xpath_string(10)) else '',
                            u'物化性质': page.xpath("//*[@id=\"main\"]/div[1]/div[1]/table/tr[11]/td[2]/p/text()") if page.xpath("//*[@id=\"main\"]/div[1]/div[1]/table/tr[11]/td[2]/p/text()") else [],
                            u'用途': page.xpath(xpath_string(12))[0]  if page.xpath(xpath_string(12)) else '',
                            u'上游原料': page.xpath('//*[@id=\"main\"]/div[1]/div[1]/table/tr[14]/td[2]/a/text()') if page.xpath('//*[@id=\"main\"]/div[1]/div[1]/table/tr[14]/td[2]/a/text()') else [],
                            u'下游产品': page.xpath('//*[@id=\"main\"]/div[1]/div[1]/table/tr[15]/td[2]/a/text()') if page.xpath('//*[@id=\"main\"]/div[1]/div[1]/table/tr[15]/td[2]/a/text()') else [],
                }
            data = json.dumps(dic, encoding='utf-8', ensure_ascii=False)
            new_urls = []
            for t in range(total):
                new_url = compspat.format(chem_uri, str(t))
                get_logger(batch_id, today_str, '/opt/service/log/').info("new url" + new_url)
                new_urls.append(new_url)
            manager.put_urls_enqueue(batch_id, new_urls)
            get_logger(batch_id, today_str, '/opt/service/log/').info('start posting prd page to cache')
            return process._cache.post(url, data)

        else:
            chem_name = page.xpath("//*[@id=\"main\"]/div[1]/div[1]/table/tr[1]/td[2]/text()")[0]
            total = len(page.xpath("//*[@id=\"main\"]/div[2]/div[2]/dl/dd/form"))   # total num of suppliers
            dic = ''
            for i in range(1, total + 1):
                c = safe_state(page.xpath("//*[@id=\"main\"]/div[2]/div[2]/dl/dd/form[{}]".format(str(i))))
                if c is '':
                    break
                comp = {}
                comp[u'source'] = url
                comp[u'chem_name'] = chem_name
                comp[u'name'] = safe_state(c.xpath(".//table/tr[1]/td[2]/a[1]/text()"))
                comp[u'tel'] = safe_state(c.xpath(".//table/tr[2]/td[2]/text()"))
                comp[u'fax'] =  safe_state(c.xpath(".//table/tr[3]/td[2]/text()"))
                comp[u'website'] = safe_state(c.xpath(".//table/tr[4]/td[2]/a/text()"))
    
                dic += json.dumps(comp, encoding='utf-8', ensure_ascii=False) + '\n'
            dic = dic.strip()
            get_logger(batch_id, today_str, '/opt/service/log/').info('start posting companies to cache')
            return process._cache.post(url, dic)



# process('http://china.chemnet.com/product/search.cgi\?skey=%B1%BD%CD%AA;use_cas=0;f=pclist;p=1','testfw-20160725',"get:1:false:10:",'',debug=True)
