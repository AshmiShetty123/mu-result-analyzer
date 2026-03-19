import pdfplumber
import re
import pandas as pd


def convert_mu_pdf_to_csv(pdf_path, output_csv_path, college_code=None):

    students = []
    current_semester = "Unknown"

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages in PDF: {total_pages}")

        # Detect semester from page 1
        page1_text = pdf.pages[0].extract_text()
        if page1_text:
            sem_match = re.search(r'Semester\s*-\s*(\w+)', page1_text, re.IGNORECASE)
            if sem_match:
                current_semester = sem_match.group(1)

        print(f"Semester detected: {current_semester}")

        for page_num, page in enumerate(pdf.pages, start=1):

            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            n = len(lines)

            i = 0
            while i < n:

                line = lines[i].strip()

                # Skip lines like "Regular"
                if line.upper() == "REGULAR":
                    i += 1
                    continue

                # Detect student line
                student_match = re.match(
                    r'(\d{7})\s+(.*?)\s+(?:Regular\s+)?(MALE|FEMALE)\s+\([^)]+\)\s+MU-(\d+)\s*:\s*(.*)',
                    line
                )

                if student_match:

                    seat = student_match.group(1).strip()
                    name = student_match.group(2).strip()

                    # Ignore wrong name detection
                    if name.upper() == "REGULAR":
                        i += 1
                        continue

                    gender = student_match.group(3).strip()
                    col_code = student_match.group(4).strip()
                    col_name = student_match.group(5).strip()

                    result = ""
                    sgpi = ""

                    # Scan next lines for result and TOT row
                    for j in range(i + 1, min(i + 25, n)):

                        next_line = lines[j]

                        # Detect PASS / FAIL
                        if not result:
                            if re.search(r'\bPASS\b', next_line):
                                result = "PASS"
                            elif re.search(r'\bFAIL\b|\bFAILED\b', next_line):
                                result = "FAIL"

                        # Detect SGPI from TOT row
                        if next_line.strip().startswith("TOT"):

                            parts = next_line.split()

                            try:
                                sgpi = float(parts[-1])
                            except:
                                sgpi = ""

                            break

                    # If FAIL → CGPA = 0
                    if result == "FAIL":
                        sgpi = 0

                    # If result missing but CGPA exists
                    if result == "" and sgpi != "":
                        result = "UNKNOWN"

                    student_data = {
                        "Seat No": seat,
                        "Name": name,
                        "Gender": gender,
                        "College Code": col_code,
                        "College Name": col_name,
                        "Semester": current_semester,
                        "CGPA": sgpi,
                        "Result": result
                    }

                    # Filter by college code if user entered
                    if college_code:
                        if str(col_code) == str(college_code):
                            students.append(student_data)
                    else:
                        students.append(student_data)

                i += 1

    print(f"\nTotal students parsed: {len(students)}")

    if students:
        df = pd.DataFrame(students)
        df["CGPA"] = pd.to_numeric(df["CGPA"], errors="coerce")

        df.to_csv(output_csv_path, index=False)

        print(f"Colleges in CSV: {df['College Code'].unique().tolist()}")

    else:
        df = pd.DataFrame(columns=[
            "Seat No", "Name", "Gender", "College Code",
            "College Name", "Semester", "CGPA", "Result"
        ])
        df.to_csv(output_csv_path, index=False)

    print(f"\n✅ CSV saved to: {output_csv_path}")

    return output_csv_path