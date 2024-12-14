import sys
import os
# add the parent directory of the script to the Python module search path, 
# allowing it to import modules from that directory, like llm.together_textgen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm.together_textgen import text_generator as together_text_generator

import os
import json
import tqdm
import threading
import time

# use TogetherAI's text generation
generate_text_function = together_text_generator

# helper function to generate a structured prompt for analysis
# formats the prompt with the page_data to extract key metrics from the page
def generate_prompt(page_data):
    return """
You are an analyst extracting key metrics and points from a page in an official document.
Your task is to identify relevant data points related to a company's corporate social responsibility (CSR) efforts. 
You do not care about redundant information or irrelevant points.
You only extract key points that provide useful insights about a company's actions, statistics, or commitments related to CSR.

The output should be a list of objects, where each object represents a single point or fact, and contains the following properties:
- `value`: The value of the point or fact, which can be a number, a metric, or a descriptive text.
- `metric`: A boolean indicating whether the value is a metric or not.
- `topic`: The topic of the point or fact, which can be "E" for environmental, "S" for social, or "G" for governance.
- `description`: A brief description of the point or fact, providing context and additional information.
- `tags`: An array of keywords or tags associated with the point or fact, which can be used for filtering or searching.

Do not include general statements. Only include points mentioning organizations, statistics, or proven action.
You respond with concise and accurate JSON formatted output, like as follows:\n
## Input\n
```start
[
    "Renewable electricity  Our retail stores, data centers, and offices  around the world currently source 100 percent  renewable electricity.",
    "Over 70 percent of companies on Apple\u2019s  Supplier List \u2014 those suppliers that make  up 98 percent of Apple\u2019s direct spend for  materials, manufacturing, and assembly of  our products worldwide \u2014 have committed to  100 percent renewable electricity.",
    "In addition,  many other smaller suppliers have also made these commitments.",
    "About 1.5  gigawatts of Apple-created renewable  electricity projects account for over 90 percent  of the renewable electricity our facilities use.",
    "In fiscal  year 2021, Apple avoided 180,000 metric tons  of CO 2e by shifting the mode of transport and  reducing product weight through the removal   of the power adapter from the box of  iPhone devices.",
    "And we\u2019ve expanded our relationship with Bureau of Energy Resources, initiating new government contracts.",
    "We also offer  our U.S. employees a transit subsidy of up to $100 per month, and at our Cupertino and surrounding Santa Clara Valley campus, we offer free coach buses to commute to and from our corporate offices.",
    "Apple has invested in the 2300-acre IP Radian Solar project in Brown County, Texas."
]
end```

## Output\n
```start
[
    {
        "value": "70 percent",
        "metric": true,
        "topic": "E",
        "description": "Percent of companies on Apple's Supplier List that have committed to 100 percent renewable electricity, making 98 percent of Apple's direct spend for materials, manufacturing, and assembly of products worldwide.",
        "tags": ["supplier", "renewable energy"]
    },
    {
        "value": "1.5 gigawatts",
        "metric": true,
        "topic": "E",
        "description": "Created from renewable energy projects that account for over 90 percent of the renewable electricity our facilities use.",
        "tags": ["renewable energy"]
    },
    {
        "value": "180,000 metric tons",
        "metric": true,
        "topic": "E",
        "description": "Metric tons of CO 2e avoided by shifting the mode of transport and reducing product weight through the removal of the power adapter from the box of iPhone devices.",
        "tags": ["carbon emissions"]
    },
    {
        "value": "$100",
        "metric": true,
        "topic": "S",
        "description": "Monthly transit subsidy for employees.",
        "tags": ["employee benefits"]
    },
    {
        "value": "Bureau of Energy Resources",
        "metric": false,
        "topic": "G",
        "description": "Expansion of relationship with Bureau of Energy Resources with new government contracts.",
        "tags": ["partnerships"]
    },
    {
        "value": "none",
        "metric": false,
        "topic": "S",
        "description": "Offer free coach buses to commute to and from corporate offices at Cupertino and surrounding the Santa Clara Valley campus.",
        "tags": ["employee benefits"]
    },
    {
        "value": "IP Radian Solar project",
        "metric": false,
        "topic": "E",
        "description": "Offer free coach buses to commute to and from corporate offices at Cupertino and surrounding the Santa Clara Valley campus.",
        "tags": ["renewable energy"]
    }
]
end```
Note that topic of the point or fact can only be "E", "S", or "G".

Provide analysis output for the following data, as a JSON list:\n
## Input\n
```start""" + str(page_data) + "end```## Output\n"""


# create directory for parsed results
if not os.path.exists('parsed'):
    os.mkdir('parsed')

# load company data
with open("database.json", 'r') as database_file:
    company_data = json.load(database_file)

# process each company's data
for company_name in company_data.keys():
    for report_year in company_data[company_name]:
        print(f"Processing {company_name}, {report_year}")

        # file paths for input and parsed output
        source_path = os.path.join('text', company_name, f"{report_year}.json")
        destination_path = os.path.join('parsed', company_name, f"{report_year}.json")

        # skip already processed files
        if os.path.exists(destination_path):
            continue

        # ensure parent directories exist
        parent_directory = os.path.join('parsed', company_name)
        if not os.path.exists(parent_directory):
            os.mkdir(parent_directory)

        parsed_results = [] # store the parsed data
        # reads the input JSON file (source_path), which contains the raw data of the document, 
        # and loads it into the document_data variable
        with open(source_path, 'r') as source_file:
            document_data = json.load(source_file)

        # threaded task to process a page
        def process_page_in_thread(page_content):
            try:
                result = generate_text_function(generate_prompt(page_content))
                parsed_results.append(result)
            except Exception as error:
                print(f"Error processing page: {error}")
                try:
                    time.sleep(1.1)
                    first_half = page_content[:len(page_content) // 2]
                    second_half = page_content[len(page_content) // 2:]
                    result_first = generate_text_function(generate_prompt(first_half))
                    result_second = generate_text_function(generate_prompt(second_half))
                    parsed_results.append([result_first, result_second])
                except Exception as retry_error:
                    print(f"Retry failed for {company_name}, {report_year}: {retry_error}")

        # manage threading for processing document pages
        threads = []
        num_threads = 4
        for batch_index in tqdm.tqdm(range(len(document_data['pages']) // num_threads)):
            for page in document_data['pages'][batch_index * num_threads:(batch_index + 1) * num_threads]:
                thread = threading.Thread(target=process_page_in_thread, args=(page,))
                threads.append(thread)
                thread.start()
                time.sleep(1.1)
            for thread in threads:
                thread.join()

        # save parsed results
        with open(destination_path, 'w') as destination_file:
            json.dump({'parsed_pages': parsed_results}, destination_file)
