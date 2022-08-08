# Imports for Selenium
from doctest import master
from re import X
from webbrowser import Chrome
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import math
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Imports for BeautifulSoup
from bs4 import BeautifulSoup

# Imports required for reading and writing Google Sheets
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pprint import pprint

# Imports required for getting USD Official price
import requests

# Imports for time
from datetime import datetime

# Arguments for Selenium driver
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1200')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--log-level=3')

# Connecting to Google Sheets
SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = None
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Sheets ID and range
SAMPLE_SPREADSHEET_ID = '197-ZvJk6cWsTInval9KbI_wR26dY4wpArVReqfPvwl4'
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Getting USD Official price
URL = 'https://www.dolarsi.com/api/api.php?type=valoresprincipales'
json = requests.get(URL).json()
usd_official = float(str(json[0]['casa']['venta']).replace(',','.'))

# -------------------------------------------------------
# DUTY FREE SECTION

# Defining driver
driver_dufry = webdriver.Chrome(options=chrome_options)

# URLS - FreeShop
url_fragrances = ['https://buenosaires.shopdutyfree.com/es/beauty/fragrance/para-el','https://buenosaires.shopdutyfree.com/es/beauty/fragrance/para-ella']

# Loop to obtain each fragrance URL
single_urls = [] 
x=0

while x < len(url_fragrances):
    driver_dufry.get(url_fragrances[x]) # Open url_fragrances
    driver_dufry.maximize_window()

    time.sleep(2)

    pages = math.ceil(float(driver_dufry.find_element(by=By.CLASS_NAME,value='toolbar-number').text)/40) # Obtains amount of subpages to iterate later
    elems = driver_dufry.find_elements(by=By.CLASS_NAME, value='product-item-link')
    page_links = [elem.get_attribute('href') for elem in elems]
    single_urls.append(page_links)

    o=2 # Since the URL changes from page 2 on, another loop was added in order to contemplate this case

    while o <= pages:
        driver_dufry.get(url_fragrances[x]+'?p='+str(o)) # URL modified, page number added
        elems = driver_dufry.find_elements(by=By.CLASS_NAME, value='product-item-link')
        page_links = [elem.get_attribute('href') for elem in elems]
        single_urls.append(page_links)

        time.sleep(2)
        o+=1
    
    x+=1 

# XPath to obtain fragrance sizes
xpath_sizes = '/html/body/div[3]/main/div/div/div[1]/div/div[1]/div[7]/form/div[1]/div/div[1]/div/div/div['

# List used to update Google Sheets values
gsheets_list = [['Marca','Modelo','Género','URL','Size','Precio - USD Oficial','Precio - ARS']]

# List used to get values from MercadoLibre
meli_list = []

