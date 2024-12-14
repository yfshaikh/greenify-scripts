import os
import json
import re
from PyPDF2 import PdfReader
import spacy

# load the small English SpaCy model (en_core_web_sm) to tokenize and parse text
nlp = spacy.load("en_core_web_sm")

# create a directory to store extracted text data if it doesn't exist
os.makedirs('text', exist_ok=True)

# function to extract text from all pages of a PDF document
def extract_text_from_pdf(pdf_path):
    """Extracts text from all pages of a PDF file."""
    pdf_reader = PdfReader(pdf_path)
    for page in pdf_reader.pages:
        # return the text of each page one by one without storing the full content in memory at once
        yield page.extract_text()

# load the database of company data
with open("database.json", 'r') as file:
    company_data = json.load(file)

# function to check if a sentence is coherent
def is_sentence_coherent(sentence):
    """
    Determines if a sentence is coherent by checking
    for the presence of at least one subject and one verb.
    """
    has_subject = any(token.dep_.endswith("subj") for token in sentence)
    has_verb = any(token.pos_ == "VERB" for token in sentence)
    return has_subject and has_verb

# iterate through each company and its associated report data
for company_name, reports in company_data.items():
    for report_year in reports:
        print(f"Processing report for {company_name} ({report_year})")

        # path to the PDF file and its corresponding JSON file 
        pdf_path = os.path.join('data', company_name, f"{report_year}.pdf")
        company_text_dir = os.path.join('text', company_name)
        json_file_path = os.path.join(company_text_dir, f"{report_year}.json")

        # skip if this report has already been processed
        if os.path.exists(json_file_path):
            print(f"Report {report_year} for {company_name} already processed. Skipping.")
            continue

        # ensure the directory for storing text data exists
        os.makedirs(company_text_dir, exist_ok=True)

        # dictionary structure to store extracted text, organized by pages
        processed_data = {'pages': []}

        # extract and process text from each page of the PDF
        for page_text in extract_text_from_pdf(pdf_path):
            # replace newlines with spaces for better sentence parsing
            cleaned_text = re.sub(r'\n+', ' ', page_text)

            # process the cleaned text using SpaCy's NLP model
            doc = nlp(cleaned_text)

            # filter coherent sentences
            coherent_sentences = [
                str(sentence) for sentence in doc.sents if is_sentence_coherent(sentence)
            ]

            # add coherent sentences to the page data
            if coherent_sentences:
                processed_data['pages'].append(coherent_sentences)

        # save the processed text data to a JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(processed_data, json_file) # json.dump() function takes a Python object and converts it into a JSON string

        print(f"Processed report for {company_name} ({report_year}) saved.")
