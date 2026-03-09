import { useState, useMemo } from "react";
import {
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  Trash2,
  Play,
  Loader2,
  AlertTriangle,
  CheckSquare,
  Square,
  Filter,
  X,
  Globe,
  Calendar,
  RefreshCw
} from "lucide-react";
import api, { DocumentProcessOptions } from "../services/api";

export interface ProjectDocument {
  id: number;
  filename: string;
  filePath: string;
  fileHash: string | null;
  docType: string | null;
  processedAt: string;
  entityCount: number;
  status: "pending" | "processing" | "completed" | "error";
  domain?: string;
}

interface ProjectDocumentManagerProps {
  projectId: number;
  documents: ProjectDocument[];
  onDocumentsChange: () => void;
}

type StatusFilter = "all" | "pending" | "completed" | "error";

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

export default function ProjectDocumentManager({
  projectId,
  documents,
  onDocumentsChange,
}: ProjectDocumentManagerProps) {
  const [selectedDocs, setSelectedDocs] = useState<Set<number>>(new Set());
  const [processingDoc, setProcessingDoc] = useState<number | null>(null);
  const [batchProcessing, setBatchProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState({ current: 0, total: 0 });
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  // Filter documents based on status
  const filteredDocuments = useMemo(() => {
    if (statusFilter === "all") return documents;
    return documents.filter(doc => doc.status === statusFilter);
  }, [documents, statusFilter]);

  const allSelected = filteredDocuments.length > 0 && 
    filteredDocuments.every(doc => selectedDocs.has(doc.id));
  const someSelected = selectedDocs.size > 0 && !allSelected;

  const stats = useMemo(() => ({
    total: documents.length,
    pending: documents.filter(d => d.status === "pending").length,
    completed: documents.filter(d => d.status === "completed").length,
    error: documents.filter(d => d.status === "error").length,
  }), [documents]);

  const toggleSelectAll = () => {
    if (allSelected) {
      // Deselect only filtered docs
      const newSelected = new Set(selectedDocs);
      filteredDocuments.forEach(doc => newSelected.delete(doc.id));
      setSelectedDocs(newSelected);
    } else {
      // Select all filtered docs
      const newSelected = new Set(selectedDocs);
      filteredDocuments.forEach(doc => newSelected.add(doc.id));
      setSelectedDocs(newSelected);
    }
  };

  const toggleSelectDoc = (docId: number) => {
    const newSelected = new Set(selectedDocs);
    if (newSelected.has(docId)) {
      newSelected.delete(docId);
    } else {
      newSelected.add(docId);
    }
    setSelectedDocs(newSelected);
  };

  const handleProcessSingle = async (docId: number) => {
    setProcessingDoc(docId);
    setError(null);

    const options: DocumentProcessOptions = {
      nerEnabled: true,
      extractRelationships: true,
    };

    try {
      const result = await api.processDocument(docId, options);
      
      if (result.success) {
        onDocumentsChange();
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError("Failed to process document");
      console.error("Error processing document:", err);
    } finally {
      setProcessingDoc(null);
    }
  };

  const handleProcessSelected = async () => {
    const pendingSelected = Array.from(selectedDocs).filter(docId => {
      const doc = documents.find(d => d.id === docId);
      return doc?.status === "pending";
    });

    if (pendingSelected.length === 0) {
      setError("No pending documents selected");
      return;
    }

    setBatchProcessing(true);
    setProcessingProgress({ current: 0, total: pendingSelected.length });
    setError(null);

    const options: DocumentProcessOptions = {
      nerEnabled: true,
      extractRelationships: true,
    };

    try {
      // Process one by one to show progress
      for (let i = 0; i < pendingSelected.length; i++) {
        setProcessingProgress({ current: i, total: pendingSelected.length });
        await api.processDocument(pendingSelected[i], options);
      }
      
      setSelectedDocs(new Set());
      onDocumentsChange();
    } catch (err) {
      setError("Failed to process documents");
      console.error("Error processing documents:", err);
    } finally {
      setBatchProcessing(false);
      setProcessingProgress({ current: 0, total: 0 });
    }
  };

  const handleRemoveSelected = async () => {
    if (selectedDocs.size === 0) return;

    setRemoving(true);
    setError(null);

    try {
      const docIds = Array.from(selectedDocs);
      
      for (const docId of docIds) {
        await api.removeDocumentWithCascade(projectId, docId);
      }

      setSelectedDocs(new Set());
      setShowRemoveConfirm(false);
      onDocumentsChange();
    } catch (err) {
      setError("Failed to remove documents");
      console.error("Error removing documents:", err);
    } finally {
      setRemoving(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-sm font-medium">
            <CheckCircle className="w-3 h-3" />
            COMPLETED
          </span>
        );
      case "processing":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded-sm font-medium">
            <RefreshCw className="w-3 h-3 animate-spin" />
            PROCESSING
          </span>
        );
      case "error":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-sm font-medium">
            <AlertCircle className="w-3 h-3" />
            ERROR
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-500/20 text-slate-400 text-xs rounded-sm font-medium">
            <Clock className="w-3 h-3" />
            PENDING
          </span>
        );
    }
  };

  const FilterButton = ({ filter, label, count }: { filter: StatusFilter; label: string; count: number }) => (
    <button
      onClick={() => {
        setStatusFilter(filter);
        setSelectedDocs(new Set());
      }}
      className={`px-3 py-1.5 rounded-sm text-xs font-medium transition-colors ${
        statusFilter === filter
          ? "bg-slate-600 text-slate-200"
          : "bg-slate-800 text-slate-400 hover:bg-slate-700"
      }`}
    >
      {label}
      <span className="ml-1.5 font-mono text-slate-500">{count}</span>
    </button>
  );

  return (
    <div className="space-y-4">
      {/* Status Filter Buttons */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-slate-500 mr-1" />
        <FilterButton filter="all" label="All" count={stats.total} />
        <FilterButton filter="pending" label="Pending" count={stats.pending} />
        <FilterButton filter="completed" label="Completed" count={stats.completed} />
        <FilterButton filter="error" label="Error" count={stats.error} />
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 bg-slate-800/50 border border-slate-700 rounded-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSelectAll}
            className="flex items-center gap-2 text-sm text-slate-300 hover:text-slate-200"
          >
            {allSelected ? (
              <CheckSquare className="w-4 h-4 text-slate-400" />
            ) : someSelected ? (
              <div className="w-4 h-4 border-2 border-slate-400 bg-slate-400 rounded-sm" />
            ) : (
              <Square className="w-4 h-4 text-slate-500" />
            )}
            <span className="font-mono text-xs">
              {selectedDocs.size > 0 ? `${selectedDocs.size} selected` : "Select All"}
            </span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {selectedDocs.size > 0 && (
            <>
              <button
                onClick={() => setSelectedDocs(new Set())}
                className="flex items-center gap-1.5 px-3 py-1.5 text-slate-400 hover:text-slate-300 rounded-sm text-sm transition-colors"
              >
                <X className="w-3.5 h-3.5" />
                Clear
              </button>

              <button
                onClick={handleProcessSelected}
                disabled={batchProcessing}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-400 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm text-sm font-medium transition-colors"
              >
                {batchProcessing ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5" />
                )}
                Process Selected
              </button>

              <button
                onClick={() => setShowRemoveConfirm(true)}
                disabled={removing}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm text-sm font-medium transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Remove
              </button>
            </>
          )}
        </div>
      </div>

      {/* Processing Progress */}
      {batchProcessing && (
        <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-sm">
          <div className="flex items-center gap-3">
            <Loader2 className="w-4 h-4 animate-spin text-yellow-400" />
            <span className="text-sm text-yellow-400">
              Processing documents... {processingProgress.current} of {processingProgress.total}
            </span>
          </div>
          <div className="mt-2 h-1 bg-slate-700 rounded-sm overflow-hidden">
            <div
              className="h-full bg-yellow-500 transition-all duration-300"
              style={{
                width: `${processingProgress.total > 0 ? (processingProgress.current / processingProgress.total) * 100 : 0}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span className="text-sm text-red-400">{error}</span>
        </div>
      )}

      {/* Documents List */}
      <div className="border border-slate-700 rounded-sm overflow-hidden">
        {filteredDocuments.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">
              {statusFilter === "all" 
                ? "No documents in this project" 
                : `No ${statusFilter} documents`}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className={`p-4 hover:bg-slate-800/50 transition-colors ${
                  selectedDocs.has(doc.id) ? "bg-slate-800/80" : ""
                }`}
              >
                <div className="flex items-start gap-3">
                  {/* Checkbox */}
                  <button
                    onClick={() => toggleSelectDoc(doc.id)}
                    className="flex-shrink-0 mt-0.5"
                  >
                    {selectedDocs.has(doc.id) ? (
                      <CheckSquare className="w-4 h-4 text-slate-400" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-600" />
                    )}
                  </button>

                  {/* Document Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        {/* Title and Status */}
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="text-sm font-medium text-slate-200 truncate">
                            {doc.filename}
                          </h4>
                          {getStatusBadge(doc.status)}
                        </div>

                        {/* Metadata */}
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          {doc.domain && (
                            <span className="flex items-center gap-1">
                              <Globe className="w-3 h-3" />
                              {doc.domain}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {formatDate(doc.processedAt)}
                          </span>
                          <span className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            {doc.docType || "Unknown"}
                          </span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        {/* Entity Count */}
                        <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800 rounded-sm">
                          <span className="text-xs font-semibold text-slate-400 font-mono">
                            {doc.entityCount}
                          </span>
                          <span className="text-xs text-slate-500">entities</span>
                        </div>

                        {/* Process Button (for pending) */}
                        {doc.status === "pending" && (
                          <button
                            onClick={() => handleProcessSingle(doc.id)}
                            disabled={processingDoc === doc.id}
                            className="flex items-center gap-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded-sm text-xs transition-colors"
                          >
                            {processingDoc === doc.id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                            Process
                          </button>
                        )}

                        {/* Remove Button */}
                        <button
                          onClick={() => {
                            setSelectedDocs(new Set([doc.id]));
                            setShowRemoveConfirm(true);
                          }}
                          className="p-1.5 hover:bg-red-500/20 rounded-sm text-slate-500 hover:text-red-400 transition-colors"
                          title="Remove document"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Remove Confirmation Dialog */}
      {showRemoveConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-sm p-5 w-full max-w-md">
            <div className="flex items-start gap-3 mb-4">
              <div className="p-2 bg-red-500/20 rounded-sm">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Remove Documents?</h3>
                <p className="text-sm text-slate-400 mt-1">
                  You are about to remove {selectedDocs.size} document
                  {selectedDocs.size !== 1 ? "s" : ""} from this project.
                </p>
              </div>
            </div>

            <div className="bg-red-500/10 border border-red-500/30 rounded-sm p-3 mb-4">
              <p className="text-sm text-red-400">
                <strong>Warning:</strong> This will permanently delete the documents and all
                associated entities ({Array.from(selectedDocs).reduce((sum, docId) => {
                  const doc = documents.find((d) => d.id === docId);
                  return sum + (doc?.entityCount || 0);
                }, 0)} entities total). This action cannot be undone.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleRemoveSelected}
                disabled={removing}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-700 disabled:text-slate-500 rounded-sm font-medium text-sm transition-colors"
              >
                {removing ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Removing...
                  </span>
                ) : (
                  "Remove Documents"
                )}
              </button>
              <button
                onClick={() => {
                  setShowRemoveConfirm(false);
                  if (selectedDocs.size === 1) {
                    setSelectedDocs(new Set());
                  }
                }}
                disabled={removing}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-sm font-medium text-sm transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
