# ⚡ AI Resume Match Analyzer

A Streamlit-powered web application that intelligently analyzes a resume against a job description using natural language processing (NLP). It scores how well the resume matches, visualizes strengths and gaps, and generates an executive summary and downloadable reports.

---

## 🔍 Features

* 📥 Upload resume (PDF, DOCX, or TXT)
* 📋 Paste or upload job description
* 📊 Generate a match score (skills, experience, education, keywords)
* 🧠 NLP-based analysis using Python and Streamlit
* 📈 Interactive dashboard (gauge, radar, skills matrix)
* 📝 Executive summary + full text report download

---

## 🚀 Getting Started

### 🔧 Prerequisites

* Python 3.8+
* pip

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/abhinavramsv/resume-analyzer.git
cd resume-analyzer

# (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 🖥️ Run the App

```bash
streamlit run ui_app.py
```

---

## 📁 Project Structure

```
resume-analyzer/
├── resume_parser.py       # Extracts text from resumes
├── scoring.py             # Calculates match scores
├── visualizer.py          # Generates charts and dashboards
├── report_gen.py          # Builds text-based reports
├── ui_app.py              # Streamlit UI app
├── main.py                # CLI alternative (optional)
├── requirements.txt       # Python dependencies
├── sample_resume.txt      # Example resume file
├── sample_jd.txt          # Example job description
└── README.md              # You're here
```

---

## 📎 Example Inputs

* `sample_resume.txt` – Resume of John Doe
* `sample_jd.txt` – Data Analyst job description

---

## 📚 Technologies Used

* Python
* Streamlit
* Plotly
* SpaCy / NLTK (for NLP)
* PyPDF2 / python-docx

---

## 🛠️ Future Enhancements

* Add support for LinkedIn profile parsing
* Improve experience extraction with NLP
* Support multiple resumes for batch processing

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙌 Acknowledgements

Built using Streamlit and open-source Python libraries.

---
