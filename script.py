from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
import random
import regex
import re
import requests
from dotenv import load_dotenv
from pathlib import Path
import os
import sys
import logging

dotenv_path = Path('.env')

if (len(sys.argv) == 2):
  dotenv_path = sys.argv[1]

logfile_name = f"{dotenv_path}.log"

logging.basicConfig(
    filename=logfile_name,
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

load_dotenv(dotenv_path=dotenv_path)

logging.info("Script started...")

# keep these a secret!!
ntfy_auth_key=os.getenv("NTFY_AUTH_KEY")
base_url=os.getenv("BASE_URL")
notification_server_url=os.getenv("NOTIFICATION_SERVER_URL")
topic_name=os.getenv("TOPIC_NAME")

headers = { 
    'User_Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
}

ignore_models = []
ignore_models = ['Lenovo ThinkCentre M910Q USFF (Refurbished/ 2nd hand)']

if random.choice(range(30)) < 2:
  ignore_models = []

def getMessageFromCatalog(catalog):
  res = ""
  for cat in catalog:
    res += f"""
    Model: {cat['Name']}
Price: {cat['Price']}
Available: {cat['Stock']}
Details: [website]({cat['DetailsUrl']})
<<<<<<<<<<<<<<>>>>>>>>>>>>>>

"""
  if res=="":
    res = None
  return res

def sendFlash(message):  
  if message is None:
    logging.info("sendFlash received a None Message.")
    return 
  headers = {"Authorization":f"Bearer {ntfy_auth_key}","Tags":"loudspeaker", 'Markdown':'yes','Title':'Device(s) currently for sale'}
  requests.post(f"{notification_server_url}/{topic_name}", data=message,headers=headers)
  logging.info("Message sent.")
  pass

def extractTagText(s:str):
  return re.sub('<[^<>]+>', '', s)  
  
def getInStock(u:str):
  url = base_url  + u
  r = requests.get(url, headers=headers)
  soup = BeautifulSoup(r.content,'html.parser')
  price_div = soup.find('div',{'class':'grid__item medium-up--one-half'})
  rx = "[0-9]* in stock"
  v = regex.findall(rx,price_div.text)[0]
  v = v.replace("in stock","")
  return v

url = base_url + "/collections/all"

visited_pages = ['1']
for_sale_items = []
sold_out_count = 0
for_sale_count = 0
catalogue = []

while True:
  r = requests.get(url , headers=headers)
  soup = BeautifulSoup(r.content,'html.parser')  
  items = soup.find_all('li',{'class':'grid__item'})    
  for item in items:         
    p  =item.find('dl',{'class':'price price--listing'})         
    img = item.find('a', {'class':'grid-view-item__link'})    
    if img is not None:      
      model_name = extractTagText(img.find('span',{'class':'visually-hidden'}).text)
      logging.info(f"Extracted model_name '{model_name}'")
    else:
      sold_out_count += 1                         
      continue
    if p is not None:          
      for_sale_count += 1
      for_sale_items.append(item)        
      price = item.find('span',{'class':'price-item price-item--sale'}).text.strip()      
      details_a = item.find('a',{'class':'grid-view-item__link grid-view-item__image-container full-width-link'})
      details_url = details_a['href']
      if (img is not None):        
        if (model_name not in ignore_models):
          catalogue.append({'Name':model_name,
                            'Price':price,
                            'DetailsUrl':base_url+details_url,
                            'Stock':getInStock(details_url)})
    else:
      sold_out_count += 1                         
  
  has_next_page = soup.find('a',{'class':'btn btn--tertiary btn--narrow'})
  if (has_next_page is not None):
    next_url = base_url + has_next_page['href']        
    parsed_url = urlparse(next_url)
    pages = parse_qs(parsed_url.query)['page']        
    if (pages[-1] not in visited_pages):      
      url = next_url
      visited_pages.append(pages[-1])      
      continue      
  break
logging.info(f"Found {sold_out_count} sold out, and {for_sale_count} for sale.")

sendFlash(getMessageFromCatalog(catalogue))

logging.info(f"Script completed...")
