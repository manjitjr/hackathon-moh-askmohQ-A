# Q&A Knowledge Base Cleaner

A simple web application to upload, clean, and prepare Excel files containing questions and answers for AI knowledge bases.

## Features

- 📤 Upload Excel files (.xlsx, .xls)
- 🧹 Automatic data cleaning:
  - Removes duplicates
  - Trims whitespace
  - Removes empty entries
  - Normalizes text formatting
- 📊 Statistics dashboard
- 👀 Preview cleaned data
- 💾 Export in multiple formats (JSON, CSV, Excel)

## Quick Start

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Start the server:
```bash
python3 app.py
```

3. Open the website:
```bash
open index.html
```

## How to Use

1. **Upload**: Drag and drop your Excel file or click to browse
2. **Process**: Click "Clean & Process" to clean your data
3. **Review**: Check the statistics and preview the cleaned data
4. **Download**: Export in your preferred format (JSON, CSV, or Excel)

## Excel File Format

Your Excel file should contain at least two columns:
- **Question** column (can be named: "Question", "Q", or similar)
- **Answer** column (can be named: "Answer", "A", "Ans", or similar)

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python Flask
- **Data Processing**: Pandas, OpenPyXL
