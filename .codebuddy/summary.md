# Project Summary

## Overview
The project uses Python as the main programming language. It involves fetching electricity consumption data from ENTSO-E Transparency Platform using a custom data fetcher class. The data is then processed, analyzed, and visualized using various functions and classes.

## Languages, Frameworks, and Main Libraries
- **Languages:** Python
- **Frameworks:** None
- **Main Libraries:** Pandas, Matplotlib, Requests, Aiohttp

## Purpose
The project aims to fetch, process, and analyze electricity consumption data from the ENTSO-E Transparency Platform. It involves fetching generation and flow data for Portugal and Spain, resampling the data to a standard granularity, and visualizing the results.

## Relevant Files
- **Build Files/Configuration Files/Project Files:**
  - `./src/__init__.py`
  - `./src/analyzer.py`
  - `./src/config.py`
  - `./src/data_fetcher.py`
  - `./src/main.py`
- **Source Files:**
  - Source files can be found in the `./src/` directory.
- **Documentation Files:**
  - Documentation files are located in the `./docs/` directory.
  
## Relevant Tools
- The Jupyter Notebook `./tools/df_inspector.ipynb` is used to inspect and visualize the fetched data using PandasGUI.

This summary provides an overview of the project, its purpose, the main languages and libraries used, relevant files for building and configuration, source files location, and where to find documentation files.