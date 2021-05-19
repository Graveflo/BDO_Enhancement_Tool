# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import sqlite3
from typing import List, Dict, TypeVar

from BDO_Enhancement_Tool.utilities import relative_path_convert

GEAR_DB = 'gear.sqlite3'


class GearData(object):
    def __init__(self, item_id=None, name=None, grade=None, icon_url=None, item_type=None):
        self.item_id = item_id
        self.name = name
        self.grade = grade
        self.icon_url = icon_url
        self.item_type = item_type

    def get_grade_str(self) -> str:
        return grade_enum_to_str(self.grade)

    def get_class_str(self) -> str:
        return class_enum_to_str(self.item_type)

    def get_gt_str(self) -> str:
        grade = self.get_grade_str()
        i_type = self.get_class_str()
        return class_grade_to_gt_str(i_type, grade, self.name)

T = TypeVar('T', bound=GearData)

class GearDatabase(object):
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = relative_path_convert(GEAR_DB, fp=__file__)
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn is not None:
            self.conn.close()
        self.conn = None

    def process_row(self, row):
        return GearData(*row)

    def  process_rows(self, rows):
        return list(map(GearData, rows))

    def lookup_id(self, item_id) -> T:
        with self:
            conn = self.conn
            cur = conn.cursor()
            cur.execute('SELECT * FROM Gear WHERE gear_id=?', (int(item_id),))
            result = cur.fetchone()
            if result is None:
                raise KeyError('Item is not in gear database: {}'.format(item_id))
            return self.process_row(result)

    def query(self, str_query) -> List[T]:
        with self:
            conn = self.conn
            cur = conn.cursor()
            return self.process_rows(cur.execute(str_query))


class CachedGearDataBase(GearDatabase):
    def __init__(self, db_path=None):
        super(CachedGearDataBase, self).__init__(db_path=db_path)
        self.id_cache: Dict[int, T] = {}

    def process_row(self, row):
        gd = super(CachedGearDataBase, self).process_row(row)
        self.id_cache[gd.item_id] = gd
        return gd

    def  process_rows(self, rows):
        return [self.id_cache[row[0]] if row[0] in self.id_cache else self.process_row(row) for row in rows]

    def lookup_id(self, item_id) -> T:
        item_id = int(item_id)
        if item_id in self.id_cache:
            return self.id_cache[item_id]
        else:
            return super(CachedGearDataBase, self).lookup_id(item_id)

    def dump_all(self):
        self.query('SELECT * FROM Gear')

def class_grade_to_gt_str(item_class, item_grade, name):
    if item_grade == 'Yellow':
        item_grade = 'Boss'
    if item_grade == 'Orange':
        if name.lower().find('fallen god') > -1:
            item_grade = 'Fallen God'
        else:
            item_grade = 'Blackstar'
    return item_grade + " " + item_class

def grade_enum_to_str(res_grade):
    if res_grade == 0:
        return 'White'
    elif res_grade == 1:
        return 'Green'
    elif res_grade == 2:
        return 'Blue'
    elif res_grade == 3:
        return 'Yellow'
    elif res_grade == 4:
        return 'Orange'
    else:
        return 'Error'

def class_enum_to_str(res_class):
    if res_class == 0:
        return 'Weapons'
    elif res_class == 1:
        return 'Armor'
    elif res_class == 2:
        return 'Accessories'
    else:
        return 'Error'
