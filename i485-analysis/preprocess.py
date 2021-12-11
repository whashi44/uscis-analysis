"""
Preprocess the uscis I485 Adjustment of status data
1. Download the csv files from the website
2. Rename the file and omit unnecessary files
3. Extract information from csv and save it into csv file
Currently works from 2014 qtr 1 through 2019 qtr 2
"""

# standard library
from os.path import basename
import os
from urllib.parse import urljoin
import re
import shutil
import csv

# External library
import requests
from bs4 import BeautifulSoup
from natsort import natsorted
import numpy as np
import pandas as pd
from fiscalyear import FiscalQuarter


def main():
    data_path = "data"
    raw_path = "raw"
    # download(raw_path)
    # rename(data_path, raw_path)
    data, header = extract(data_path)
    modify(data, header)

# -----------------------------------------------------------------------------------------------------


def download(path="raw"):
    """
    Automatically download all the csv file from uscis website with specified url
    """

    try:
        print(f"Making folder: {path}")
        os.mkdir(path)
    except FileExistsError:
        raise
    # finally:
    #     os.chdir(path)
    #     print(f"Changed directory to: {path}")

    base = "https://www.uscis.gov/tools/reports-studies/immigration-forms-data?topic_id=20658&field_native_doc_issue_date_value%5Bvalue%5D%5Bmonth%5D=&field_native_doc_issue_date_value_1%5Bvalue%5D%5Byear%5D=&combined=&items_per_page=100"
    with requests.Session() as s:
        # stream will make it generator and parse faster
        url = s.get(base, stream=True).text
        # Specifying the parse is necessary to avoid warning
        soup = BeautifulSoup(url, "html.parser")
        # creating generator with all the url that end with .csv
        # the soup.select will include other unnecessary html parameter, hence urljoin is used to extract just the href
        for link in (urljoin("", a["href"]) for a in soup.select("a[href$='.csv']")):
            # Since the link still has value such as "https://....", basename() is used to extract only the csv file name to open
            file = basename(link)
            # Creating a path to raw folder to save file
            file_path = f"{path}/{file}"
            with open(file_path, "wb") as write_file:
                print(f"saving .csv file:{link} to path")
                write_file.write(requests.get(link).content)

# -----------------------------------------------------------------------------------------------------


def rename(data_path="data", raw_path="raw"):
    """
    Rename files because the original file name had inconsistency
    Remove other files that is not useful for analysis (i.e. one with inconsistent format, especially before 2014)
    Remove fy 2013 csv because the csv format was completely different.
    """
    # data_path = "data"
    # raw_path = "raw"

    # make data deposit directory
    try:
        print(f"Making folder: {data_path}")
        os.mkdir(data_path)
    except FileExistsError:
        raise
    # finally:
    #     # Change directory to raw so that raw files can be retrieved
    #     os.chdir(raw_path)
    #     print(f"Changed directory to: {raw_path}")

    # Get all the files from raw folder
    all_files = os.listdir(raw_path)

    # Extracting useful files
    files = [file for file in all_files if "fy" in file]
    # Extracting unuseful files
    remove_files = [file for file in all_files if "fy" not in file]

    years = []
    quarters = []

    # Find year and quarter information from file name ex. "I485_data_fy2014_qtr3.csv"
    for file in files:
        numbers = re.findall(
            r"\d+",  # for number
            file
        )  # 0th is I485, 1st is fiscal year, 2nd is quarter
        years.append(numbers[1])
        quarters.append(numbers[2])

    # Rename files to uniform format, and save copy to "data" folder
    for file, year, quarter in zip(files, years, quarters):
        print(f"Copying and renaming the filename from: \n{file}")
        new_name = f"I485_data_fy{year}_qtr{quarter}.csv"
        shutil.copyfile(f"{raw_path}/{file}", f"{data_path}/{new_name}")
        print(f"To: {new_name}")

    # remove special file, which has inconsistent format
    print(f"Removing special file, the 2013 quarter 3, due to its inconsistent format")
    os.remove(f"{data_path}/I485_data_fy2013_qtr3.csv")

# -----------------------------------------------------------------------------------------------------


