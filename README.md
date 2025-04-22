# ReadRater

A simple Flask-based web application for browsing and reviewing books.

## Features

- Browse a catalog of books with titles, authors, and optional cover images
- Full-text search by title or author
- User authentication: register, log in, log out
- Authenticated users can:
  - Add new books
  - Edit existing book details
  - Submit reviews (rating + comment)
- MySQL database backend
- Analytics notebook (`analytics.ipynb`) to explore review data with pandas and matplotlib

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Running the App](#running-the-app)
- [Analytics Notebook](#analytics-notebook)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Prerequisites

- Python 3.8+
- MySQL Server
- `pip` package manager

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Meenakshi1402/project_ReadRater.git
   cd project_ReadRater
   ```

2. **Create and activate a virtual environment**
   - On macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - On Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install dependencies**
   ```bash
   pip install flask mysql-connector-python werkzeug pandas numpy matplotlib
   ```

4. **Configure environment variables**
   Create a file named `.env` in the project root with:
   ```env
   SECRET_KEY=<your-secret-key>
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=<your-db-password>
   DB_NAME=readraterdb
   ```

## Database Setup

1. **Start your MySQL server** and log in as a user with permissions to create databases:
   ```sql
   CREATE DATABASE readraterdb;
   USE readraterdb;
   
   CREATE TABLE books (
     id INT AUTO_INCREMENT PRIMARY KEY,
     title VARCHAR(200) NOT NULL,
     author VARCHAR(100) NOT NULL,
     cover_url VARCHAR(255),
     added_at DATETIME DEFAULT CURRENT_TIMESTAMP
   );
   
   CREATE TABLE users (
     id INT AUTO_INCREMENT PRIMARY KEY,
     username VARCHAR(50) UNIQUE NOT NULL,
     password_hash VARCHAR(255) NOT NULL,
     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
   );
   
   CREATE TABLE reviews (
     id INT AUTO_INCREMENT PRIMARY KEY,
     user_id INT NOT NULL,
     book_id INT NOT NULL,
     rating TINYINT NOT NULL,
     comment TEXT,
     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
     FOREIGN KEY (user_id) REFERENCES users(id),
     FOREIGN KEY (book_id) REFERENCES books(id)
   );
   ```

2. **Update `app.py`** or your environment to match your MySQL credentials if different.

## Running the App

With your virtual environment activated and database ready:

```bash
export FLASK_APP=app.py        # macOS/Linux
set FLASK_APP=app.py           # Windows
flask run                      # Launches on http://127.0.0.1:5000
```  
Or simply:  
```bash
python app.py
```

Visit **http://127.0.0.1:5000** in your browser.

## Analytics Notebook

1. Start Jupyter:
   ```bash
   jupyter notebook analytics.ipynb
   ```
2. **Step-by-step cells**:
   - **Imports**:
     ```python
     import mysql.connector
     import pandas as pd
     import numpy as np
     import matplotlib.pyplot as plt
     ```
   - **Database connection & query**:
     ```python
     conn = mysql.connector.connect(
         host="localhost",
         user="root",
         password="<your-db-password>",
         database="readraterdb"
     )
     query = '''
     SELECT r.id AS review_id, r.book_id, b.title, b.author,
            r.rating, r.comment, r.created_at
       FROM reviews r
       JOIN books b ON b.id = r.book_id;
     '''
     df = pd.read_sql(query, conn)
     df.head()
     ```
   - **Average ratings**:
     ```python
     avg_ratings = df.groupby('title')['rating'] \
                     .mean() \
                     .sort_values(ascending=False)
     avg_ratings.head(10)
     ```
   - **Plot distribution**:
     ```python
     df['rating'].value_counts().sort_index().plot(kind='bar')
     plt.title('Rating Distribution')
     plt.xlabel('Rating')
     plt.ylabel('Count')
     plt.show()
     ```

## Project Structure

```
project_ReadRater/
├── app.py
├── analytics.ipynb
├── requirements.txt
├── .gitignore
├── static/
│   └── styles.css
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── book_detail.html
│   ├── add_book.html
│   ├── edit_book.html
│   ├── login.html
│   └── register.html
└── venv/  (virtual environment)
```

## Contributing

Feel free to fork and open pull requests. Please file issues for bugs or features.



