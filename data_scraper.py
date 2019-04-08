# -*- coding: utf-8 -*-
import grequests
from bs4 import BeautifulSoup
import requests
from multiprocessing import Pool
import pandas as pd

SITE = 'https://www.icd10data.com'
CODES = '{}/ICD10CM/Codes/'.format(SITE)


class Downloader():
    def __init__(self, sites):
        self.sites = sites

    def exception(self, request, exception):
        print("error: {} {}".format(request.url, exception))

    def run(self):
        return grequests.imap(
            (grequests.get(u, timeout=5) for u in self.sites),
            exception_handler=self.exception,
            size=5)


def yieldParentSites():
    resp = requests.get(CODES)

    soup = BeautifulSoup(resp.content, 'html.parser')
    for div in soup.find_all('ul', class_='ulPopover'):
        for child in div.find_all('a'):
            yield SITE + child['href']


def my_replacer(text):
    return text.strip().replace('\r', '').replace('\n', '')


class Parser():
    def __init__(self, response):
        self.response = response
        self.content = response.content
        self.soups = []

    def yieldLinks(self, soup):
        for div in soup.find_all('ul', class_='ulPopover'):
            for child in div.find_all('a'):
                yield SITE + child['href']

    def runParent(self):
        soup = BeautifulSoup(self.content, 'html.parser')
        return self.yieldLinks(soup)

    @property
    def code(self):
        return self.parseCode(self.response.url)

    @classmethod
    def parseCode(cls, url):
        return url.split('/')[-1]

    def getName(self, soup):
        tag = soup.title
        name = tag.text.split(':')[1].strip().replace("\"", '')
        return name

    def getSubClass(self, soup):
        tag = soup.ol
        # print(tag.text)
        class_list = tag.text.replace('›', '').replace('\n', ',').split(',')
        subclasses = list(filter(lambda x: len(x.strip()) > 1, class_list))
        length = len(subclasses)
        code_version = '' if length < 1 else subclasses[0].strip()
        L1_key = '' if length < 2 else subclasses[1].strip()
        L1_class = '' if length < 3 else subclasses[2].strip()
        L2_key = '' if length < 4 else subclasses[3].strip()
        L2_class = '' if length < 5 else subclasses[4].strip()
        L3_key = '' if length < 6 else subclasses[5].strip()
        L3_class = '' if length < 7 else subclasses[6].strip()
        return code_version, L1_key, L1_class, L2_key, L2_class, L3_key, L3_class

    def getSynonyms(self, soup):
        span = soup.find(text='Approximate Synonyms')
        if not span:
            return
        table = span.parent.next_element.next_element.next_element
        return [my_replacer(i.text) for i in table.find_all('li')]

    def getApplicableTo(self, soup):
        span = soup.find(text='Applicable To')
        if not span:
            return
        table = span.parent.next_element.next_element.next_element
        return [my_replacer(i.text) for i in table.find_all('li')]

    def getClinicalInformation(self, soup):
        span = soup.find(text='Clinical Information')
        if not span:
            return
        table = span.parent.next_element.next_element.next_element
        return [my_replacer(i.text) for i in table.find_all('li')]

    def getDRGCodes(self, soup):
        span = soup.find(text='ICD-10-CM ')
        if not span:
            return
        table = span.parent.next_element.next_element.next_element.next_element.next_element.next_element.next_element.next_element.next_element
        return [i.text.split(' ')[0].strip() for i in table.find_all('li')]

    def getBodyContent(self, soup):
        return soup.select('div ~ div.container.vp > *')[0].text

    def runChild(self):
        soup = BeautifulSoup(self.content, 'html.parser')
        name = self.getName(soup)
        code_version, L1_key, L1_class, L2_key, L2_class, L3_key, L3_class = self.getSubClass(soup)
        applicableTo = self.getApplicableTo(soup)
        ClinicalInformations = self.getClinicalInformation(soup)
        synonyms = self.getSynonyms(soup)
        drg_codes = self.getDRGCodes(soup)
        # body_content = self.getBodyContent(soup)
        return self.code, name, code_version, L1_key, L1_class, L2_key, L2_class, L3_key, L3_class, synonyms, applicableTo, ClinicalInformations, drg_codes


class Scraper():
    def mapChild(self, content):
        p = Parser(content)
        return p.runChild()

    def runForSites(self):
        d = Downloader(yieldParentSites())
        for parent in d.run():
            p = Parser(parent)
            children = Downloader(p.runParent())
            yield children

    def runForSynonyms(self):
        d = Downloader(yieldParentSites())
        for parent in d.run():
            p = Parser(parent)
            children = Downloader(p.runParent())
            with Pool(10) as p:
                out = p.map(self.mapChild, children.run())
                print('parsed', len(out), 'pages for site', parent.url)
                yield out


def loadAllCodes():
    # todo make this non blocking
    s = Scraper()
    print('running scraper')
    for items in s.runForSynonyms():
        # todo: bulk save items because this is ridiculous
        count = 0
        data_list = []
        for item in items:
            if item:
                code, name, code_version, L1_key, L1_class, L2_key, L2_class, L3_key, L3_class, synonyms, applicableTo, ClinicalInfos, drg_codes = item
                single_data = {
                    "code": my_replacer(code),
                    "name": my_replacer(name),
                    "code_version": my_replacer(code_version),
                    "L1_key": my_replacer(L1_key),
                    "L1_class": my_replacer(L1_class),
                    "L2_key": my_replacer(L2_key),
                    "L2_class": my_replacer(L2_class),
                    "L3_key": my_replacer(L3_key),
                    "L3_class": my_replacer(L3_class),
                    "synonyms": synonyms,
                    "applicableTo": applicableTo,
                    "ClinicalInfos": ClinicalInfos,
                    'DRGCodes': drg_codes
                }
                data_list.append(single_data)
                count += 1
        print('saved', count, 'items to the database')

        column = ['code', 'name', 'code_version', 'L1_key', 'L1_class', 'L2_key', 'L2_class', 'L3_key', 'L3_class',
                  'synonyms', 'applicableTo', 'ClinicalInfos', 'DRGCodes']
        # code_list = list(filter(lambda x: (x[code].find('.') != -1), data_list))
        code_list = []
        for i in data_list:
            s_code = i['code']
            if (s_code.find('.') != -1):
                code_list.append(i)
        try:
            df = pd.DataFrame.from_dict(data=code_list)
            df = df[column]
            df.to_csv('/home/ec2-user/icd10_codes_res_with_drgCodes.csv', mode='a', header=None, encoding='utf-8')
        except KeyError:
            df.to_csv('/home/ec2-user/error_codes.csv', mode='a', header=None, encoding='utf-8')


if __name__ == '__main__':
    loadAllCodes()
