# import webarchive

# with webarchive.open('mechtech.webarchive') as archive:
#     archive.extract('mechtech_template.html')

from bs4 import BeautifulSoup
import lxml

with open('carpooling/templates/mechtech_template.html', 'r') as f:
    soup = BeautifulSoup(f, 'lxml')

print(soup.contents[1])