# Loop through each Dufry product
for xa in range(len(single_urls)):

    for h in range(len(single_urls[xa])):
        print('Current progress: '+str(xa)+' of '+str(len(single_urls)))
        print('Subpage current progress: '+str(h)+' of '+str(len(single_urls[xa])))
        print('-----------------------------------------------------------------------')

        # Opens each product
        driver_dufry.get(single_urls[xa][h])
        time.sleep(2)

        # Obtains and cleans each fragrance size
        sizes_id = [elementos.text for elementos in driver_dufry.find_elements(by=By.CSS_SELECTOR, value='div[id^="option-label-size-480-item-"]')] # Obtains each available size 
        sizes_clean_id = [ele for ele in sizes_id if ele.strip()] # Cleans the list by removing the empty values
        
        # In case there is no size option
        if len(sizes_clean_id)==0:

            # Get and clean price
            fragrance_price = [elementos.text for elementos in driver_dufry.find_elements(by=By.CLASS_NAME, value='price')]
            fragrance_price = list(filter(None, fragrance_price))
            new_price = []

            for string in fragrance_price:
                new_price.append(string.replace('US$','').replace(',','.'))

            # Obtains information table
            labels = [elementos.text for elementos in driver_dufry.find_elements(by=By.CSS_SELECTOR, value='th[class="col label"]')]
            data = [elementos.text for elementos in driver_dufry.find_elements(by=By.CSS_SELECTOR, value='td[class="col data"]')]

            # Create a dictionary out of 'labels' and 'data'
            label_data_dict = dict(zip(labels,data))

            # From 'label_data_dict', get brand and gender
            # Contemplates english and spanish cases
            if label_data_dict.get('Marca'):
                marca = label_data_dict['Marca']
            elif label_data_dict.get('Brand'):
                marca = label_data_dict['Brand']
            else:
                marca = ''

            if label_data_dict.get('Género'):
                genero = label_data_dict['Género']
            elif label_data_dict.get('Gender'):
                genero = label_data_dict['Gender']
            else:
                genero = ''

            # Obtains model
            try:
                modelo = driver_dufry.find_element(by=By.XPATH,value='/html/body/div[3]/main/div/div/div[1]/div/div[1]/div[1]/h1/span[3]').text
            except NoSuchElementException: # In case a 404 error happens
                modelo = ''

            # Format model name to improve MercadoLibre search
            if modelo == '':
                final_model = ''
            elif modelo[-1]=='S':
                final_model = modelo[:-1]
            else:
                final_model = modelo

            if 'ml' in final_model:
                tamaño_ml_entitulo = final_model.split('ml')
                size_ml = str(tamaño_ml_entitulo[0][-3:]).strip()+'ml'
    
            # Format gender, simplifying gender for Google Sheets
            if genero=='Para él':
                genero='Hombre'
            elif genero=='Para ella':
                genero='Mujer'
            else:
                genero=''

            # To contemplate 404 errors
            if len(new_price)==0:
                sent_price = '0'
            else:
                sent_price = new_price[len(new_price)-1]
            
            # Appends all values to 'gsheets_list' and 'meli_list'
            gsheets_list.append([marca, final_model, genero, single_urls[xa][h],size_ml,sent_price,usd_official*float(sent_price)])
            meli_list.append([marca, final_model, genero, single_urls[xa][h],size_ml,sent_price,usd_official*float(sent_price)])
        
        # In case there are size options
        # Loop to click each size and obtain fragrance characteristics
        x=1
        while x <= len(sizes_clean_id):
            try:
                # Clicks each price and saves every possible size-price combination
                driver_dufry.find_element(by=By.XPATH, value=xpath_sizes+str(x)+']').click()
                size_ml = driver_dufry.find_element(by=By.XPATH, value=xpath_sizes+str(x)+']').text
                fragrance_price = [elementos.text for elementos in driver_dufry.find_elements(by=By.CLASS_NAME, value='price')]

                # Cleans price
                fragrance_price = list(filter(None, fragrance_price))
                new_price = []

                for string in fragrance_price:
                    new_price.append(string.replace('US$','').replace(',','.'))

                # When first size is clicked, all relevant information is appended to 'gsheets_list'
                if x==1:
                    # Obtains information table
                    labels = [elementos.text for elementos in driver_dufry.find_elements(by=By.CSS_SELECTOR, value='th[class="col label"]')]
                    data = [elementos.text for elementos in driver_dufry.find_elements(by=By.CSS_SELECTOR, value='td[class="col data"]')]

                    # Create a dictionary out of 'labels' and 'data'
                    label_data_dict = dict(zip(labels,data))

                    # From 'label_data_dict', get brand and gender
                    # Contemplates english and spanish cases
                    if label_data_dict.get('Marca'):
                        marca = label_data_dict['Marca']
                    else:
                        marca= label_data_dict['Brand']

                    if label_data_dict.get('Género'):
                        genero = label_data_dict['Género']
                    else:
                        genero = label_data_dict['Gender']
                    
                    # Obtains model
                    modelo = driver_dufry.find_element(by=By.XPATH,value='/html/body/div[3]/main/div/div/div[1]/div/div[1]/div[1]/h1/span[3]').text
                    
                    # Format model name to improve MercadoLibre search
                    if modelo[-1]=='S':
                        final_model = modelo[:-1]
                    else:
                        final_model = modelo
                    
                    # Format gender, simplifying gender for Google Sheets
                    if genero=='Para él':
                        genero='Hombre'
                    elif genero=='Para ella':
                        genero='Mujer'

                    # Appends all values to 'gsheets_list' and 'meli_list'
                    gsheets_list.append([marca, final_model, genero, single_urls[xa][h],size_ml,new_price[len(new_price)-1],usd_official*float(new_price[len(new_price)-1])])
                    meli_list.append([marca, final_model, genero, single_urls[xa][h],size_ml,new_price[len(new_price)-1],usd_official*float(new_price[len(new_price)-1])])

                # When selected size is not the first one clicked; brand, model, gender and Dufry URL won't be added to 'gsheets_list' to avoid repetition
                else:
                    gsheets_list.append(['','','','',size_ml,new_price[len(new_price)-1],usd_official*float(new_price[len(new_price)-1])])
                    meli_list.append([marca, final_model, genero, single_urls[xa][h],size_ml,new_price[len(new_price)-1],usd_official*float(new_price[len(new_price)-1])])

            # When size button isn't clickable (out of stock), it raises WebDriverException
            except:
                WebDriverException

            x+=1

