# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""


class Item(object):
    def __init__(self, item_id=None):
        self.item_id = None
        if item_id is not None:
            self.set_item_id(item_id)

    def set_item_id(self, item_id):
        self.item_id = int(item_id)