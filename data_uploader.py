import os
from dotenv import load_dotenv
import json
import time
import tqdm
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from pinecone import Pinecone, ServerlessSpec
from langchain.embeddings import OpenAIEmbeddings

load_dotenv()

# initialize embeddings
embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002") #  used to generate vector embeddings for the company metrics descriptions

# MongoDB 
mongo_uri = os.getenv("MONGO_URI")  
mongo_client = MongoClient(mongo_uri)  
db = mongo_client["sustainability_db"]

# ensure the collection exists in MongoDB 
try:
    collection = db["company_metrics"]
    collection.insert_one({"_id": "test_document"})
    collection.delete_one({"_id": "test_document"})  
except CollectionInvalid:
    # If collection doesn't exist, it will automatically be created during insertions
    collection = db["company_metrics"]

# Pinecone API initialization
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENV = os.getenv('PINECONE_ENV')  
PINECONE_INDEX_NAME = "company-key-data"

# create an instance of the Pinecone class
pc = Pinecone(api_key=PINECONE_API_KEY)

# ensure Pinecone index exists
if PINECONE_INDEX_NAME not in [index.name for index in pc.list_indexes()]:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',  
            region=PINECONE_ENV  
        )
    )

pinecone_index = pc.Index(PINECONE_INDEX_NAME)

# load company data from the database
with open("database.json", 'r') as database_file:
    company_data = json.load(database_file)

# batch size for uploads
UPLOAD_BATCH_SIZE = 1

# process each company's data
for company_name in company_data.keys():
    for report_year in company_data[company_name]:
        print(f"Processing: {company_name}, {report_year}")
        cleaned_data_path = os.path.join('cleaned', company_name, f"{report_year}.json")

        # load cleaned data
        try:
            with open(cleaned_data_path, 'r') as cleaned_file:
                cleaned_entries = json.load(cleaned_file)
        except FileNotFoundError:
            print(f"Cleaned data file not found for {company_name}, {report_year}. Skipping.")
            continue

        # initialize containers for documents and entries
        document_batch = []
        mongo_entries = []

        # process entries in the cleaned data
        for entry in tqdm.tqdm(cleaned_entries):
            entry['year'] = report_year
            entry['company'] = company_name

            mongo_entries.append(entry)
            vector_id = f"{company_name}-{report_year}-{entry.get('id')}"
            document_batch.append({
                "id": vector_id,
                "values": embedding_model.embed_query(entry.get("description", "")),  # Ensure description exists
                "metadata": entry
            })

            # upload in batches to Pinecone and MongoDB
            if len(document_batch) >= UPLOAD_BATCH_SIZE:
                # upload batch to Pinecone
                pinecone_index.upsert(vectors=document_batch)
                document_batch = []

                # upload batch to MongoDB
                if mongo_entries:
                    collection.insert_many(mongo_entries) 
                mongo_entries = []

        # upload remaining entries to Pinecone
        if document_batch:
            pinecone_index.upsert(vectors=document_batch)

        # upload remaining entries to MongoDB
        if mongo_entries:
            collection.insert_many(mongo_entries)

        time.sleep(0.1)
