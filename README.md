# NLP using spaCy transformer and lookups
This is the code repository is for NLP Project with **spaCy**. It contains all the supporting project files necessary to work through to create a web based service in **flask** that can be used to upload the resumes and also search resumes from the database.

Contains a custom trained **named entity recognizer** for extracting the information from the documents. 

# Installation
- run the requirement.txt file 
`pip install -r requirement.tx`


## Setup
- run the server file to open the web application `python server.py`

## Files and their info

**db_connection.py** 
- Help to connect to the data base

**server.py**
- Enables the setup to the server
- Checks the database connection
- Uploads the data onto the database
- Handles the search query to return the matched documents
