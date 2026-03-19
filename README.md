# mu-result-analyzer
Developed a Flask-based web application to extract and analyze Mumbai University result PDFs. Implemented automated PDF parsing using pdfplumber and generated interactive dashboards for college-wise performance, CGPA distribution, and gender-based analysis using Chart.js.

---

## Features

- Upload MU result PDF
- Automatic extraction of:
  - Student details
  - College name & code
  - Semester
  - CGPA
  - Result (PASS/FAIL)
- College-wise result analysis
- Interactive charts using Chart.js
- Gender-based performance insights
- CGPA distribution visualization
- Download processed data as CSV

---

## Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS
- **Data Processing:** Pandas
- **PDF Parsing:** pdfplumber
- **Visualization:** Chart.js

---

## Project Structure
```
project/
│── app.py
│── mu_parser.py
│── templates/
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── dashboard.html
│   ├── statistics.html
│── uploads/
│── outputs/
│── users.csv
```
----

## How to Run

1. Clone the repository

git clone https://github.com/AshmiShetty123/mu-result-analyzer.git
cd mu-result-analyzer

2. Install dependencies

pip install flask pandas pdfplumber

3. Run the app

python app.py

4. Open in browser:

http://127.0.0.1:5000

---

## Key Functionalities

- Parses unstructured MU PDF results into structured CSV
- Detects PASS/FAIL using grading patterns (P/F)
- Generates college-wise analytics
- Provides clean dashboard and statistics view

---

## ⚠️ Note

This project is developed for academic purposes.  
Please do not copy it directly for submissions.

---

## Future Improvements

- Login authentication using database
- Advanced filters (semester, college)
- Export charts as images
- Deploy on cloud (Render / AWS)

---

## Author

Asmhi Shetty
