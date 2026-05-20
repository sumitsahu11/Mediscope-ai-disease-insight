from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from fetcher import fetch_nhs_disease_article
from summarizer import summarize_text
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="/")
CORS(app)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/disease-summary", methods=["POST"])
def disease_summary():
    data = request.get_json() or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Please enter a disease name to search."}), 400

    if len(query) < 2:
        return jsonify({"error": "Search term is too short. Please enter a disease name."}), 400

    article_text, article_url = fetch_nhs_disease_article(query)

    if not article_text:
        return jsonify({
            "error": (
                f"Could not find NHS information for '{query}'. "
                "Try checking the spelling or using the full disease name "
                "(e.g. 'type 2 diabetes' instead of 'diabetes type 2')."
            )
        }), 404

    summary = summarize_text(article_text)

    return jsonify({
        "query": query,
        "summary": summary,
        "source_url": article_url,
        "source_name": "NHS",
        "attribution": (
            "Content adapted from the NHS website "
            "under the Open Government Licence v3.0."
        ),
    })


if __name__ == "__main__":
    print()
    print("  ╔═══════════════════════════════════════╗")
    print("  ║   Disease Info Finder — NHS + Flask   ║")
    print("  ║   http://localhost:5000               ║")
    print("  ╚═══════════════════════════════════════╝")
    print()
    app.run(debug=True, host="0.0.0.0", port=5000)
