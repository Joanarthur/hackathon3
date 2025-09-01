from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import List, Dict, Optional
import os
import requests

# Flask app
app: Flask = Flask(__name__, static_folder='../static', template_folder='../templates')

# Use DATABASE_URL from environment or default to SQLite
DATABASE_URL: str = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), '../flashcards.db')}")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db: SQLAlchemy = SQLAlchemy(app)

class Flashcard(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    question: str = db.Column(db.Text, nullable=False)
    answer: str = db.Column(db.Text, nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, str]:
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at.isoformat()
        }

# Ensure tables exist
with app.app_context():
    db.create_all()

def local_fallback_generator(text: str) -> List[Dict[str, str]]:
    import re
    sentences: List[str] = re.split(r'[\n\.?]+', text.strip())
    qa: List[Dict[str, str]] = []
    for s in sentences:
        s = s.strip()
        if len(s) < 20:
            continue
        if ' is ' in s.lower():
            parts: List[str] = s.split(' is ', 1)
            q: str = f"What is {parts[0].strip()}?"
            a: str = parts[1].strip()
        else:
            q = f"Explain: {s[:60]}..."
            a = s
        qa.append({'question': q, 'answer': a})
        if len(qa) >= 12:
            break
    if not qa:
        qa = [{'question': 'What is this note about?', 'answer': text[:300]}]
    return qa

def hf_generate_qa(text: str, hf_api_key: Optional[str] = None) -> List[Dict[str, str]]:
    if not hf_api_key:
        return local_fallback_generator(text)
    headers: Dict[str, str] = {"Authorization": f"Bearer {hf_api_key}", "Accept": "application/json"}
    payload: Dict[str, str] = {"inputs": text}
    try:
        resp = requests.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
            headers=headers,
            json=payload,
            timeout=30
        )
        if resp.ok:
            data = resp.json()
            if isinstance(data, list) and 'summary_text' in data[0]:
                summary: str = data[0]['summary_text']
                return local_fallback_generator(summary)
        return local_fallback_generator(text)
    except Exception:
        return local_fallback_generator(text)

@app.route('/')
def index() -> str:
    cards: List[Flashcard] = Flashcard.query.order_by(Flashcard.created_at.desc()).limit(50).all()
    return render_template('index.html', cards=[c.to_dict() for c in cards])

@app.route('/generate', methods=['POST'])
def generate() -> jsonify:
    notes: str = request.json.get('notes','').strip()
    if not notes:
        return jsonify({'error':'No notes provided'}), 400
    hf_key: Optional[str] = os.getenv('HUGGINGFACE_API_KEY')
    qa: List[Dict[str, str]] = hf_generate_qa(notes, hf_key)
    return jsonify({'qa': qa})

@app.route('/save', methods=['POST'])
def save() -> jsonify:
    qa: List[Dict[str, str]] = request.json.get('qa', [])
    saved: List[Flashcard] = []
    for item in qa:
        q: str = (item.get('question') or '').strip()
        a: str = (item.get('answer') or '').strip()
        if not q or not a:
            continue
        card: Flashcard = Flashcard(question=q, answer=a)
        db.session.add(card)
        saved.append(card)
    db.session.commit()
    return jsonify({'saved':[c.to_dict() for c in saved]})

@app.route('/api/cards')
def api_cards() -> jsonify:
    cards: List[Flashcard] = Flashcard.query.order_by(Flashcard.created_at.desc()).all()
    return jsonify({'cards':[c.to_dict() for c in cards]})

# For Vercel serverless
app = app  # Vercel looks for an "app" object

