# DutyFree and MercadoLibre scraper
This project was our first approach to web scraping. The objective was to easily analyze the price gap between fragrances in MercadoLibre and Duty Free Shop due to the financial situation in Argentina. 

# :file_cabinet: Data Collection and Data Cleansing
* The first step was to properly scrape data from the Duty Free Shop.
* Once Dufry data was collected, it was later used to search for MercadoLibre matching products.
* When all data from MercadoLibre was obtained, several filters were necessary to narrow down the search to only one winning listing. 

### Challenges:

:apple: DutyFree:
* Sizes: There were some listings that contain multiple sizes, others that didn't contain even one.
* Prices: Each size must be matched with its price. Furthermore, some products had discount prices that had to be taken into account. 
* Errors: In multiple occasions, listings returned a 404 error, since there wasn't stock available and the page was poorly designed. 

:handshake: MercadoLibre:
* Search criteria: Listing titles in duty free weren't suitable for MercadoLibre search so they had to be modified using string manipulation. The final take was to search model + size. 
* Filters: Since one search offered multiple listings, a series of filters had to be developed to sort out the best result. Firstly, listings were filtered by matching brand and size, assigning them a degree of coincidence. From the remaining listings, the ones that contained matching gender and a degree of coincidence higher than 65% were selected. Finally, the one with the lowest price was chosen. 

# Technologies:
* Selenium.
* BeautifulSoup.
* Google Sheets API.
* DolarSi API. (https://www.dolarsi.com/api/api.php?type=valoresprincipales)
