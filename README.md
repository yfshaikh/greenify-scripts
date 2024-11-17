# **Greenify** 🌱
_A Sustainability Platform for a Greener Future_

---

## Table of Contents

1. [Setup](#setup)
2. [Usage](#usage)
3. [Contributors](#contributors)

---

## Setup

1. Clone the repository to your system. You can clone using:
  ```bash
  git clone https://github.com/yfshaikh/greenify-scripts
  cd greenify
  ```
2. Open a Python Virtual Environment:
  ```bash
  python -m venv venv
  .\venv\Scripts\Activate.ps1 (Windows)
  source venv/bin/activate (macOS)
  ```
3. Required dependencies or libraries. You can install these with:
  ```bash
  pip install -r requirements.txt
  ```

4. Configure environment variables required:
   - Create a `.env` file with the following contents:
     ```
     API_KEY=your_api_key (TogetherAI)
     DATABASE_URL=your_database_url (MongoDB and Pinecone)
     ```

---

## Usage

To run the scripts, use the following commands:

### Script 1: [Scraping Web for Reports]
Run the script as follows:
```bash
python database_gen.py
```

### Script 2: [PDF to JSON]
Run the script as follows:
```bash
python process_pdf.py
```

### Script 3: [Parsing of JSON]
Run the script as follows:
```bash
python llm_parse.py
```

### Script 4: [Cleaning Parsed Files]
Run the script as follows:
```bash
python data_cleaner.py
```

### Script 5: [Uploading Cleaned Files to Database]
Run the script as follows:
```bash
python data_uploader.py
```

---

## Contributors

- Omar Ahmad
- Omer Akbar
- Saad Makda
- Yusuf Shaikh
