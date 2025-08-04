from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import tempfile
import traceback
import ollama
import json

app = Flask(__name__)
CORS(app)  # 🔥 FIXED: Removed extra indentation here

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({"error": "No resume uploaded"}), 400

        file = request.files['resume']

        # Extract text (only first 2 pages for faster processing)
        if file.filename.endswith('.pdf'):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                file.save(tmp.name)
                with pdfplumber.open(tmp.name) as pdf:
                    text = "\n".join([page.extract_text() or '' for page in pdf.pages[:2]])
        else:
            text = file.read().decode('utf-8', errors='ignore')

        prompt = f"""
You are a professional resume reviewer. Analyze the following resume and return scores in valid JSON.

Resume:
{text}

Return only JSON in this format:
{{
  "Objective": 0-100,
  "Experience": 0-100,
  "Projects": 0-100,
  "Skills": 0-100,
  "Education": 0-100,
  "Certifications": 0-100,
  "Overall": 0-100,
  "Suggestions": {{
    "Objective": "...",
    "Experience": "...",
    "Projects": "...",
    "Skills": "...",
    "Education": "...",
    "Certifications": "..."
  }}
}}
"""

        # Use a faster model (e.g., mistral)
        response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
        content = response["message"]["content"]

        # Extract only the JSON part (in case LLM adds extra text)
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        json_str = content[json_start:json_end]

        result = json.loads(json_str)

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to analyze resume", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001, debug=True)
