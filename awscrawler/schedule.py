#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yuande Liu <miraclecome (at) gmail.com>

from __future__ import print_function, division
from math import ceil

import time

from ec2manager import Ec2Manager

class schedule(object):

    def __init__(self, machine_num, *args, **kwargs):
        self.machine_num = machine_num
        self.cycle = kwargs.get('cycle', 600)
        self.group_num = int(ceil(machine_num * 2 / self.cycle)) if machine_num * 2 >= self.cycle else 1
        self.restart_interval = 0 if machine_num * 2 >= self.cycle else self.cycle / machine_num 

        self.ec2manager = Ec2Manager()

    def run(self):
        self.ec2manager.create_instances(self.machine_num)
        time.sleep(30)

        before = time.time()
        while 1:
            self.ec2manager.stop_one_and_restart()
            if self.restart_interval != 0:
                now = time.time()
                sleep_interval = before + self.restart_interval - now
                if sleep_interval > 0:
                    time.sleep(sleep_interval)
                before = now
