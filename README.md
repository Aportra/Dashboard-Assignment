# PNW Car Search Dashboard

This repository contains a tactical dashboard built using **Python**, **Dash**, and **Plotly**. The dashboard is designed to help users search for used cars listed on Craigslist in the Pacific Northwest (PNW) area. It allows users to filter listings by various parameters such as state, city, price, make, year, and more. The dashboard also includes features for sorting and analyzing the data, and provides visualizations to assist prospective car buyers.

## Features

- **Car Listings Table**: View detailed information about cars listed in different states and cities.
- **Map of Car Listings**: Visualize car listings on an interactive map with filters applied.
- **Price Analysis**: Analyze price trends and relationships between car features (such as odometer and price).
  
### Filtering Options

- **State & City**: Filter listings by state and city within the PNW region.
- **Price**: Set a price range using a slider.
- **Odometer**: Filter listings by mileage range.
- **Year**: Select cars based on their year of production.
- **Car Make**: Filter by specific car manufacturers.

### Visualizations

- **Interactive Map**: Displays the geographic locations of the car listings on a map, with tooltips for quick information.
- **Median Price Over Time**: Shows how the median price for different car makes changes over time.
- **Price vs. Odometer**: Scatter plot of car price against log-transformed odometer readings.
- **Count of Listings by Make**: Bar chart showing the number of listings by car manufacturer.

## Technologies Used

- **Dash**: Web framework for building analytical web applications.
- **Plotly**: Library for creating interactive charts and visualizations.
- **Pandas**: Data manipulation and analysis library.
- **Numpy**: Numerical computing library.

## Project Structure

```bash

