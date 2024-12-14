import os
import json
import tqdm

# create the 'cleaned' directory 
if not os.path.exists('cleaned'):
    os.mkdir('cleaned')

# load the dataset from the database file
with open("database.json", 'r') as database_file:
    dataset = json.load(database_file)

def extract_substring(text, start_marker, end_marker):
    # locate the start marker
    start_pos = text.find(start_marker)
    if start_pos == -1:
        return None  # start marker not found

    # adjust position to the actual start of the substring
    start_pos += len(start_marker)

    # locate the end marker
    end_pos = text.find(end_marker, start_pos)
    if end_pos == -1:
        return None  

    # extract and return the substring
    return text[start_pos:end_pos]

# process each company's data
for company_name in dataset.keys():
    for report_year in dataset[company_name]:
        print(f"Processing {company_name}, {report_year}")

        # paths for input and cleaned output
        source_path = os.path.join('parsed', company_name, f"{report_year}.json")
        cleaned_output_path = os.path.join('cleaned', company_name, f"{report_year}.json")

        # skip processing if the cleaned file already exists
        if os.path.exists(cleaned_output_path):
            continue

        # make sure the parent directory for cleaned data exists
        cleaned_parent_dir = os.path.join('cleaned', company_name)
        if not os.path.exists(cleaned_parent_dir):
            os.mkdir(cleaned_parent_dir)

        cleaned_data = []

        # load parsed data
        with open(source_path, 'r') as parsed_file:
            parsed_pages = json.load(parsed_file)

        # process pages and extract cleaned data
        entry_id = 0 # unique ID for each entry in the dataset
        for page_content in parsed_pages['parsed_pages']:
            if isinstance(page_content, list):
                combined_entries = []
                # loops through each sub_page_content in the page_content (which is a list of sub-pages)
                for sub_page_content in page_content:
                    extracted = extract_substring(sub_page_content, '```start', 'end```')
                    if extracted:
                        try:
                            parsed = json.loads(extracted)
                            for item in parsed:
                                item["id"] = f"{report_year}.{entry_id}"
                                entry_id += 1
                            combined_entries.extend(parsed)
                        except json.JSONDecodeError:
                            pass
                cleaned_data.extend(combined_entries)
            else:
                extracted = extract_substring(page_content, '```start', 'end```')
                if extracted:
                    try:
                        parsed = json.loads(extracted)
                        for item in parsed:
                            item["id"] = f"{report_year}.{entry_id}"
                            entry_id += 1
                        cleaned_data.extend(parsed)
                    except json.JSONDecodeError:
                        pass

        # Save cleaned data to the output file
        with open(cleaned_output_path, 'w') as cleaned_file:
            json.dump(cleaned_data, cleaned_file)
