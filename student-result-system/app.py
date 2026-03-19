from flask import Flask, render_template, request, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
from mu_parser import convert_mu_pdf_to_csv

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


# ── HELPER ────────────────────────────────────────────────────────────────────
def load_filtered_df():
    """Load full CSV and apply college code filter from session if set."""
    csv_path = os.path.join(app.config["OUTPUT_FOLDER"], "result_full.csv")

    if not os.path.exists(csv_path):
        return None, "CSV file not found. Please upload a PDF first."

    if os.path.getsize(csv_path) == 0:
        return None, "CSV file is empty. Parser did not detect any students."

    df = pd.read_csv(csv_path)

    # ensure CGPA is numeric
    df["CGPA"] = pd.to_numeric(df["CGPA"], errors="coerce")

    college_code = session.get("college_code", "").strip()

    if college_code:
        df["College Code"] = df["College Code"].astype(str).str.zfill(4)

        df = df[df["College Code"] == college_code.zfill(4)]

        if df.empty:
            return None, (
                f"No students found for college code '{college_code}'. "
                f"Available codes: {df['College Code'].unique().tolist()}"
            )

    return df, None


# ── REGISTER ──────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users_file = "users.csv"
        new_user = pd.DataFrame([[username, password]], columns=["username", "password"])

        if os.path.exists(users_file):
            old_users = pd.read_csv(users_file)
            new_user = pd.concat([old_users, new_user])

        new_user.to_csv(users_file, index=False)
        return redirect(url_for("login"))

    return render_template("register.html")


# ── LOGIN ─────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        users_file = "users.csv"

        if os.path.exists(users_file):
            users = pd.read_csv(users_file, dtype=str)
            user = users[
                (users["username"].str.strip() == username) &
                (users["password"].str.strip() == password)
            ]
            if not user.empty:
                session["logged_in"] = True
                return redirect(url_for("upload"))

        return "Invalid login"

    return render_template("login.html")


# ── UPLOAD ────────────────────────────────────────────────────────────────────
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files["pdf"]
        college_code = request.form.get("college_code", "").strip()

        # Store college code in session (empty = show all colleges)
        session["college_code"] = college_code

        if file:
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(pdf_path)

            # Always save FULL CSV (all students); filtering happens at display time
            output_csv = os.path.join(app.config["OUTPUT_FOLDER"], "result_full.csv")
            convert_mu_pdf_to_csv(pdf_path, output_csv, college_code=None)

            if os.path.exists(output_csv):
                df_check = pd.read_csv(output_csv)
                print(f"CSV created. Total rows: {len(df_check)}")
                print(f"Colleges in CSV: {df_check['College Code'].unique().tolist()}")
            else:
                print("ERROR: CSV not created!")

            return redirect(url_for("dashboard"))

    return render_template("upload.html")


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    df, error = load_filtered_df()
    if error:
        return error

    try:
        male_count   = len(df[df["Gender"] == "MALE"])
        female_count = len(df[df["Gender"] == "FEMALE"])

        male_pass   = len(df[(df["Gender"] == "MALE")   & (df["Result"] == "PASS")])
        female_pass = len(df[(df["Gender"] == "FEMALE") & (df["Result"] == "PASS")])

        male_pass_percent   = round((male_pass   / male_count)   * 100, 2) if male_count   else 0
        female_pass_percent = round((female_pass / female_count) * 100, 2) if female_count else 0

        pass_count = len(df[df["Result"] == "PASS"])
        fail_count = len(df[df["Result"] == "FAIL"])
        above_9    = len(df[df["CGPA"] >= 9])
        above_8    = len(df[df["CGPA"] >= 8])

        college_stats = df.groupby("College Name").agg(
            pass_count=("Result", lambda x: (x == "PASS").sum()),
            fail_count=("Result", lambda x: (x == "FAIL").sum())
        ).reset_index()

        labels        = college_stats["College Name"].tolist()
        pass_values   = college_stats["pass_count"].tolist()
        fail_values   = college_stats["fail_count"].tolist()
        college_table = college_stats.to_html(classes="college-table", index=False)

        cgpa_labels = ["0-5", "5-6", "6-7", "7-8", "8-9", "9-10"]
        cgpa_values = [
            len(df[(df["CGPA"] >= 0) & (df["CGPA"] < 5)]),
            len(df[(df["CGPA"] >= 5) & (df["CGPA"] < 6)]),
            len(df[(df["CGPA"] >= 6) & (df["CGPA"] < 7)]),
            len(df[(df["CGPA"] >= 7) & (df["CGPA"] < 8)]),
            len(df[(df["CGPA"] >= 8) & (df["CGPA"] < 9)]),
            len(df[(df["CGPA"] >= 9) & (df["CGPA"] <= 10)])
        ]

    except Exception as e:
        return f"Error processing data: {e}"

    return render_template(
        "dashboard.html",
        total=len(df),
        failed=fail_count,
        above_9=above_9,
        above_8=above_8,
        pass_count=pass_count,
        fail_count=fail_count,
        male_count=male_count,
        female_count=female_count,
        male_pass_percent=male_pass_percent,
        female_pass_percent=female_pass_percent,
        labels=labels,
        pass_values=pass_values,
        fail_values=fail_values,
        cgpa_labels=cgpa_labels,
        cgpa_values=cgpa_values,
        college_table=college_table,
        table=df.head(20).to_html(classes="table", index=False)
    )


