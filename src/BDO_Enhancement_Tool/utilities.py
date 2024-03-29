#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import os
import sys
import traceback
import json
import math
import subprocess
import typing
from typing import TypeVar, List, Dict


def relative_path_convert(x, fp=None):
    """
    Takes a valid path: either relative to CWD or an absolute path and convert it to a relative path for this file.
    The relative path assumes that simply joining the returned path with the path of this file shall result in a valid
    path pointing to the origonal valid file object (x).
    :param x: str: path to a valid file object
    :return: str: a path to the file object relative to this file
    """
    if fp is None:
        fp = __file__
    return os.path.abspath(os.path.join(os.path.split(fp)[0], x))


### stackoverflow - Dietrich Epp
if sys.platform == 'darwin':
    def open_folder(path):
        subprocess.Popen(['open', '--', path])
elif sys.platform == 'linux2':
    def open_folder(path):
        subprocess.Popen(['xdg-open', '--', path])
elif sys.platform == 'win32':
    def open_folder(path):
        subprocess.Popen(['explorer', path])
###


class Settings(dict):
    def __init__(self, settings_file_path=None):
        super(Settings, self).__init__()
        self.changes_made = False
        self.changes = []
        self.init_settings()
        self.f_path = settings_file_path
        if settings_file_path is not None:
            if os.path.exists(settings_file_path):
                if os.path.isfile(settings_file_path):
                    self.load()
                else:
                    raise IOError('settings file is not a file: ' + repr(settings_file_path))
                #        os.remove(settings_file_path)
                #elif os.path.isdir(settings_file_path):
                #    os.rmdir(settings_file_path)

    def init_settings(self, sets=None):
        if sets is not None:
            self.update(sets)

    def __setitem__(self, key, value):
        try:
            prev = self[key]
            is_new = not value == prev
        except KeyError:
            is_new = True
        if isinstance(key, list):
            set = self
            for it_ in key[:-1]:
                set = set[it_]
            set[key[-1]] = value
        else:
            super(Settings, self).__setitem__(key, value)
        if is_new:
            self.changes_made = True
            self.changes.append((key, value))

    def __getitem__(self, item):
        if isinstance(item, list):
            init_o = self
            for it_ in item:
                init_o = init_o[it_]
            return init_o
        else:
            return super(Settings, self).__getitem__(item)

    def get_state_json(self):
        return self

    def set_state_json(self, state):
        #self.clear()
        self.update(state)

    def save(self, file_path=None):
        if file_path is None:
            file_path = self.f_path
        else:
            # Must force write
            self.changes_made = True
        if file_path is None:
            raise AttributeError('No settings file path specified.')
        if self.changes_made:
            state = json.dumps(self.get_state_json(), indent=4)
            with open(file_path, 'w') as f:
                f.write(state)
            self.changes_made = False
            self.changes = []

    def load(self, file_path=None):
        if file_path is None:
            file_path = self.f_path
        with open(file_path, 'r') as f:
            self.f_path = file_path
            self.set_state_json(json.loads(f.read()))

    def invalidate(self):
        self.changes_made = True


class Tee(object):
    def __init__(self, name=None, mode=None):
        self.file_name = name
        self.file_mode = mode
        self.file = None
        self.stdout = sys.stdout
        self.cache = []
        sys.stdout = self
        if name is not None and mode is not None:
            self.open_file()

    def __del__(self):
        sys.stdout = self.stdout
        self.close()

    def open_file(self, fp=None, fm=None):
        if fp is None:
            fp = self.file_name
        if fm is None:
            fm = self.file_mode
        file_ = self.file
        if self.file is not None:
            self.file = None
            file_.close()
        self.file = open(fp, fm, encoding='utf-8')
        cache = self.cache
        self.cache = []
        self.write(''.join(cache), echo=False)

    def write(self, data, echo=True):
        if self.file is None:
            self.cache.append(data)
        else:
            self.file.write(data)
            self.file.flush()
        if echo:
            self.stdout.write(data)

    def flush(self):
        if self.file is not None and self.file.closed is False:
            self.file.flush()

    def close(self):
        if self.file is not None:
            self.file.close()

