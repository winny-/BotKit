#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path as ospath

def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance


@singleton
class ignore(object):
    def __init__(self):
        self.ignoredfile = "%s/ignored.txt" % ospath.dirname(ospath.abspath(__file__))
        exists = ospath.isfile(self.ignoredfile)

        data = ""
        with open(self.ignoredfile, 'r') as f:
            data = f.read()
        with open(self.ignoredfile, 'w') as f:
            data = data.lower().replace(" ",'')
            data = data.replace("\n",'').replace("\r",'')
            self._ignored = data.split(',')
            f.write(', '.join(self._ignored))

    def _save(self):
        with open(self.ignoredfile, 'w') as f:
            f.write(', '.join(self._ignored))

    def add(self, user):
        user = user.lower()
        if not user in self._ignored:
            self._ignored.append(user)
            self._save()

    def remove(self, user):
        user = user.lower()
        if user in self._ignored:
            self._ignored = [a for a in self._ignored if a != user]
            self._save()  

    def isignored(self, user):
        return user.lower() in self._ignored

    def getignored(self):
        return self._ignored

    def setignored(self, ignored):
        if type(ignored) != list:
            raise TypeError("List expected got %s!" % type(ignored).__name__)
        else:
            self._ignored = [i.lower() for i in ignored]
