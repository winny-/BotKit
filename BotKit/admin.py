#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from os import path as ospath

def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

@singleton
class admin(object):
    def __init__(self):
        self.adminfile = "%s/admins.txt" % ospath.dirname(ospath.abspath(__file__))
        exists = ospath.isfile(self.adminfile)

        data = ""
        with open(self.adminfile, 'r') as f:
            data = f.read()
        with open(self.adminfile, 'w') as f:
            self._admins = data.lower().replace(" ",'').split(',')
            f.write(', '.join(self._admins))

    def _save(self):
        with open(self.adminfile, 'w') as f:
            f.write(', '.join(self._admins))

    def add(self, user):
        user = user.lower()
        if not user in self._admins:
            self._admins.append(user)
            self._save()

    def remove(self, user):
        user = user.lower()
        if user in self._admins:
            self._admins = [a for a in self._admins if a != user]
            self._save()  

    def isadmin(self, user):
        return user.lower() in self._admins

    def getadmins(self):
        return self._admins