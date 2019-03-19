#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os
import sys
import traceback
from operator import itemgetter

relative_path_add = lambda feel, str_path: sys.path.append(
    os.path.abspath(os.path.join(os.path.split(feel)[0], str_path)))

reT = lambda x: lambda y: x  # return a function that will return the origonal parameter
string_wrap_generator = lambda x: type('', (object,), {'__str__': reT(x)})()

arr_pass_flatten = lambda x: [__ for _ in x for __ in _]


# def sanitize_for_utf8(string_in):
#    string_in.replace(chr(191),'j' )


class Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()


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
