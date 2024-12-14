import requests
from bs4 import BeautifulSoup
import os
import json

# companies to fetch reports for
companies = [
    'cbre'
]

# cutoff year for fetching reports
OLDEST_YEAR = 2023

# base URLs used for constructing search and report URLs
BASE_SEARCH_URL = "https://www.responsibilityreports.com/Companies?search="
BASE_REPORT_URL = "https://www.responsibilityreports.com"

# load previously stored data if available
data_file = 'database.json'
data = {}
if os.path.exists(data_file):
    with open(data_file, 'r') as f:
        data = json.load(f)

# function to construct the full search URL
def construct_search_url(company_name):
    return f"{BASE_SEARCH_URL}{company_name}"

# function to construct the full report URL
def construct_full_url(relative_url):
    return f"{BASE_REPORT_URL}{relative_url}"

# main function
# responsible for processing a single company, downloading its most 
# recent and archived reports, and saving them locally
def process_company(company_name):
    os.makedirs('data', exist_ok=True)

    # fetch the search page for the company
    search_response = requests.get(construct_search_url(company_name))
    search_soup = BeautifulSoup(search_response.text, 'html.parser')
    # print(search_soup)

    # extract the first company's info from the search results
    company_element = search_soup.find('span', class_='companyName')
    if not company_element:
        print(f"No results found for {company_name}")
        return

    company_link = company_element.find('a')
    company_title = company_link.text.strip()

    # skip if the company is already processed
    if company_title in data:
        print(f"{company_title} already processed.")
        return

    # initialize data storage for the company
    data[company_title] = []
    company_url = construct_full_url(company_link['href'])
    print(company_url)

    # fetch the company's main page
    company_response = requests.get(company_url)
    company_soup = BeautifulSoup(company_response.text, 'html.parser')
    # print(company_soup)

    # directory to store reports for this company
    company_dir = os.path.join('data', company_title)
    os.makedirs(company_dir, exist_ok=True)

   # Download the most recent report
    try:
        recent_report_section = company_soup.find('div', class_='most_recent_content_block')
        
        if recent_report_section:
            # locate the link within the 'view_btn' div
            view_btn_div = recent_report_section.find('div', class_='view_btn')
            if view_btn_div:
                recent_link = view_btn_div.find('a', class_='btn_form_10k')
                if recent_link and recent_link.text.strip():
                    # extract the year from the text content
                    recent_year_text = recent_report_section.find('span', class_='bold_txt').text.strip()
                    recent_year = recent_year_text[:4]
                    print(f"Most recent report year: {recent_year}")  
                    
                    # save the report if the year meets the cutoff
                    if int(recent_year) >= OLDEST_YEAR:
                        save_report(recent_link['href'], recent_year, company_dir, company_title)
                    else:
                        print(f"Report year {recent_year} is older than the cutoff ({OLDEST_YEAR}).")
                else:
                    print(f"No valid link found in the 'view_btn' section for {company_title}.")
            else:
                print(f"No 'view_btn' div found in the most recent report section for {company_title}.")
        else:
            print(f"No 'most_recent_content_block' section found for {company_title}.")
    except Exception as e:
        print(f"Failed to download the most recent report for {company_title}: {e}")


    # download archived reports
    try:
        archived_reports = company_soup.find_all('span', class_='btn_archived download')
        for report in archived_reports:
            report_link = report.find('a')['href']
            report_year = report.parent.find('span', class_='heading').text.strip()[:4]
            if int(report_year) >= OLDEST_YEAR:
                save_report(report_link, report_year, company_dir, company_title)
    except Exception as e:
        print(f"Failed to download archived reports for {company_title}: {e}")

# function to save a report PDF locally
def save_report(relative_url, year, directory, company_title):
    report_url = construct_full_url(relative_url)
    response = requests.get(report_url)
    file_name = f"{year}.pdf"
    file_path = os.path.join(directory, file_name)
    with open(file_path, 'wb') as report_file:
        report_file.write(response.content)
    data[company_title].append(year)
    print(f"Saved report for {company_title} ({year}).")

# process each company in the list
for company in companies:
    process_company(company)

# save the updated data to the database file
with open(data_file, 'w') as f:
    json.dump(data, f, indent=4)