# ── STATISTICS ────────────────────────────────────────────────────────────────
@app.route("/statistics")
def statistics():
    df, error = load_filtered_df()
    if error:
        return error

    male_count   = len(df[df["Gender"] == "MALE"])
    female_count = len(df[df["Gender"] == "FEMALE"])

    male_pass   = len(df[(df["Gender"] == "MALE")   & (df["Result"] == "PASS")])
    female_pass = len(df[(df["Gender"] == "FEMALE") & (df["Result"] == "PASS")])

    male_pass_percent   = round((male_pass   / male_count)   * 100, 2) if male_count   else 0
    female_pass_percent = round((female_pass / female_count) * 100, 2) if female_count else 0

    pass_count = len(df[df["Result"] == "PASS"])
    fail_count = len(df[df["Result"] == "FAIL"])

    college_stats = df.groupby("College Name").agg(
        pass_count=("Result", lambda x: (x == "PASS").sum()),
        fail_count=("Result", lambda x: (x == "FAIL").sum())
    ).reset_index()

    labels      = college_stats["College Name"].tolist()
    pass_values = college_stats["pass_count"].tolist()
    fail_values = college_stats["fail_count"].tolist()

    cgpa_labels = ["0-5", "5-6", "6-7", "7-8", "8-9", "9-10"]
    cgpa_values = [
        len(df[(df["CGPA"] >= 0) & (df["CGPA"] < 5)]),
        len(df[(df["CGPA"] >= 5) & (df["CGPA"] < 6)]),
        len(df[(df["CGPA"] >= 6) & (df["CGPA"] < 7)]),
        len(df[(df["CGPA"] >= 7) & (df["CGPA"] < 8)]),
        len(df[(df["CGPA"] >= 8) & (df["CGPA"] < 9)]),
        len(df[(df["CGPA"] >= 9) & (df["CGPA"] <= 10)])
    ]

    return render_template(
        "statistics.html",
        pass_count=pass_count,
        fail_count=fail_count,
        labels=labels,
        pass_values=pass_values,
        fail_values=fail_values,
        cgpa_labels=cgpa_labels,
        cgpa_values=cgpa_values,
        male_pass_percent=male_pass_percent,
        female_pass_percent=female_pass_percent
    )


# ── DOWNLOAD CSV ──────────────────────────────────────────────────────────────
@app.route("/download")
def download():
    df, error = load_filtered_df()
    if error:
        return error

    download_path = os.path.join(app.config["OUTPUT_FOLDER"], "result_download.csv")
    df.to_csv(download_path, index=False)
    return send_file(download_path, as_attachment=True, download_name="result.csv")


# ── LOGOUT ────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
