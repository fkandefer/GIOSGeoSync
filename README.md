# Air Quality Dashboard

## Overview

This repository contains a script that automatically fetches air quality data from GIOS sensors measuring **PM10**, **PM2.5**, and **CO** levels across Poland. The script runs every **3 hours** using **GitHub Actions** and updates an **ArcGIS dashboard** with the latest data.

## Dashboard

The latest air quality data is visualized on an interactive ArcGIS dashboard(Outdated due to changes in GIOS API):

➡️ [**Air Quality Dashboard**](https://agh-ust.maps.arcgis.com/apps/dashboards/6475cee14589421b8e38035aeb5df1ca)

## Features

- ✅ **Automated data retrieval and processing** every 3 hours
- ⚡ **Integration with GitHub Actions** for scheduled execution
- 🌍 **Visualization of air quality measurements** on ArcGIS
- 📊 **Supports PM10, PM2.5, and CO concentration data**

## How It Works

1. 🕒 **GitHub Actions Workflow**: The script is triggered automatically every 3 hours.
2. 📥 **Data Collection**: Fetches air quality data from GIOS API.
3. 🛠️ **Processing**: Cleans, formats, and prepares the data for visualization.
4. 📡 **Dashboard Update**: Pushes the processed data to the ArcGIS dashboard.


## License

📝 This project is licensed under the **MIT License**.