def chain_iter(*iterables):
    for iterable in iterables:
        for i in iterable:
            yield i

def sanitizeFileName(fileName):
    """
    Only accepts valid filename characters (Win32)
    :param fileName: The file name to be cleaned
    :return: A string with all illegal characters removed
    """
    valid_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(c for c in fileName if c in valid_chars)

def isnumeric(s):
    """
    Determines weather an reference is numeric or not
    :param s: The reference in question
    :rtype: boolean
    """
    try:
        float(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

def emptyFolder(folder_path, exceptions=None):
    """
    Deletes all of the files in a folder. Some files can be declared exceptions to the deletion procedure.
    :param folder_path: Path of folder to empty
    :param exceptions: Folder contents that will not be deleted
    :return: None
    """
    if exceptions is None:
        exceptions = []
    for file_ in os.listdir(folder_path):
        delete_me = os.path.join(folder_path, file_)
        if os.path.isfile(delete_me) and file_ not in exceptions:
            os.remove(delete_me)

def getStackTrace():
    """
    Return text that gives information on the python interpreters execution stack. This can be helpful debug information.
    :return: string : traceback body text
    """
    exc_infos = sys.exc_info()
    exc_traceback = exc_infos[2]
    str_c = "EXC:" + str(exc_infos[0])
    for sta in traceback.extract_tb(exc_traceback):
        filename, linenum, func, stacktxt = sta
        str_c += "\r\n" + str(filename) + " --> " + str(func) + ", line: " + str(linenum) + "\r\n" + str(
            stacktxt) + "\r\n"
    return str_c

def fmt_traceback(tb):
    str_c = []
    for sta in traceback.extract_tb(tb):
        filename, linenum, func, stacktxt = sta
        str_c.extend([str(filename) + " --> "+str(func)+", line: " + str(linenum), str(stacktxt), ''])
    return "\r\n".join(str_c)

def removeWhiteSpace(inStr):
    """
    Removes spaces, tabs and newline characters.
    :param inStr: string : The string to cleanse
    :return: string : the cleansed string
    """
    return inStr.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")

def string_between(inStr, leader, trailer):
    """
        Alex Martelli - Stack Overflow
        Finds first from the beginning.
        "" (blank strings) are indications of index 0 and end of string
    """
    if leader == "":
        end_of_leader = 0
    else:
        end_of_leader = inStr.index(leader) + len(leader)
    if trailer == "":
        start_of_trailer = len(inStr)
    else:
        start_of_trailer = inStr.index(trailer, end_of_leader)
    return inStr[end_of_leader:start_of_trailer]

def string_between_ext(inStr, leader, trailer, start=0):
    """
        Alex Martelli - Stack Overflow
        Finds first from the beginning.
        "" (blank strings) are indications of index 0 and end of string
    """
    inStr_n = inStr[start:]
    if leader == "":
        end_of_leader = 0
    else:
        end_of_leader = inStr_n.index(leader) + len(leader)
    if trailer == "":
        start_of_trailer = len(inStr_n)
    else:
        start_of_trailer = inStr_n.index(trailer, end_of_leader)
    return inStr_n[end_of_leader:start_of_trailer]

def string_betweenr(inStr, leader, trailer):
    if leader == "":
        end_of_leader = 0
    else:
        end_of_leader = inStr.rfind(leader)
    if trailer == "":
        start_of_trailer = len(inStr)
    else:
        start_of_trailer = inStr[:end_of_leader].rfind(trailer) + len(trailer)
    return inStr[start_of_trailer:end_of_leader]

def center_rect(inner, outer):
    in_w, in_h = inner
    ow, oh = outer

    margin_w = int(math.floor((ow - in_w) / 2.0))
    margin_h = int(math.floor((oh - in_h) / 2.0))

    return margin_w, margin_h

def fitAspectRatio(ratio, height=None, width=None, prefer_high=True):
    rat_w, rat_h = ratio
    if height is None:
        if width is None: raise ValueError("height and width cannot both be 0")
        height = float(width * rat_h) / float(rat_w)
        if height == int(height):
            return width, height
        else:
            rat_mult, remainder = divmod(width, rat_w)
            rat_mult += 1
            width += rat_w - remainder
            height = rat_h * rat_mult
    else:
        if height is None: raise ValueError("height and width cannot both be 0")
        width = float(height * rat_w) / float(rat_h)
        if width == int(width):
            return width, height
        else:
            rat_mult, remainder = divmod(height, rat_h)
            rat_mult += 1
            height += rat_h - remainder
            width = rat_w * rat_mult
    if not prefer_high:
        width = width - rat_w
        height = height - rat_h
    return width, height


A = TypeVar('A')
def dict_box_list(list_obj:List[A], bin_f) -> Dict[typing.Any, List[A]]:
    ret_dict = {}
    for item in list_obj:
        key = bin_f(item)
        if key in ret_dict:
            ret_dict[key].append(item)
        else:
            ret_dict[key] = [item]
    return ret_dict

T = TypeVar('T')

class UniqueList(list[T]):
    def __init__(self, iterable=None):
        super(UniqueList, self).__init__()
        self.set = set()
        lne = 0
        if iterable is not None:
            for i in iterable:
                self.set.add(i)
                this_len = len(self.set)
                if this_len>lne:
                    super(UniqueList, self).append(i)
                lne = this_len

    def append(self, key: T):
        if key not in self.set:
            super(UniqueList, self).append(key)
            self.set.add(key)

    def add(self, key: T):
        return self.append(key)

    def remove(self, value: T) -> None:
        self.set.remove(value)
        super(UniqueList, self).remove(value)

    def __contains__(self, item: T):
        return item in self.set

    def pop(self, index=None) -> T:
        item = super(UniqueList, self).pop(index)
        self.set.remove(item)
        return item

    def insert(self, index, object: T):
        try:
            index = self.index(object)
            super(UniqueList, self).pop(index)
        except ValueError:
            self.set.add(object)
        super(UniqueList, self).insert(index, object)


class FileSearcher(object):
    # FileFoundException = FileFoundException  # Legacy Support
    RETURN_ALL = lambda x: True

    def __init__(self, path, confirmation_function=RETURN_ALL, list_dirs=False):
        self.path = path
        self.stack_frames = [(self.path, os.listdir(self.path), 0)]
        self.execF = confirmation_function
        self.list_dirs = list_dirs

    def __iter__(self):
        return self

    def NonRecursive(self):
        """
        This is a generator for non recursive behaviors
        :return:
        """
        path_, strc_, place_ = self.stack_frames.pop()
        list_dirs = self.list_dirs
        for path in strc_:
            fso = os.path.join(path_, path)
            if os.path.isdir(fso):
                if list_dirs: yield fso
            else:
                if self.execF(fso):
                    yield fso
                    # raise FileFoundException(fso)
                    # else:
                    # self.stack_frames.append((path_, strc_, place_))
                    # yield fso

    def __next__(self):
        flags_ = True
        path_, strc_, place_ = self.stack_frames.pop()
        while flags_:
            for i in range(place_, len(strc_)):
                place_ += 1  # for next iteration
                fso = os.path.join(path_, strc_[i])
                if os.path.isdir(fso):
                    self.stack_frames.append((path_, strc_, place_))
                    try:
                        self.stack_frames.append((fso, os.listdir(fso), 0))  # Uses space instead of pulling files twice
                    except WindowsError:
                        pass
                    if self.list_dirs: return fso
                    break
                else:
                    if self.execF(fso):
                        self.stack_frames.append((path_, strc_, place_))
                        return fso
                        # raise FileFoundException(fso)
                        # else:
                        # self.stack_frames.append((path_, strc_, place_))
                        # return fso
            try:
                path_, strc_, place_ = self.stack_frames.pop()
            except IndexError:
                flags_ = False
        raise StopIteration()


def check_pop(d, k):
    if k in d:
        return d[k]
    else:
        return None