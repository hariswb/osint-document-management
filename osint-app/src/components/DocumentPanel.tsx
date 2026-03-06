import { useState } from "react";
import { FileText, Upload, Trash2, Eye, Calendar, File } from "lucide-react";

interface Document {
  id: number;
  filename: string;
  file_path: string;
  file_hash: string;
  doc_type: string;
  processed_at: string;
  entity_count: number;
}

const mockDocuments: Document[] = [
  {
    id: 1,
    filename: "article_prabowo.html",
    file_path: "data/scraped/article_prabowo.html",
    file_hash: "abc123...",
    doc_type: "html",
    processed_at: "2026-03-06 14:30",
    entity_count: 45,
  },
  {
    id: 2,
    filename: "report_indonesia.pdf",
    file_path: "data/uploads/report_indonesia.pdf",
    file_hash: "def456...",
    doc_type: "pdf",
    processed_at: "2026-03-06 12:15",
    entity_count: 28,
  },
];

const fileTypeIcons: Record<string, React.ReactNode> = {
  html: <FileText className="w-5 h-5 text-orange-400" />,
  pdf: <FileText className="w-5 h-5 text-red-400" />,
  txt: <File className="w-5 h-5 text-gray-400" />,
};

export default function DocumentPanel() {
  const [documents] = useState<Document[]>(mockDocuments);
  const [isDragging, setIsDragging] = useState(false);

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
    // Handle file upload
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <FileText className="w-6 h-6" />
            Documents
          </h2>
          <p className="text-gray-400">
            Upload and manage documents for entity extraction
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg font-medium transition-colors">
          <Upload className="w-4 h-4" />
          Upload File
        </button>
      </div>

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 mb-6 text-center transition-colors ${
          isDragging
            ? "border-primary-500 bg-primary-500/10"
            : "border-gray-700 hover:border-gray-600"
        }`}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-500" />
        <p className="text-lg font-medium mb-2">Drop files here</p>
        <p className="text-sm text-gray-500">
          or click the Upload button to select files
        </p>
        <p className="text-xs text-gray-600 mt-2">
          Supports: PDF, HTML, TXT (max 50MB)
        </p>
      </div>

      {/* Document List */}
      <div className="space-y-3">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-primary-500/50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gray-700 rounded-lg flex items-center justify-center">
                  {fileTypeIcons[doc.doc_type] || <File className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="font-medium">{doc.filename}</h3>
                  <p className="text-sm text-gray-500">{doc.file_path}</p>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-xs text-gray-600 flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {doc.processed_at}
                    </span>
                    <span className="text-xs text-primary-400">
                      {doc.entity_count} entities extracted
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
                  <Eye className="w-4 h-4" />
                </button>
                <button className="p-2 hover:bg-red-500/20 hover:text-red-400 rounded-lg transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {documents.length === 0 && (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <p className="text-gray-500">No documents yet</p>
          <p className="text-sm text-gray-600 mt-1">
            Upload a document to start extracting entities
          </p>
        </div>
      )}
    </div>
  );
}