def extract(data_path="data"):
    """Read csv file from data folder and perform following:
        1. Extract header information from the first file, assuming all other file have same/similar header information
        2. Extract state and city application information
        3. Convert them to numpy array and return
    """
    # # Change directory to data folder
    # try:
    #     os.chdir("data")
    # except FileNotFoundError:
    #     raise FileNotFoundError

    # Grab all the files so you can iterate through
    files = os.listdir(data_path)
    # I want to use the newest report to extract the basic header because it has the most information.
    files = natsorted(files, reverse=True)

    # Grab header information
    with open(f"{data_path}/{files[0]}", "r") as read_file:
        # read file as csv, it automatically skip comma if there is quote
        csv_file = csv.reader(read_file, delimiter=",")
        header = []

        for row in csv_file:
            # removing leading and trailing white space
            row = list(map(str.strip, row))
            # lower casing all the item to avoid word mismatch
            row = list(map(str.lower, row))
            # for special case, 2019 qtr 1 and qtr 2
            other_count = 1
            # Looking at the file structure, there is a category for green card application,
            # As well as the result of application for each category, hence concatnate would be
            # appropriate to increase consistency and uniformity
            # pre-2017qtr1 has family-based1, instead of family-based
            if "family-based" in row or "family-based1" in row:
                category_name = ""  # for "family-based", "employment"
                categories = row  # for green card category
                results = next(csv_file)  # for application status
                found_family = False  # flag
                found_other = False
                # For concatinating the category and result
                for category, status in zip(
                    categories, results
                ):
                    # Checking the condition, if category name appears, store the category name
                    # If not, then use the previous category name
                    # Then, cancatnate the category name and the status with ":"

                    # For family based green card
                    if "family" in category:
                        category_name = "Family"
                        # family should come first, hence the flag is true
                        found_family = True
                    # For employment based green card
                    elif "employment" in category:
                        category_name = "Employment"
                    # For humanitarian based green card
                    elif "humanitarian" in category:
                        category_name = "Humanitarian"
                    # For other category
                    elif "other" in category:
                        category_name = "Other"
                        found_other = True
                    # For total count of application
                    elif "total" in category:
                        category_name = "Total"
                    # For 2019 qtr 1 and qtr 2 with shifted "total"
                    elif other_count == 4:
                        category_name = "Total"
                    # For keeping track of "other" to make sure "total" is included
                    elif found_other:
                        other_count += 1
                    # For first couple empty cases
                    elif not found_family:
                        pass

                    # There are some numbers after the result (i.e. Application2) so strip those
                    status = "".join(i for i in status if not i.isdigit())

                    # concatnate to create better category
                    value = category_name + ":" + status
                    header.append(value)

        # Fill those empty header
        header[0:3] = ["State", "City", "Abbreviation"]

        # eliminate those empty strings in the end
        header = header[0:23]

        # Add year and quarter
        header.append("Year")
        header.append("Quarter")

    # Grab states and city information
    city_cases = []

    for file in files:
        print(f"working on file:{file}")
        # Find the year and quarter from the file name
        numbers = re.findall(r"\d+", file  # for number
                             )  # 0th is I485, 1st is fiscal year, 2nd is quarter
        year = numbers[1]
        quarter = numbers[2]

        with open(f"{data_path}/{file}", "r") as read_file:
            # csv_file is a list of list
            csv_file = csv.reader(read_file, delimiter=",")

            # Each row is a list
            for row in csv_file:
                # removing leading and trailing white space
                row = list(map(str.strip, row))
                # lower casing for case-insensitive comparison
                row = list(map(str.lower, row))

                # If it finds the section of the total number of case, store that
                if "total" in row[0]:
                    total_case_numbers = row

                # For looping through states
                # if the first column(state) is alabama, or alaska (before 2017_qtr3)
                if row[0] == "alabama" or row[0] == "alaska":
                    # Loop until final city, vermont
                    while row[1] != "vermont":
                        # if 1st column is not empty, meaning this row is state
                        if (row[0] != ""):
                            # grab the state name
                            state_name = row[0].title()
                            # For special case in 2017, 1st quarter for guam, the row is shifted so we need to grab it now
                            if (year == "2017") and (quarter == "1") and (state_name == "Guam"):
                                # Grab current line because it has all the information
                                row_with_state = row
                                row_with_state[0] = state_name
                                # check the next line, which has the city name
                                row = next(csv_file)
                                # removing leading and trailing white space
                                row = list(map(str.strip, row))
                                # create lower case
                                row = list(map(str.lower, row))
                                # Grab city name
                                row_with_state[1] = row[1].title()
                                # capitalize state abbreviation
                                row_with_state[2] = row[2].upper()
                                row_with_state[23] = year
                                row_with_state[24] = quarter

                        # if the 1st column is empty, meaning this row is city
                        # some year has repeating the header at the middle of the line, hence 2nd if statement is counter for that (see 2018 qtr 1 Kentucky)
                        elif (row[0] == "" and row[1] != ""):
                            row_with_state = row
                            # adding the state name to the initial part
                            row_with_state[0] = state_name
                            # initialize the city name
                            row_with_state[1] = row_with_state[1].title()
                            # capitalize state abbreviation
                            row_with_state[2] = row_with_state[2].upper()
                            # Some year has empty strings in the end of the row, hence simply substitute
                            try:
                                row_with_state[23] = year
                                row_with_state[24] = quarter
                            # Some states do not have empty strings in the of the row, hence handle that
                            except IndexError:
                                # for pre 2014, there is no city abbreviation, insert empty string to avoid index error later on
                                if year == "2014":
                                    row_with_state.insert(2, "")

                                # other case append instead of inject
                                row_with_state.append(year)
                                row_with_state.append(quarter)

                            # Add to state list
                            city_cases.append(row_with_state)

                        # keep checking the next row
                        row = next(csv_file)
                        # removing leading and trailing white space
                        row = list(map(str.strip, row))
                        row = list(map(str.lower, row))  # create lower case

    # convert the list of list to array of array
    city_cases = np.array([np.array(x)[0:25] for x in city_cases])
    # print(np.shape(city_cases))
    # convert the list to array
    header = np.array(header)

    print("Converting empty strings, 'd' and 'D' to NaN")
    # Convert the empty strings and d or D to NaN
    city_cases[city_cases == ''] = np.NaN
    city_cases[city_cases == 'd'] = np.NaN
    city_cases[city_cases == 'D'] = np.NaN
    # Convert the hyphen to 0
    print("Converting '-' to 0")
    city_cases[city_cases == '-'] = 0

    return city_cases, header


