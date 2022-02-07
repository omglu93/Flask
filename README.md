# Degree Data Flask REST API
## _The project is still under construction._


The DD API will enable the user to pull degree data based on geographical location and date. Degree days are essentially a simplified representation of outside-air-temperature data. They are widely used for calculations relating to the effect of outside air temperature on building energy consumption.

"Heating degree days", or "HDD", are a measure of how much (in degrees), and for how long (in days), outside air temperature was lower than a specific "base temperature" (or "balance point"). They are used for calculations relating to the energy consumption required to heat buildings.

"Cooling degree days", or "CDD", are a measure of how much (in degrees), and for how long (in days), outside air temperature was higher than a specific base temperature. They are used for calculations relating to the energy consumption required to cool buildings.


## Calculation baselines

- 10.5 C
- 15.5 C
- 18.5 C


## Requirements

The REST API requires a Token from https://www.weatherapi.com/

The token is to be placed in a api.py file with the following content
```
API_TOKEN = Your Token
```
