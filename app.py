import os
import random
from flask import Flask, request, render_template_string, send_file, session
import PyPDF2
from pdf2image import convert_from_path
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# HTML Template for the file upload and random page display
template = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Random PDF Page</title>
</head>
<body>
  <h1>Upload a PDF and Get a Random Page</h1>
  <form method="POST" enctype="multipart/form-data">
    {% if not pdf_file %}
      <input type="file" name="pdf_file" accept="application/pdf" required>
      <button type="submit">Upload PDF</button>
    {% else %}
      <button type="submit" name="get_page">Get Random Page</button>
    {% endif %}
  </form>
  {% if page_num %}
  <h2>Random Page {{ page_num }}:</h2>
  <img src="{{ url_for('show_page', page_num=page_num) }}" alt="Random PDF Page" style="max-width: 100%; max-height: 80vh;">
  {% endif %}
</body>
</html>
"""

# Function to extract a random page from the PDF
def get_random_page(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)
        random_page = random.randint(0, total_pages - 1)
        return random_page + 1  # Return random page number

# Function to convert a specific PDF page to an image
def pdf_page_to_image(pdf_path, page_num):
    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
    img = images[0]
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# Main route to upload PDF or get a random page
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'pdf_file' in request.files:  # Check if a file is uploaded
            pdf_file = request.files['pdf_file']
            if pdf_file and pdf_file.filename.endswith('.pdf'):
                filepath = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
                pdf_file.save(filepath)
                session['pdf_path'] = filepath  # Store the file path in session
                return render_template_string(template, pdf_file=True)

        if 'get_page' in request.form:  # If button to get a random page is pressed
            if 'pdf_path' in session:  # Ensure the PDF is available
                pdf_path = session['pdf_path']
                page_num = get_random_page(pdf_path)
                session['random_page'] = page_num  # Store the random page number in session
                return render_template_string(template, page_num=page_num, pdf_file=True)

    return render_template_string(template)

# Route to display the random PDF page as an image
@app.route('/show_page')
def show_page():
    if 'pdf_path' in session and 'random_page' in session:
        pdf_path = session['pdf_path']
        page_num = session['random_page']
        img_bytes = pdf_page_to_image(pdf_path, page_num)
        return send_file(img_bytes, mimetype='image/png')

    return "Error: No PDF file uploaded or random page not selected."

if __name__ == "__main__":
    app.run(debug=True)