# Formatting datetime to update Google Sheets
now = datetime.now() 
date_time = now.strftime('%d/%m/%Y, %H:%M:%S')

# Updating Google Sheets with USD price and last update time
request = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, 
                            range='TC y última update!a1', valueInputOption='USER_ENTERED', body={'values':[['Última update:',date_time],['Dólar oficial:',usd_official]]}).execute()

# -------------------------------------------------------
# MERCADOLIBRE SECTION

# List used to update Google Sheets values
master_meli = [['Precio - MercadoLibre (ARS)','Título de la publicación','URL']]

# Loops through 'meli_list', obtains and cleans data for better results in MercadoLibre search
for x in range(len(meli_list)):
    row_g_sheets = x

    print('Obtaining data from MercadoLibre: ' + str(row_g_sheets) + ' of ' + str(len(meli_list)))
    print('-----')

    brand_search = (meli_list[x][0]).lower()
    model_search = (meli_list[x][1]).lower()
    size_search = ((meli_list[x][4]).rstrip()).lower()
    gender_search = (meli_list[x][2]).lower()
    size_filtro = size_search.replace('ml','')

    if 'for him' in model_search:
        modelo_filtro = model_search.replace(' for him','')
    elif 'for her' in model_search:
        modelo_filtro = model_search.replace(' for her','')
    elif brand_search in model_search:
        modelo_filtro = model_search.replace(brand_search,'')
    else:
        modelo_filtro = model_search

    # Later used for measuring search accuracy
    split_model_words = modelo_filtro.split()

    # 'inp' will be searched in MercadoLibre
    inp = model_search+' '+size_search

    # Formatting inp to match URL properties of MercadoLibre
    out = inp.replace(' ', '-')
    out2 = inp.replace(' ', '%20') 

    # URL for MercadoLibre
    url = 'https://listado.mercadolibre.com.ar/belleza-y-cuidado-personal/perfumes/{}#D[A:{}]'.format(out, out2)
    
    # Gets HTML from MercadoLibre
    result = requests.get(url)
    doc = BeautifulSoup(result.text, 'html.parser')
    
    index = [] # Stores title in bold, listing title, price and URL
    
    listados = doc.find_all('li', class_='ui-search-layout__item')
    for i in range(len(listados)):
        price = listados[i].find('span', class_='price-tag-fraction')
        title = listados[i].find('h2', class_='ui-search-item__title')
        link = (listados[i].find('a')).get('href')
        brand = listados[i].find('span', class_='ui-search-item__brand-discoverability')
        
        # Contemplates empty brand case
        if brand == 'None':
            brand_2 = 'nada'
        else:
            brand_2 = brand.string
        
        price = price.string
        title = (title.string).lower()
        price = float((price.string).replace('.',''))

        index.append([price, title, link, brand_2])
    
    first_filter = [] # Matching brand and size from MercadoLibre and DutyFree for proper comparison
    
    for us in range(len(index)):
        # Contemplates empty brand case
        if(index[us][3]) is None:
            index[us][3] = 'SIN MARCA'

        count_matches = 0
        
        # Matching brand and size
        if brand_search in (index[us][3].lower()) and size_filtro in (index[us][1]): 
            # Appending a degree of coincidence between Duty Free product and MercadoLibre result
            for l in range(len(split_model_words)):
                count_matches += (index[us][1]).count(split_model_words[l])

            if len(split_model_words)==0:
                grado_coincidencia_modelo=0
            else:
                grado_coincidencia_modelo = count_matches / len(split_model_words)

            # Appending those products that surpassed the first filter
            first_filter.append([index[us][0], index[us][1], index[us][2], index[us][3].lower(), grado_coincidencia_modelo])

    # If there is no product that matches size and brand
    if (len(first_filter))==0:
        master_meli.append(['Sin producto en MercadoLibre'])
    
    # In case there are one or more matches
    else:
        gender_listing_count = 0
        second_filter = [] # Checks if any listing contains gender information, if so, it is prioritized. Furthermore, degree of coincidence must be greater than 65%
        third_filter = [] # Select lowest price option

        # Checks if any listing contains gender
        for ya in range(len(first_filter)):
            if gender_search in (first_filter[ya][1]):
                gender_listing_count+=1
        
        if gender_listing_count > 0:
            for yas in range(len(first_filter)):
                if gender_search in (first_filter[yas][1]) and float(first_filter[yas][4])>0.65:
                    second_filter.append([first_filter[yas][0], first_filter[yas][1], first_filter[yas][2], first_filter[yas][3], first_filter[yas][4]])
        
        elif gender_listing_count == 0:
            for ya in range(len(first_filter)):
                # If wrong gender is present in listing, it won't be appended to 'second_filter'
                if gender_search == 'hombre':
                    if 'mujer' not in first_filter[ya][1] and float(first_filter[ya][4])>0.65:
                        second_filter.append([first_filter[ya][0], first_filter[ya][1], first_filter[ya][2], first_filter[ya][3], first_filter[ya][4]])
                elif gender_search == 'mujer':
                    if 'hombre' not in first_filter[ya][1] and float(first_filter[ya][4])>0.65:
                        second_filter.append([first_filter[ya][0], first_filter[ya][1], first_filter[ya][2], first_filter[ya][3], first_filter[ya][4]])

        # Determines lowest price
        if len(second_filter)>0:
            lista_lowest_price = min(u[0] for u in second_filter)
            lowest_price = lista_lowest_price
        else:
            lowest_price = ''
            master_meli.append(['Sin producto en MercadoLibre'])

        # The listing that matches with the lowest price, is appended to the third and final filter
        for ya in range(len(second_filter)):
            if second_filter[ya][0] == lowest_price:
                third_filter.append([second_filter[ya][0], second_filter[ya][1], second_filter[ya][2], second_filter[ya][3], second_filter[ya][4]])
        
        # To avoid having two matching listings, the one with maximum degree of coincidence will be appended to 'master_meli'
        for po in range(len(third_filter)):
            if third_filter[po][4] == max(u[4] for u in third_filter):
                    master_meli.append([third_filter[po][0], third_filter[po][1], third_filter[po][2]])
                    break

# When product isn't available on MercadoLibre, it won't be updated in Google Sheets
for ha in range(len(master_meli)):
    if master_meli[ha][0]=='Sin producto en MercadoLibre':
        gsheets_list[ha][0]='Sin producto en MercadoLibre'

master_ml_2 = list(filter(lambda sub_list: 'Sin producto en MercadoLibre' not in sub_list, master_meli))
compilacion_sheets = list(filter(lambda sub_list: 'Sin producto en MercadoLibre' not in sub_list, gsheets_list))

# Hyperlinks for Google Sheets
master_ml_3 = [['Precio - MercadoLibre (ARS)','Título de la publicación']]
for xas in range(len(master_ml_2)):
    if xas>=1:
        master_ml_3.append([master_ml_2[xas][0],'=HYPERLINK("'+master_ml_2[xas][2]+'";"'+master_ml_2[xas][1]+'")'])

# Update MercadoLibre products in Google Sheets
request = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, 
                            range='General!I2', valueInputOption='USER_ENTERED', body={'values':master_ml_3}).execute()

# Update Duty Free products in Google Sheets
request = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, 
                            range='General!a2', valueInputOption='USER_ENTERED', body={'values':compilacion_sheets}).execute()
