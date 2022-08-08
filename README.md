# DutyFree and MercadoLibre scraper
This project was our first approach to web scraping. The objective was to easily analyze the price gap between fragrances in MercadoLibre and Duty Free Shop due to the financial situation in Argentina. 

# :file_cabinet: Data Collection 
* The first step was to properly scrape data from the Duty Free Shop.
* Once Dufry data was collected, it was later used to search for MercadoLibre matching products.
* When all data from MercadoLibre was obtained, several filters were necessary to narrow down the search to only one winning listing. 

### Challenges

:apple: DutyFree:
* Sizes: There were some listings that contain multiple sizes, others that didn't contain even one.
* Prices: Each size must be matched with its price. Furthermore, some products had discount prices that had to be taken into account. 
* Errors: In multiple occasions, listings returned a 404 error, since there wasn't stock available and the page was poorly designed. 

:handshake: MercadoLibre:
