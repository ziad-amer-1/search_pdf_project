import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import pdfplumber

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_FOLDER = "/files"
TXT_FOLDER = "/txt"

app = Flask(__name__)

def getpath(path):
  return os.path.abspath(ROOT_DIR + path)

def is_filename_valid(filename):
  return '.' in filename and filename.rsplit('.')[1].lower() in ALLOWED_EXTENSIONS

if not os.path.exists(getpath(UPLOAD_FOLDER)):
  os.makedirs(getpath(UPLOAD_FOLDER))

if not os.path.exists(getpath(TXT_FOLDER)):
  os.makedirs(getpath(TXT_FOLDER))

def search_keyword_in_file(file_path, keyword):
  with open(file_path, 'r', encoding='utf-8') as file:
    file_content = file.read()
    if keyword.lower() in file_content.lower():
      return os.path.basename(file_path)

def search_keyword_in_files(keyword):
  matching_files = []
  with ThreadPoolExecutor() as exc:
    futures = [
      exc.submit(
        search_keyword_in_file,
        os.path.join(getpath(TXT_FOLDER), filename),
        keyword
      ) for filename in os.listdir(getpath(TXT_FOLDER))
    ]
    for f in futures:
      if f.result():
        matching_files.append(f.result())

    return matching_files

def list_of_pdf_files():
  return os.listdir(getpath(UPLOAD_FOLDER))

def save_file(uploaded_file):
  filename = uploaded_file.filename
  if is_filename_valid(filename):
    target_path_to_pdf = os.path.join(getpath(UPLOAD_FOLDER), filename)
    target_path_to_txt = os.path.join(getpath(TXT_FOLDER), filename.rsplit(".")[0] + ".txt")
    uploaded_file.save(target_path_to_pdf)
    with pdfplumber.open(target_path_to_pdf) as pdf:
      with open(target_path_to_txt, 'w', encoding='utf-8') as text_file:
        for page_num in range(len(pdf.pages)):
          page = pdf.pages[page_num]
          text = page.extract_text()
          text_file.write(text)
          text_file.write('\n')

def save_files(uploaded_files):
  with ThreadPoolExecutor() as exc:
    exc.map(save_file, uploaded_files)
  return "Files uploaded Successfully"

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
  return save_files(request.files.getlist("files"))

@app.route('/pdfs', methods=['GET'])
def list_pdfs():
  pdf_files = list_of_pdf_files()
  return jsonify({"pdf_files": pdf_files})

@app.route("/search", methods=["GET"])
def search():
  keyword = request.args.get('keyword', '')
  if not keyword:
    return jsonify({"message": "keyword is empty"})
  return search_keyword_in_files(keyword)

@app.route("/preview_cv", methods=["GET"])
def preview_cv():
  pdf_filename = request.args.get('filename', '')
  if not pdf_filename:
    return "filename can't be empty", 500
  return send_file(os.path.join(getpath(UPLOAD_FOLDER), pdf_filename), mimetype='application/pdf')

@app.route("/", methods=["GET"])
def home():
  return "<h1>Hi</h1>"

CORS(app, resources={r'/*': {'origins': '*'}})
if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True, threaded=True)
