# USCIS - I485 Adjustment of Status Analysis
Data cleaning and Analysis for Adjustment of status.

USCIS generously provides statistics for their processing performance in their website "Immigration and citizenship Data" <br>URL: https://www.uscis.gov/tools/reports-studies/immigration-forms-data <br>
The USCIS statistics represents the following application results
- Received
- Accepted
- Rejected
- Postponed

for following category:
- Family based
- Employment based
- Other

For each city that has service center for every state.


## Questions
- What is the distribution of the application received among cities?
- Does policy affects application numbers?
- How does the number of case changes over the year?
- Are there any correlation between population and the application case?
- How did COVID-19 affect the application case?
- What are the processing speed of the each cities?



## Data Wrangling
### CSV Downloading
The csv file was downloaded using requests for http request and beautiful soup for CSS search.


### File naming schema
USCIS follows naming schema of "I485_performancedata_fy####_qtr#.csv" with # is a place holder for year or quarter digits.<br>
However, some file name lacks inconsistency due to human error or change in format, such as:
- I485_performancedata_fy2014qtr2.csv (no underscore before qtr)
- I485_Performanced_ata_fy2014qtr3.csv (extra underscore)
- I485_Performancedata_fy2017qtr4.csv (Capitalized P)

Hence, it was necessary to organize the file name and create consistency to

### Data Extraction
USCIS follows default format.
However, some year included some exception to this format, change in format over the year, or format that is hard to analyze using python, including:
- 2013 data was drastically different in terms of format compared to the rest of the year, hence omitted
- updated naming schema from family-based1 to family-based between before 2017 and after 2017
- 2018 qtr 1 had injection of category and application status in the middle of the spreadsheet
- Multilevel column header for category (i.e. family-based) and application status (i.e. Application Received), which is visually appealing in excel, but harder to categorize in csv.
- Multilevel row header to group cities within state
- Some spreadsheets had empty cell, which contributed to the non-uniform csv row length.
- 2019 qtr1 and qtr2 had "Total" for the header shifted up one cell

Therefore, python script was used to parse these data, store them in the pandas data frame, and save to csv file.
