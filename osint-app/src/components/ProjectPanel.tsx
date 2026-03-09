import { useState } from "react";
import { 
  FolderKanban, 
  Plus, 
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  X,
  Edit2,
  Trash2,
  ChevronRight,
  ChevronDown,
  Play,
  Globe,
  Calendar,
  Check,
  Loader2 as Loader,
  RefreshCw
} from "lucide-react";
import api, { Project, Document, Entity } from "../services/api";
import ProjectDocumentManager, { ProjectDocument } from "./ProjectDocumentManager";

interface ProjectPanelProps {
  projects: Project[];
  currentProject: Project | null;
  onProjectSelect: (project: Project | null) => void;
  onProjectsChanged: () => void;
}

interface ProjectWithDetails extends Project {
  documents?: Document[];
  entities?: Entity[];
}

type DocumentStatus = "pending" | "processing" | "completed" | "error";

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

export default function ProjectPanel({ 
  projects, 
  currentProject, 
  onProjectSelect, 
  onProjectsChanged 
}: ProjectPanelProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [newProject, setNewProject] = useState({ name: "", description: "" });
  const [expandedProject, setExpandedProject] = useState<number | null>(null);
  const [projectDetails, setProjectDetails] = useState<Map<number, ProjectWithDetails>>(new Map());
  const [processingDoc, setProcessingDoc] = useState<number | null>(null);
  const [batchProcessing, setBatchProcessing] = useState<number | null>(null);

  const fetchProjectDetails = async (projectId: number) => {
    try {
      const details = await api.getProject(projectId);
      setProjectDetails((prev) => new Map(prev.set(projectId, details)));
    } catch (err) {
      console.error("Error fetching project details:", err);
    }
  };

  const toggleProjectExpand = async (projectId: number) => {
    if (expandedProject === projectId) {
      setExpandedProject(null);
    } else {
      setExpandedProject(projectId);
      if (!projectDetails.has(projectId)) {
        await fetchProjectDetails(projectId);
      }
    }
  };

  const convertToProjectDocuments = (docs: Document[], entities: Entity[]): ProjectDocument[] => {
    return docs.map((doc) => {
      const entityCount = entities.filter((e) => e.source_doc_id === doc.id).length;
      const status: DocumentStatus = entityCount > 0 ? "completed" : "pending";
      
      return {
        id: doc.id,
        filename: doc.filename,
        filePath: doc.file_path,
        fileHash: doc.file_hash,
        docType: doc.doc_type,
        processedAt: doc.processed_at,
        entityCount,
        status,
        domain: extractDomain(doc.file_path),
      };
    });
  };

  const handleProcessDocument = async (docId: number, projectId: number) => {
    setProcessingDoc(docId);
    try {
      await api.processDocument(docId, { nerEnabled: true, extractRelationships: true });
      await fetchProjectDetails(projectId);
    } catch (err) {
      console.error("Error processing document:", err);
    } finally {
      setProcessingDoc(null);
    }
  };

  const handleProcessAllPending = async (projectId: number) => {
    const details = projectDetails.get(projectId);
    if (!details?.documents) return;

    const pendingDocs = details.documents.filter(doc => {
      const entityCount = details.entities?.filter(e => e.source_doc_id === doc.id).length || 0;
      return entityCount === 0;
    });

    if (pendingDocs.length === 0) return;

    setBatchProcessing(projectId);
    try {
      const docIds = pendingDocs.map(d => d.id);
      await api.batchProcessDocuments(docIds, { nerEnabled: true, extractRelationships: true });
      await fetchProjectDetails(projectId);
    } catch (err) {
      console.error("Error batch processing documents:", err);
    } finally {
      setBatchProcessing(null);
    }
  };

  const handleRemoveDocument = async (projectId: number, docId: number) => {
    if (!confirm("Are you sure you want to remove this document? This will also delete all associated entities. This action cannot be undone.")) {
      return;
    }

    try {
      await api.removeDocumentWithCascade(projectId, docId);
      await fetchProjectDetails(projectId);
    } catch (err) {
      console.error("Error removing document:", err);
    }
  };

  const handleCreateProject = async () => {
    if (!newProject.name.trim()) return;
    
    try {
      const created = await api.createProject(newProject.name, newProject.description);
      setNewProject({ name: "", description: "" });
      setIsCreating(false);
      onProjectsChanged();
      // Auto-select the new project
      onProjectSelect(created);
    } catch (err) {
      console.error("Error creating project:", err);
      alert("Failed to create project");
    }
  };

  const handleUpdateProject = async () => {
    if (!editingProject || !editingProject.name.trim()) return;
    
    try {
      await api.updateProject(editingProject.id, {
        name: editingProject.name,
        description: editingProject.description
      });
      setEditingProject(null);
      onProjectsChanged();
    } catch (err) {
      console.error("Error updating project:", err);
      alert("Failed to update project");
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    if (!confirm("Are you sure you want to delete this project? This action cannot be undone.")) {
      return;
    }
    
    try {
      await api.deleteProject(projectId);
      if (currentProject?.id === projectId) {
        onProjectSelect(null);
      }
      onProjectsChanged();
    } catch (err) {
      console.error("Error deleting project:", err);
      alert("Failed to delete project");
    }
  };



  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'active':
        return <Clock className="w-4 h-4 text-blue-400" />;
      case 'archived':
        return <AlertCircle className="w-4 h-4 text-slate-400" />;
      default:
        return <Clock className="w-4 h-4 text-blue-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400';
      case 'active':
        return 'bg-blue-500/20 text-blue-400';
      case 'archived':
        return 'bg-slate-500/20 text-slate-400';
      default:
        return 'bg-blue-500/20 text-blue-400';
    }
  };

  const getDocStatusBadge = (status: DocumentStatus) => {
    switch (status) {
      case "completed":
        return (
          <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-sm font-medium">
            COMPLETED
          </span>
        );
      case "processing":
        return (
          <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded-sm font-medium">
            PROCESSING
          </span>
        );
      case "error":
        return (
          <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-sm font-medium">
            ERROR
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 bg-slate-500/20 text-slate-400 text-xs rounded-sm font-medium">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <FolderKanban className="w-6 h-6" />
            Projects
          </h2>
          <p className="text-slate-400">
            Select a project as your workspace or create a new one
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={onProjectsChanged}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-sm transition-colors font-medium text-sm"
            title="Refresh projects list"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button 
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-sm transition-colors font-medium text-sm"
          >
            <Plus className="w-4 h-4" />
            New Project
          </button>
        </div>
      </div>



      {/* Create Project Modal */}
      {isCreating && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-sm p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Create New Project</h3>
              <button onClick={() => setIsCreating(false)} className="p-1 hover:bg-slate-700 rounded-sm">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Project Name *</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  placeholder="Enter project name..."
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-sm focus:outline-none focus:ring-2 focus:ring-slate-500 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Description</label>
                <textarea
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  placeholder="Enter project description..."
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-sm focus:outline-none focus:ring-2 focus:ring-slate-500 resize-none text-sm"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleCreateProject}
                  disabled={!newProject.name.trim()}
                  className="flex-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 rounded-sm font-medium text-sm transition-colors"
                >
                  Create Project
                </button>
                <button
                  onClick={() => setIsCreating(false)}
                  className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-sm font-medium text-sm transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Project Modal */}
      {editingProject && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-sm p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Edit Project</h3>
              <button onClick={() => setEditingProject(null)} className="p-1 hover:bg-slate-700 rounded-sm">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Project Name *</label>
                <input
                  type="text"
                  value={editingProject.name}
                  onChange={(e) => setEditingProject({ ...editingProject, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-sm focus:outline-none focus:ring-2 focus:ring-slate-500 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Description</label>
                <textarea
                  value={editingProject.description || ""}
                  onChange={(e) => setEditingProject({ ...editingProject, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-sm focus:outline-none focus:ring-2 focus:ring-slate-500 resize-none text-sm"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleUpdateProject}
                  disabled={!editingProject.name.trim()}
                  className="flex-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 rounded-sm font-medium text-sm transition-colors"
                >
                  Save Changes
                </button>
                <button
                  onClick={() => setEditingProject(null)}
                  className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-sm font-medium text-sm transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Projects Grid */}
      <div className="grid grid-cols-1 gap-3">
        {projects.map((project) => {
          const isExpanded = expandedProject === project.id;
          const isSelected = currentProject?.id === project.id;
          const details = projectDetails.get(project.id);
          const pendingCount = details?.documents?.filter(doc => {
            const entityCount = details.entities?.filter(e => e.source_doc_id === doc.id).length || 0;
            return entityCount === 0;
          }).length || 0;
          
          return (
            <div
              key={project.id}
              className={`bg-slate-800 border rounded-sm overflow-hidden transition-all ${
                isSelected 
                  ? "border-blue-500 ring-1 ring-blue-500/50" 
                  : "border-slate-700 hover:border-slate-500"
              }`}
            >
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`px-2 py-0.5 rounded-sm text-xs font-medium flex items-center gap-1.5 ${getStatusColor(project.status)}`}>
                        {getStatusIcon(project.status)}
                        {project.status.toUpperCase()}
                      </div>
                      {isSelected && (
                        <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-sm font-medium flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          CURRENT WORKSPACE
                        </span>
                      )}
                    </div>

                    <h3 className="font-semibold text-lg mb-1">{project.name}</h3>
                    {project.description && (
                      <p className="text-sm text-slate-400 mb-3">
                        {project.description}
                      </p>
                    )}

                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <FileText className="w-3.5 h-3.5" />
                        <span className="font-mono">{project.document_count || 0}</span>
                        <span>docs</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span className="font-mono">{details?.entities?.length || 0}</span>
                        <span>entities</span>
                      </div>
                      {pendingCount > 0 && (
                        <div className="flex items-center gap-1.5 text-yellow-500">
                          <Clock className="w-3.5 h-3.5" />
                          <span className="font-mono">{pendingCount}</span>
                          <span>pending</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {!isSelected ? (
                      <button
                        onClick={() => onProjectSelect(project)}
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-sm text-sm font-medium transition-colors"
                      >
                        Select
                      </button>
                    ) : (
                      <button
                        onClick={() => onProjectSelect(null)}
                        className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-sm text-sm font-medium transition-colors"
                      >
                        Deselect
                      </button>
                    )}
                    
                    <button
                      onClick={() => toggleProjectExpand(project.id)}
                      className={`p-1.5 hover:bg-slate-700 rounded-sm transition-colors ${isExpanded ? 'bg-slate-700' : ''}`}
                      title="View documents"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                    </button>
                    
                    <button
                      onClick={() => setEditingProject(project)}
                      className="p-1.5 hover:bg-slate-700 rounded-sm"
                    >
                      <Edit2 className="w-4 h-4 text-slate-400" />
                    </button>
                    
                    <button
                      onClick={() => handleDeleteProject(project.id)}
                      className="p-1.5 hover:bg-red-500/20 rounded-sm"
                    >
                      <Trash2 className="w-4 h-4 text-slate-400 hover:text-red-400" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Expanded Document Manager */}
              {isExpanded && details && (
                <div className="border-t border-slate-700 p-4 bg-slate-900/30">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      Documents
                    </h4>
                    {pendingCount > 0 && (
                      <button
                        onClick={() => handleProcessAllPending(project.id)}
                        disabled={batchProcessing === project.id}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-400 disabled:opacity-50 rounded-sm text-xs font-medium transition-colors"
                      >
                        {batchProcessing === project.id ? (
                          <Loader className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Play className="w-3.5 h-3.5" />
                        )}
                        Process All Pending ({pendingCount})
                      </button>
                    )}
                  </div>

                  {/* Documents List */}
                  <div className="space-y-2">
                    {details.documents && details.documents.length > 0 ? (
                      details.documents.map((doc) => {
                        const entityCount = details.entities?.filter(e => e.source_doc_id === doc.id).length || 0;
                        const status: DocumentStatus = entityCount > 0 ? "completed" : "pending";
                        const isProcessing = processingDoc === doc.id;
                        const domain = extractDomain(doc.file_path);
                        
                        return (
                          <div
                            key={doc.id}
                            className="flex items-center gap-3 p-3 bg-slate-800/50 border border-slate-700 rounded-sm"
                          >
                            <div className="flex-shrink-0">
                              {getDocStatusBadge(status)}
                            </div>
                            
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-200 truncate">
                                {doc.filename}
                              </p>
                              <div className="flex items-center gap-2 mt-1">
                                {domain && (
                                  <span className="flex items-center gap-1 text-xs text-slate-500">
                                    <Globe className="w-3 h-3" />
                                    {domain}
                                  </span>
                                )}
                                <span className="flex items-center gap-1 text-xs text-slate-500">
                                  <Calendar className="w-3 h-3" />
                                  {formatDate(doc.processed_at)}
                                </span>
                              </div>
                            </div>

                            <div className="flex items-center gap-3">
                              <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800 rounded-sm">
                                <span className="text-xs font-semibold text-slate-400 font-mono">
                                  {entityCount}
                                </span>
                                <span className="text-xs text-slate-500">entities</span>
                              </div>

                              {status === "pending" && (
                                <button
                                  onClick={() => handleProcessDocument(doc.id, project.id)}
                                  disabled={isProcessing}
                                  className="flex items-center gap-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded-sm text-xs transition-colors"
                                >
                                  {isProcessing ? (
                                    <Loader className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <Play className="w-3 h-3" />
                                  )}
                                  Process
                                </button>
                              )}

                              <button
                                onClick={() => handleRemoveDocument(project.id, doc.id)}
                                className="p-1.5 hover:bg-red-500/20 rounded-sm text-slate-500 hover:text-red-400 transition-colors"
                                title="Remove document"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-center py-8 text-slate-500">
                        <FileText className="w-10 h-10 mx-auto mb-3 opacity-50" />
                        <p className="text-sm">No documents in this project</p>
                        <p className="text-xs text-slate-600 mt-1">
                          Go to Search to add documents from web results
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Full Document Manager */}
                  {details.documents && details.documents.length > 0 && (
                    <div className="mt-6 pt-6 border-t border-slate-700">
                      <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
                        Advanced Management
                      </h5>
                      <ProjectDocumentManager
                        projectId={project.id}
                        documents={convertToProjectDocuments(details.documents || [], details.entities || [])}
                        onDocumentsChange={() => fetchProjectDetails(project.id)}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Empty State */}
        {projects.length === 0 && (
          <div className="py-12 text-center">
            <FolderKanban className="w-12 h-12 mx-auto mb-4 text-slate-600" />
            <h3 className="text-lg font-medium text-slate-400 mb-1">
              No projects yet
            </h3>
            <p className="text-sm text-slate-500">
              Create your first project to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