def modify(data, header):
    """ Take the data and convert to pandas data frame
    """
    # Dataframe for easier manipulation
    df_original = pd.DataFrame(data=data, columns=header)
    # We don't need abbreviation for cities, so drop those
    df_original = df_original.drop(columns='Abbreviation')
    # Currently, there are excess columns, so simplify by adding category row
    # So there will be only columns for State,city,received,approved,denied,pending,category
    # First, let's slice the data frame into location(state & city), family, employment, humanitarian, other, total, and time (year & quarter)
    # Create a copy to avoid settingwithcopywarning
    location = df_original.iloc[:, 0:2].copy()
    family = df_original.iloc[:, 2:6].copy()
    employment = df_original.iloc[:, 6:10].copy()
    humanitarian = df_original.iloc[:, 10:14].copy()
    other = df_original.iloc[:, 14:18].copy()
    total = df_original.iloc[:, 18:22].copy()
    time = df_original.iloc[:, 22:24].copy()

    # Using fiscal year package, we can identify the date and year
    # start attribute indicate the start of the fiscal quarter, date() is simply to return only dates, not time
    time['Start_date'] = time.apply(
        lambda row: FiscalQuarter(row.Year, row.Quarter).start.date(), axis=1)
    time['End_date'] = time.apply(
        lambda row: FiscalQuarter(row.Year, row.Quarter).end.date(), axis=1)

    # Store all data frame into list to loop through
    all_df = [family, employment, humanitarian, other, total]
    # Let's rename the columns name, and then put "category" column with corresponding names
    category_list = ['Family', 'Employment', 'Humanitarian', 'Other', 'Total']
    # I also want to change the name of the columns
    new_names = ['Received', 'Approved', 'Denied', 'Pending']
    for i, df in enumerate(all_df):
        # Grab column names
        col_names = list(df.columns.values)
        # Create dictionary key = col names, value = new_names
        name_dict = dict(zip(col_names, new_names))
        # Rename the columns i.e. Family:application_received -> Received
        df = df.rename(columns=name_dict)
        # Keep the category i.e. Family, employment
        df['Category'] = category_list[i]
        # concatinate location(state,city) this data frame, and time
        df = pd.concat([location, df, time], axis=1, sort=False)

        all_df[i] = df
    df_final = pd.concat(all_df)

    # There is annoying comma in the number, so remove those
    for col in new_names:
        df_final[col] = df_final[col].str.replace(',', '')

    save_file = 'I485_data_all.csv'
    # save to csv file, without the index name
    df_final.to_csv(save_file, index=False)
    print(f"saved to {save_file}")
    # print(df_final)


if __name__ == "__main__":
    main()
