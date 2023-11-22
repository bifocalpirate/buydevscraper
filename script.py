from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
import random
import regex
import requests


base_url = "https://www.buyyourdevice.co.za"
headers = { 
    'User_Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
}

ignore_models = ['Lenovo-ThinkCentre-M910q-Tiny']
# ignore_models = []
if random.choice(range(10)) < 8:
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
    return
  headers = {'Authorization':'Bearer tk_3wow5z8vkbxj0q6obkqfhlvvhwx6c','Tags':'loudspeaker', 'Markdown':'yes','Title':'Device(s) currently for sale'}
  requests.post("https://notifications.notlocalhost.dev:8082/price-flashes", data=message,headers=headers)
  pass

def extractProduct(s:str):
  rx = "s\/.*---"  
  v =regex.findall(rx,s)[0]
  v = v.replace("s/","")
  v = v.replace("---","")
  return v
  
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
    if p is not None:          
      for_sale_count += 1
      for_sale_items.append(item)        
      price = item.find('span',{'class':'price-item price-item--sale'}).text.strip()
      img = item.find('img', {'class':'grid-view-item__image'})
      details_a = item.find('a',{'class':'grid-view-item__link grid-view-item__image-container full-width-link'})
      details_url = details_a['href']
      if (img is not None):
        model_name = extractProduct(img['data-src'])
        if (model_name not in ignore_models):
          catalogue.append({'Name':model_name,
                            'Price':price,
                            'DetailsUrl':base_url+details_url,
                            'Stock':getInStock(details_url)})                         
  
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

sendFlash(getMessageFromCatalog(catalogue))

