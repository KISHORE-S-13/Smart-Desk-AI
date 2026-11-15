from flask import Blueprint, request, jsonify
from models import KnowledgeArticle
from services.auth_service import token_required
from services.knowledge_service import ingest_pdf_file

knowledge_bp = Blueprint("knowledge", __name__)

@knowledge_bp.route("/knowledge/articles", methods=["GET"])
@token_required()
def list_knowledge_articles(current_user):
    category = request.args.get("category")
    query = KnowledgeArticle.query
    if category:
        query = query.filter_by(category=category)
    
    articles = query.order_by(KnowledgeArticle.created_at.desc()).all()
    return jsonify({
        "total": len(articles),
        "articles": [a.to_dict() for a in articles]
    }), 200


@knowledge_bp.route("/knowledge/upload", methods=["POST"])
@token_required(required_role="admin")
def upload_knowledge_pdf(current_user):
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only .pdf files are supported"}), 400

    article, err = ingest_pdf_file(file)
    if err:
        return jsonify({"error": f"Failed to ingest PDF: {err}"}), 500

    return jsonify({
        "message": "Knowledge document successfully ingested and indexed",
        "article": article.to_dict()
    }), 201
