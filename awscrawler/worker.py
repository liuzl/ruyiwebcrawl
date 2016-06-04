#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yuande Liu <miraclecome (at) gmail.com>
# TODO worker启动程序，检测队列的batch_id, 未必是我schedule调度的batch_id

from __future__ import print_function, division

from gevent import monkey; monkey.patch_all()
import gevent

from rediscluster.record import Record
from rediscluster.queues import HashQueue
from rediscluster.thinredis import ThinHash

class Worker(object):
    """ General worker
    """
    def __init__(self):
        pass

    def work(self):
        raise NotImplementedError('This method should implemented by subclasses')

class GetWorker(Worker):
    def __init__(self):
        super(GetWorker, self).__init__()
        self.queues = [i for i in self._get_task_queue()]

        batch_id = self.queues[0].key
        total_count = int( Record.instance().get_total_number(batch_id) )
        self.thinhash = ThinHash(batch_id, total_count)

    def _get_task_queue(self):
        keys = Record.instance().get_unfinished_batch()
        for key in keys:
            yield HashQueue(key, priority=2, timeout=90, failure_times=3)

    def _check_empty_queue(self, queue):
        """ after 3 times of get, result is empty
        """
        for i in range(3):
            result = queue.get(block=True, timeout=3, interval=1)
            if result != []:
                return False
        return True

    def delete_queue_check(self, queue):
        ret = self._check_empty_queue(queue)
        if ret is False:
            return False
        ret = Record.instance().is_finished(queue.key)
        if ret is True:
            return False
        status = queue.get_background_cleaning_status()
        if status != '0':
            return False
        return True

    def run(self, *args, **kwargs):
        """ end, background_cleansing, status:
            0,   None,                 begin
            0,   1,                    begin cleansing
            0,   0,                    finish cleansing
         time,   0,                    begin delete
         time,   None,                 finish delete
            0,   0,                    finish cleansing with exception
        """
        queue = self.queues[0]
        background = queue.get_background_cleaning_status()
        if Record.instance().is_finished(queue.key) is True:
            return

        tasks = []
        if background is None:
            tasks.append( gevent.spawn(queue.background_cleaning) )
            tasks.append( gevent.spawn(self.work, *args, **kwargs) )
        elif background == '1':
            tasks.append( gevent.spawn(self.work, *args, **kwargs) )
        elif background == '0':
            ret = self.delete_queue_check(queue)
            if ret is True:
                # caution! atom operation
                try:
                    Record.instance().end(queue.key)
                    self.thinhash.delete()
                    queue.flush()
                except:
                    Record.instance().from_end_rollback(queue.key)

        gevent.joinall(tasks)


    def work(self, *args, **kwargs):
        queue = self.queues[0]
        result = queue.get(block=True, timeout=3, interval=1)
        url = self.thinhash.hget(result)

        module = __import__('prefetch.workers.{}'.format(queue.key.rsplit('_', 1)[0]), fromlist=['worker'])
        module.worker(url, *args, **kwargs)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Call Worker with arguments')
    parser.add_argument('--cookie', '-c', type=str, help='cookie for this machine')
    option = parser.parse_args()
    if option.cookie:
        obj = GetWorker()
        obj.run(cookie=option.cookie)

if __name__ == '__main__':
    main()
