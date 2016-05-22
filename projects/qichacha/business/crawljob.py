# encoding=utf-8
import glob
import os
import sys
import json
import collections
import codecs
import re
import hashlib
import datetime
from collections import defaultdict
reload(sys)
sys.setdefaultencoding('utf-8')

from core.qichacha import Qichacha

sys.path.append(os.path.abspath(os.path.dirname(__file__)) )
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


###################
# global config and functions
gcounter = collections.Counter()

def getLocalFile(filename):
    return os.path.abspath(os.path.dirname(__file__)).replace("/qichacha/","/qichacha/local/") +"/"+filename

def getTheFile(filename):
    return os.path.abspath(os.path.dirname(__file__)) +"/"+filename

def file2set(filename):
    ret = set()
    with codecs.open(filename,  encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()

            if line:
                ret.add(line)
    return ret



def crawl_search(batch):
    dir_name = getTheFile( batch+"/*")
    filenames = glob.glob(dir_name)
    for filename in filenames:
        print filename
        crawl_search_file(batch, filename)


def crawl_search_file(batch, filename):
    filename_metadata = getLocalFile('crawl_search.{}.json.txt'.format(batch))
    LIMIT = 100

    #load prev state
    searched = set()
    if os.path.exists(filename_metadata):
        for line in file2set(filename_metadata):
            item = json.loads(line)
            searched.update(item["data"].keys())

    #print len(searched),list(searched)[0:3]
    #return

    #add new
    with codecs.open(filename_metadata,'a') as flog:
        #crawl_search_pass( FILENAME_CRAWL_SEED_KEYWORDS, searched, flog, crawler.list_corporate_search, LIMIT, False )
        crawl_search_pass( filename, searched, flog, LIMIT, False )

def crawl_search_pass( filename, searched, flog, limit, refresh):

    crawler = Qichacha()

    seeds = file2set(filename)
    counter = collections.Counter()
    counter['total'] = len(seeds)
    counter['searched'] = len(seeds.intersection(searched))

    print len(seeds),list(seeds)[0:3]

    for seed in sorted(list(seeds)):
        if counter['visited'] % 10 ==0:
            print os.path.basename(filename), datetime.datetime.now().isoformat(), counter

        counter['visited']+=1
        if not refresh and seed in searched:
            continue
        searched.add(seed)

        print seed, limit
        try:


            if "seed_org" in filename:
                data = crawler.list_corporate_search( [seed], limit)
            elif "seed_person" in filename:
                data = crawler.list_person_search( [seed], limit)
            else:
                print "skip unsupported filename ", fileanme
                continue

            if data:
                item = {
                    "data": data,
                    "ts": datetime.datetime.now().isoformat()
                }
                flog.write(json.dumps(item, ensure_ascii=False))
                flog.write("\n")
            else:
                counter['empty'] +=1

        except:
            counter['failed'] +=1
            pass


    print "final", os.path.basename(filename), counter


def crawl_company(filename_company):
    #load prev state
    filename_metadata = getLocalFile('loal/crawl_search.json.txt')
    crawl_search_result = set()
    if os.path.exists(filename_metadata):
        for line in file2set(filename_metadata):
            item = json.loads(line)
            crawl_search_result.update(item["data"])

    #load names
    seed_company = file2set(filename_company)

    #map names to id

def test():
    seed = "上海华衡投资"
    crawler = Qichacha()
    ret = crawler.list_corporate_search(seed, 1)
    print json.dumps(ret, ensure_ascii=False,encoding='utf-8')

def main():
    #print sys.argv

    if len(sys.argv)<2:
        show_help()
        return

    option= sys.argv[1]
    batch = sys.argv[2]
    #filename = sys.argv[3]
    if "search" == option:
        crawl_search(batch)

    elif "test" == option:
        test()
        pass


if __name__ == "__main__":
    main()
    gcounter[datetime.datetime.now().isoformat()]=1
    print json.dumps(gcounter,ensure_ascii=False,indent=4, sort_keys=True)
