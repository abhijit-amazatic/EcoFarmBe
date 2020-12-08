import requests
from bs4 import BeautifulSoup
import dateutil.parser

class Scrapper(object):
    """
    Screpper class.
    """
    def __init__(self):
        self.urls = {
            'CDFA': ['http://calcannabis.cdfa.ca.gov/news/',
                ('dt', 'dd'),
                'http://calcannabis.cdfa.ca.gov',
                'div.col-md-8 dl.dl-horizontal'],
            'BCC': ['https://www.bcc.ca.gov/media/press_releases.html',
                ('li', 'li'),
                'https://www.bcc.ca.gov',
                'main.main-primary article',],
            'CDPH': ['https://www.cdph.ca.gov/Programs/CEH/DFDCS/MCSB/Pages/News.aspx',(
                    'td.ms-rteTableLastCol-5', 'td.ms-rteTableFirstCol-5'),
                '', 'div.ms-rtestate-field tbody']
        }
    
    def get_html(self, url):
        return requests.get(url).content
    
    def get_bs4_object(self, url):
        """
        Get bs4 object for url.
        """
        body = self.get_html(url)
        return BeautifulSoup(body, 'html.parser')
    
    def get_news(self, type_):
        """
        Get news.
        """
        news_list = list()
        data = self.urls.get(type_)
        if data:
            soup = self.get_bs4_object(data[0])
            news = soup.select(data[3])
            for row in news:
                if '.' in data[1][0]:
                    d = data[1][0].split('.')
                    dts = row.find_all(d[0], {'class': d[1]})
                else:
                    dts = row.find_all(data[1][0])
                if '.' in data[1][1]:
                    d = data[1][1].split('.')
                    dds = row.find_all(d[0], {'class': d[1]})
                else:
                    dds = row.find_all(data[1][1])
                news = list(zip(dts, dds))
                news_list.extend([{
                    'date': dateutil.parser.parse(row[0].text.split('-')[0].encode('ascii', 'ignore').decode('utf-8')),
                    'title': row[1].text.encode('ascii', 'ignore').decode('utf-8'),
                    'link_id': data[2] + row[1].find('a')['href']
                         } for row in news])
        return news_list
        