import React, { useState, useEffect } from "react";
import { knowledgeApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import {
  BookOpen,
  UploadCloud,
  FileText,
  Search,
  CheckCircle,
  Tag,
  AlertCircle,
  RefreshCw,
  ExternalLink
} from "lucide-react";

export default function KnowledgeView({ onOpenChatbot }) {
  const { isAdmin } = useAuth();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [uploadError, setUploadError] = useState("");

  const categories = ["All", "VPN", "Wi-Fi", "Password Reset", "Email", "Software Installation", "General"];

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const res = await knowledgeApi.list(selectedCategory === "All" ? null : selectedCategory);
      setArticles(res.data.articles || []);
    } catch {
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, [selectedCategory]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadMsg("");
    setUploadError("");

    const formData = new FormData();
    formData.append("file", uploadFile);

    try {
      const res = await knowledgeApi.upload(formData);
      setUploadMsg(`Document '${uploadFile.name}' ingested successfully!`);
      setUploadFile(null);
      fetchArticles();
    } catch (err) {
      setUploadError(err.response?.data?.error || "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  };

  const filteredArticles = articles.filter((a) => {
    if (!search.trim()) return true;
    const term = search.toLowerCase();
    return (
      a.title.toLowerCase().includes(term) ||
      a.category.toLowerCase().includes(term) ||
      a.content.toLowerCase().includes(term)
    );
  });

  return (
    <div className="knowledge-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Enterprise Knowledge Repository & RAG</h1>
          <p className="view-subtitle">
            Verified corporate IT policies, standard operating procedures, and automated self-help guides
          </p>
        </div>
        <button className="btn-secondary" onClick={onOpenChatbot}>
          <BookOpen size={16} /> Open AI Knowledge Copilot
        </button>
      </div>

      {/* Admin PDF Upload Section */}
      {isAdmin && (
        <div className="analytics-card pdf-upload-card">
          <div className="card-header-clean">
            <div className="card-title-wrap">
              <UploadCloud size={18} className="text-primary" />
              <h3>Ingest Policy / SOP Document (PyPDF)</h3>
            </div>
            <span className="header-hint">Uploads are parsed and added to the RAG knowledge index</span>
          </div>

          <form onSubmit={handleUpload} className="pdf-upload-form">
            <div className="upload-input-wrap">
              <input
                type="file"
                accept=".pdf"
                id="pdf-file-input"
                className="file-hidden-input"
                onChange={(e) => setUploadFile(e.target.files[0])}
              />
              <label htmlFor="pdf-file-input" className="file-upload-label">
                <FileText size={18} />
                <span>{uploadFile ? uploadFile.name : "Select enterprise PDF document (.pdf)..."}</span>
              </label>
            </div>
            <button
              type="submit"
              className="btn-primary"
              disabled={!uploadFile || uploading}
            >
              {uploading ? "Ingesting PDF..." : "Ingest Document"}
            </button>
          </form>

          {uploadMsg && <div className="alert-banner alert-success mt-3">{uploadMsg}</div>}
          {uploadError && <div className="alert-banner alert-error mt-3">{uploadError}</div>}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="table-filter-bar">
        <div className="search-form">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search knowledge documents by keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="category-pill-selector">
          {categories.map((cat) => (
            <button
              key={cat}
              className={`cat-pill ${selectedCategory === cat ? "active" : ""}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Articles Grid */}
      {loading ? (
        <div className="dashboard-loading-state">
          <RefreshCw className="spin-icon" size={20} />
          <p>Loading knowledge articles...</p>
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="empty-state-card">
          <BookOpen size={32} className="text-slate-400" />
          <h4>No Articles Found</h4>
          <p>No knowledge base articles match your filter.</p>
        </div>
      ) : (
        <div className="articles-grid">
          {filteredArticles.map((art) => (
            <div key={art.id} className="article-card">
              <div className="article-card-header">
                <span className="cat-chip">{art.category}</span>
                <span className="article-source-tag">
                  {art.source === "uploaded_pdf" ? "PDF Ingestion" : "System SOP"}
                </span>
              </div>
              <h3 className="article-title">{art.title}</h3>
              <div className="article-content-preview">
                {art.content}
              </div>
              {art.tags && art.tags.length > 0 && (
                <div className="article-tags-row">
                  {art.tags.map((t, idx) => (
                    <span key={idx} className="article-tag">#{t}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
