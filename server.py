import os

from flask import Flask

from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    send_from_directory,
    url_for
)

from werkzeug.utils import secure_filename

import spacy

from core import entity_recognizer
import db_connection

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf'}

class AppServer(Flask):
    def __init__(self, *args, **kwargs):
        super(AppServer, self).__init__(*args, **kwargs)
        self.nlp = spacy.load("en_core_web_sm")

app = AppServer(__name__, template_folder='web/templates', static_folder='web/static')

# helper functions
def update_metadata(document):
    try:
        db_connection.atlas.collection.insert_one(document)
    except Exception as e:
        print(e)

def upload_to_google_cloud(file, filename):
    pass

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#test database connectivity
@app.route("/connection")
def test():
    db_name = db_connection.db['database']
    return render_template("test.html", db=db_name)

@app.route("/no-result-found")
def unknown():
    return render_template("unknown.html")	
	
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            query = request.form['query']
            query_result = handle_search(query)
            if query_result is not None:
                records, count = query_result
                return display_result(records, count)
            
            return render_template("unknown.html")
        
        except Exception as e:
            return print(e)
            
    return render_template("index.html")


@app.route('/result')
def display_result(records, count):
    return render_template("result.html", records=records, count=count)


@app.route('/collection', methods=['GET', 'POST'])
def handle_upload():

    if request.method == "POST":
        
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        try:
            file = request.files['file']
            
        except Exception as e:
            print(e)
            
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        
        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            # save local reference
            location = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(location)
            file_size = os.path.getsize(location)

            # parse and extract document features
            parsed_doc = entity_recognizer.extraction_wrapper(location)

            update_metadata({"filename": filename, "parsed_doc": parsed_doc})

            return jsonify(name=filename, size=file_size, result={"status": "Successfully parsed document and uploaded reference to Atlas cluster", "parsed_doc": parsed_doc})
        
        return jsonify(name="lost", size="in bits", result={"status": "Network error uploading the file"})
    
    return render_template("collection.html")

def prepare(query_params):
    # prepare and return query statement from the list of entity tuples received..
    pass

def execute(query_statement):
    # execute the query and return the result
    records = db_connection.atlas.collection.find()
    records_count = db_connection.atlas.collection.find().count()
    print("success: ", records)
    return (records, records_count)

def handle_search(query):
    print("query received: {}".format(query))
    doc = app.nlp(query)

    query_params = list()
    
    for ent in doc.ents:
        if ent.label_ is not None:
            entities = (ent.label_, ent.text)
            query_params.append(entities)

    if len(query_params) > 0:
        query_statement = prepare(query_params)
        return execute(query_statement) # return json containing meta-records and filename..
    
    return None

if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.run(port=5000)
