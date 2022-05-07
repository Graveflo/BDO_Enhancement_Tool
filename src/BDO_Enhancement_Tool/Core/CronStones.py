# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import json
import sqlite3

from .Item import Item


CRON_MANAGER = None
def initialize_cronstone_manager(pat):
    global CRON_MANAGER
    CRON_MANAGER = CronStoneManager(pat)


class CronStoneManager(object):
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
        self.cache = {}
        self.customs = set()

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
        return self.connection

    def close(self):
        if hasattr(self.connection, 'close'):
            self.connection.close()

    def check_out_gear(self, gear: Item):
        if gear.item_id is None:
            return None
        id = int(gear.item_id)
        if id in self.cache:
            return self.cache[id]
        else:
            connection = self.get_connection()
            cur = connection.cursor()
            cur.execute('SELECT obj from Cron WHERE gear_id={};'.format(id))
            itm = cur.fetchone()
            if itm is None:
                return None
            val = json.loads(itm[0])
            self.cache[id] = val
            return val

    def check_in_gear(self, gear: Item, level, amount):
        if gear.item_id is None:
            return None
        id = int(gear.item_id)
        if id in self.cache:
            obj = self.cache[id]
        else:
            obj = {level:amount}
            self.cache[id] = obj
        self.customs.add((id, level))
        obj[level] = amount


