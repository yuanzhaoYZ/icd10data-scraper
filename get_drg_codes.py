# -*- coding: utf-8 -*-
import urllib

import grequests
from bs4 import BeautifulSoup
import requests
from multiprocessing import Pool
import pandas as pd

SITE = 'https://www.icd10data.com'
CODES = '{}/ICD10CM/DRG/'.format(SITE)


class Downloader():
    def __init__(self, sites):
        self.sites = sites

    def exception(self, request, exception):
        print("error: {} {}".format(request.url, exception))

    def run(self):
        return grequests.imap(
            (grequests.get(u, timeout=5) for u in self.sites),
            exception_handler=self.exception,
            size=1)


def yieldParentSites():
    resp = requests.get(CODES)
    soup = BeautifulSoup(resp.content, 'html.parser')
    sites = []
    for div in soup.find_all('ul', class_='list'):
        # print(div)
        for child in div.find_all('a'):
            #  https://www.icd10data.com/ICD10CM/Codes/A00-B99/A00-A09
            sites.append(SITE + child['href'])
    return sites


def getcode(tag):
    return tag.text.split(' ')[1].strip()


def getName(tag):
    return tag.text.strip()


def getSubCode(soup):
    for div in soup.find_all('ul', class_='list'):
        return [i.text.strip() for i in div.find_all('a')]


if __name__ == '__main__':
    sites = yieldParentSites()
    d = Downloader(sites)
    res = []
    for p in d.run():
        soup = BeautifulSoup(p.content, 'html.parser')
        x = soup.select(".pageHeading")
        code = getcode(x[0])
        name = getName(x[1])
        group_members = getSubCode(soup)
        mes = {
            "code": code,
            "name": name,
            "group_members": group_members
        }
        print(mes)
        res.append(mes)
    column = ['code','name','group_members']
    df = pd.DataFrame.from_dict(data=res)
    df = df[column]
    df.to_csv('D://drgCodes.csv', mode='a', header=None, encoding='utf-8')
