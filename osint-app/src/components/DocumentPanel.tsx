import { useState, useEffect } from "react";
import { FileText, Upload, Trash2, Eye, Calendar, File, Globe, Loader2, AlertCircle, CheckCircle, Clock, FolderKanban, RefreshCw, Play, PlayCircle } from "lucide-react";
import api, { Project, Document as ApiDocument } from "../services/api";

interface DocumentPanelProps {
  currentProject: Project;
}

const fileTypeIcons: Record<string, React.ReactNode> = {
  html: <FileText className="w-5 h-5 text-orange-400" />,
  pdf: <FileText className="w-5 h-5 text-red-400" />,
  txt: <File className="w-5 h-5 text-slate-400" />,
  web: <Globe className="w-5 h-5 text-blue-400" />,
};

const statusConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  pending: { 
    icon: <Clock className="w-3 h-3" />, 
    color: "bg-slate-500/20 text-slate-400", 
    label: "PENDING" 
  },
  processing: { 
    icon: <RefreshCw className="w-3 h-3 animate-spin" />, 
    color: "bg-yellow-500/20 text-yellow-400", 
    label: "PROCESSING" 
  },
  completed: { 
    icon: <CheckCircle className="w-3 h-3" />, 
    color: "bg-green-500/20 text-green-400", 
    label: "COMPLETED" 
  },
  error: { 
    icon: <AlertCircle className="w-3 h-3" />, 
    color: "bg-red-500/20 text-red-400", 
    label: "ERROR" 
  },
};

function extractDomain(url: string): string {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { 
      month: "short", 
      day: "numeric",
      year: "numeric"
    });
  } catch {
    return dateStr;
  }
}

export default function DocumentPanel({ currentProject }: DocumentPanelProps) {
  const [documents, setDocuments] = useState<ApiDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [processingDocId, setProcessingDocId] = useState<number | null>(null);
  const [processingAll, setProcessingAll] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, [currentProject.id]);

  // Auto-refresh documents every 5 seconds to catch updates from search
  useEffect(() => {
    const interval = setInterval(() => {
      if (!processingDocId) {
        fetchDocuments();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [currentProject.id, processingDocId]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const projectDetails = await api.getProject(currentProject.id);
      setDocuments(projectDetails.documents || []);
    } catch (err) {
      setError("Failed to fetch documents");
      console.error("Error fetching documents:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    // TODO: Handle file upload
  };

  const handleRemoveDocument = async (docId: number) => {
    if (!confirm("Are you sure you want to remove this document? This will also delete all associated entities.")) {
      return;
    }

    try {
      await api.removeDocumentWithCascade(currentProject.id, docId);
      fetchDocuments();
    } catch (err) {
      console.error("Error removing document:", err);
    }
  };

  const handleProcessAll = async () => {
    const pendingIds = documents
      .filter((d) => d.status === "pending" || d.status === "error")
      .map((d) => d.id);
    if (pendingIds.length === 0) return;
    setProcessingAll(true);
    try {
      await api.batchProcessDocuments(pendingIds, { nerEnabled: true, extractRelationships: true });
      await fetchDocuments();
    } catch (err) {
      console.error("Error processing documents:", err);
      alert(`Failed to process documents: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setProcessingAll(false);
    }
  };

  const handleProcessDocument = async (docId: number) => {
    setProcessingDocId(docId);
    try {
      const result = await api.processDocument(docId, { nerEnabled: true, extractRelationships: true });
      if (!result.success) {
        throw new Error(result.message);
      }
      await fetchDocuments();
    } catch (err) {
      console.error("Error processing document:", err);
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      alert(`Failed to process document: ${errorMessage}`);
    } finally {
      setProcessingDocId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-slate-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-500/10 border border-red-500/30 rounded-sm p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <div>
            <p className="text-red-400 font-medium">{error}</p>
            <button 
              onClick={fetchDocuments}
              className="text-sm text-red-400/70 hover:text-red-400 mt-1"
            >
              Click to retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Project Header */}
      <div className="mb-6 pb-4 border-b border-slate-700">
        <div className="flex items-center gap-2 mb-2">
          <FolderKanban className="w-5 h-5 text-blue-400" />
          <span className="text-sm text-slate-400">Project:</span>
          <span className="text-lg font-semibold text-slate-200">{currentProject.name}</span>
        </div>
        <p className="text-sm text-slate-500">
          {documents.length} document{documents.length !== 1 ? 's' : ''} in this project
        </p>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <FileText className="w-6 h-6" />
            Documents
          </h2>
          <p className="text-slate-400">
            View and manage documents in this project
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchDocuments}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded-sm transition-colors text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {documents.some((d) => d.status === "pending" || d.status === "error") && (
            <button
              onClick={handleProcessAll}
              disabled={processingAll}
              className="flex items-center gap-2 px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-400 disabled:opacity-50 rounded-sm transition-colors text-sm font-medium"
            >
              {processingAll ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <PlayCircle className="w-4 h-4" />
              )}
              Process All
            </button>
          )}
          <button className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-sm transition-colors text-sm">
            <Upload className="w-4 h-4" />
            Upload Files
          </button>
        </div>
      </div>

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-sm p-8 mb-6 text-center transition-colors ${
          isDragging
            ? "border-blue-500 bg-blue-500/10"
            : "border-slate-700 hover:border-slate-600"
        }`}
      >
        <Upload className="w-10 h-10 text-slate-500 mx-auto mb-3" />
        <p className="text-slate-400 mb-1">Drag and drop files here</p>
        <p className="text-sm text-slate-500">or click to browse</p>
      </div>

      {/* Documents List */}
      <div className="space-y-2">
        {documents.length > 0 ? (
          documents.map((doc) => {
            const domain = extractDomain(doc.file_path);
            return (
              <div
                key={doc.id}
                className="flex items-center gap-4 p-4 bg-slate-800 border border-slate-700 rounded-sm hover:border-slate-600 transition-colors"
              >
                <div className="flex-shrink-0">
                  {fileTypeIcons[doc.doc_type || 'txt'] || fileTypeIcons.txt}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-slate-200 truncate">
                      {doc.filename}
                    </h3>
                    {(() => {
                      const config = statusConfig[doc.status] || statusConfig.pending;
                      return (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-medium ${config.color}`}>
                          {config.icon}
                          {config.label}
                        </span>
                      );
                    })()}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-slate-500">
                    {domain && (
                      <span className="flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        {domain}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(doc.processed_at)}
                    </span>
                    {doc.entity_count > 0 && (
                      <span className="text-xs text-slate-400">
                        {doc.entity_count} entities
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Process button for pending documents */}
                  {(doc.status === 'pending' || doc.status === 'error') && (
                    <button
                      onClick={() => handleProcessDocument(doc.id)}
                      disabled={processingDocId === doc.id}
                      className="flex items-center gap-1 px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-400 disabled:opacity-50 rounded-sm text-xs font-medium transition-colors"
                    >
                      {processingDocId === doc.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Play className="w-3.5 h-3.5" />
                      )}
                      Process
                    </button>
                  )}
                  
                  <button className="p-2 hover:bg-slate-700 rounded-sm transition-colors">
                    <Eye className="w-4 h-4 text-slate-400" />
                  </button>
                  <button 
                    onClick={() => handleRemoveDocument(doc.id)}
                    className="p-2 hover:bg-red-500/20 rounded-sm transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-slate-400 hover:text-red-400" />
                  </button>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-400 mb-2">No documents yet</h3>
            <p className="text-sm text-slate-500 mb-4">
              This project doesn't have any documents yet
            </p>
            <p className="text-sm text-slate-600">
              Go to Search to add documents from web results
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
