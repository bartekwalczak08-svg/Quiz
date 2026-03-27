import json
import csv
import sqlite3
from typing import Dict

def load_topics_from_json(file_path: str) -> Dict:
    """Wczytuje tematy quizu z pliku JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        topics = json.load(f)
    return topics


def export_questions_to_csv(db_path: str, output_path: str):
    """Eksportuje pytania z bazy SQLite do CSV"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question_id, topic, difficulty, question_text, created_at 
        FROM questions
    """)
    rows = cursor.fetchall()
    headers = ['question_id', 'topic', 'difficulty', 'question_text', 'created_at']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    conn.close()
    print(f"✅ Wyeksportowano {len(rows)} pytań do {output_path}")
