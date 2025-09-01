# AI Study Buddy (Polished)
Quick start:
1. Unzip, cd into folder.
2. python -m venv venv
   source venv/bin/activate   # Mac/Linux
   venv\Scripts\activate    # Windows
3. pip install -r requirements.txt
4. python app.py
5. Open http://127.0.0.1:5000
Notes:
- The project uses a Hugging Face key from `.env`. It's preconfigured for convenience.
- Defaults to SQLite; to use MySQL set DATABASE_URL in `.env` and install driver.
