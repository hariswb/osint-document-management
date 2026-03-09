import { useState, useEffect } from "react";
import { 
  X, 
  User, 
  Building2, 
  MapPin, 
  Calendar, 
  Link2, 
  FileText, 
  Clock,
  Tag,
  Edit3,
  Merge,
  Trash2,
  Loader2,
  AlertCircle
} from "lucide-react";
import api, { Entity, Relationship, EntityAlias, Document } from "../services/api";

interface EntityDetailPanelProps {
  entity: Entity;
  onClose: () => void;
  onEntityUpdated: () => void;
}

interface EntityDetails {
  entity: Entity;
  relationships: Relationship[];
  aliases: EntityAlias[];
  documents: Document[];
  coOccurring: Entity[];
}

const entityTypeIcons: Record<string, React.ReactNode> = {
  PER: <User className="w-5 h-5" />,
  ORG: <Building2 className="w-5 h-5" />,
  GPE: <MapPin className="w-5 h-5" />,
  DAT: <Calendar className="w-5 h-5" />,
};

const entityTypeColors: Record<string, string> = {
  PER: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  ORG: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  GPE: "bg-green-500/20 text-green-400 border-green-500/30",
  DAT: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  NOR: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  EVT: "bg-red-500/20 text-red-400 border-red-500/30",
};

const relationshipTypeColors: Record<string, string> = {
  "co-occurrence": "bg-gray-500/20 text-gray-400",
  "affiliation": "bg-blue-500/20 text-blue-400",
  "family": "bg-pink-500/20 text-pink-400",
  "ownership": "bg-yellow-500/20 text-yellow-400",
  "employment": "bg-green-500/20 text-green-400",
  "location": "bg-purple-500/20 text-purple-400",
};

export default function EntityDetailPanel({ entity, onClose, onEntityUpdated }: EntityDetailPanelProps) {
  const [details, setDetails] = useState<EntityDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "relationships" | "aliases" | "documents">("overview");
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(entity.name);

  useEffect(() => {
    fetchEntityDetails();
  }, [entity.id]);

  const fetchEntityDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEntityDetails(entity.id);
      setDetails(data);
    } catch (err) {
      setError("Failed to load entity details");
      console.error("Error fetching entity details:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateName = async () => {
    try {
      await api.updateEntity(entity.id, { name: editedName });
      setIsEditing(false);
      onEntityUpdated();
      fetchEntityDetails();
    } catch (err) {
      console.error("Error updating entity:", err);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this entity? This action cannot be undone.")) {
      return;
    }
    try {
      await api.deleteEntity(entity.id);
      onClose();
      onEntityUpdated();
    } catch (err) {
      console.error("Error deleting entity:", err);
    }
  };

  const handleMerge = async () => {
    // TODO: Implement merge dialog
    alert("Merge functionality will be implemented with entity deduplication");
  };

  if (loading) {
    return (
      <div className="fixed inset-y-0 right-0 w-[480px] bg-gray-800 border-l border-gray-700 shadow-2xl z-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-y-0 right-0 w-[480px] bg-gray-800 border-l border-gray-700 shadow-2xl z-50 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Entity Details</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-y-0 right-0 w-[480px] bg-gray-800 border-l border-gray-700 shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-start justify-between mb-4">
          <div className={`p-3 rounded-xl ${entityTypeColors[entity.entity_type]?.split(' ')[0] || 'bg-gray-500/20'}`}>
            {entityTypeIcons[entity.entity_type] || <User className="w-5 h-5" />}
          </div>
          <div className="flex gap-2">
            <button 
              onClick={handleMerge}
              className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white"
              title="Merge with another entity"
            >
              <Merge className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setIsEditing(!isEditing)}
              className={`p-2 rounded-lg ${isEditing ? 'bg-primary-500/20 text-primary-400' : 'hover:bg-gray-700 text-gray-400 hover:text-white'}`}
              title="Edit entity"
            >
              <Edit3 className="w-4 h-4" />
            </button>
            <button 
              onClick={handleDelete}
              className="p-2 hover:bg-red-500/20 rounded-lg text-gray-400 hover:text-red-400"
              title="Delete entity"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Entity Name */}
        <div className="mb-3">
          {isEditing ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                className="flex-1 px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={handleUpdateName}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-sm font-medium"
              >
                Save
              </button>
            </div>
          ) : (
            <h2 className="text-2xl font-bold">{entity.name}</h2>
          )}
        </div>

        {/* Entity Type Badge */}
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium border ${entityTypeColors[entity.entity_type] || "bg-gray-500/20 text-gray-400 border-gray-500/30"}`}>
          {entityTypeIcons[entity.entity_type]}
          {entity.entity_type}
        </div>

        {/* Confidence Score */}
        <div className="mt-4 flex items-center gap-3">
          <span className="text-sm text-gray-400">Extraction Confidence</span>
          <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full"
              style={{ width: `${(entity.confidence || 0) * 100}%` }}
            />
          </div>
          <span className="text-sm font-medium text-primary-400">
            {((entity.confidence || 0) * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700">
        {[
          { id: "overview", label: "Overview", count: null },
          { id: "relationships", label: "Relationships", count: details?.relationships.length || 0 },
          { id: "aliases", label: "Aliases", count: details?.aliases.length || 0 },
          { id: "documents", label: "Documents", count: details?.documents.length || 0 },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-primary-500 text-primary-400"
                : "border-transparent text-gray-400 hover:text-white"
            }`}
          >
            {tab.label}
            {tab.count !== null && tab.count > 0 && (
              <span className="ml-2 px-1.5 py-0.5 bg-gray-700 rounded text-xs">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="bg-gray-900/50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Basic Information
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">ID</span>
                  <span className="font-mono">#{entity.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Type</span>
                  <span>{entity.entity_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Created</span>
                  <span>{new Date(entity.created_at).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Source Document</span>
                  <span>#{entity.source_doc_id || "N/A"}</span>
                </div>
              </div>
            </div>

            {/* Co-occurring Entities */}
            {details?.coOccurring && details.coOccurring.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  Frequently Co-occurring
                </h3>
                <div className="space-y-2">
                  {details.coOccurring.slice(0, 5).map((coEntity) => (
                    <div 
                      key={coEntity.id}
                      className="flex items-center gap-3 p-3 bg-gray-900/50 rounded-lg hover:bg-gray-700/50 transition-colors cursor-pointer"
                    >
                      <div className={`p-1.5 rounded ${entityTypeColors[coEntity.entity_type]?.split(' ')[0] || 'bg-gray-500/20'}`}>
                        {entityTypeIcons[coEntity.entity_type] || <User className="w-3 h-3" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{coEntity.name}</p>
                        <p className="text-xs text-gray-500">{coEntity.entity_type}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-gray-900/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-primary-400">{details?.relationships.length || 0}</p>
                <p className="text-xs text-gray-500">Relationships</p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-green-400">{details?.aliases.length || 0}</p>
                <p className="text-xs text-gray-500">Aliases</p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-purple-400">{details?.documents.length || 0}</p>
                <p className="text-xs text-gray-500">Documents</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === "relationships" && (
          <div className="space-y-3">
            {details?.relationships.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Link2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No relationships found</p>
                <p className="text-sm mt-1">Relationships will be extracted automatically from documents</p>
              </div>
            ) : (
              details?.relationships.map((rel) => (
                <div key={rel.id} className="bg-gray-900/50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${relationshipTypeColors[rel.relationship_type] || "bg-gray-500/20 text-gray-400"}`}>
                      {rel.relationship_type}
                    </span>
                    <span className="text-xs text-gray-500">
                      {((rel.confidence || 0) * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-medium">{rel.source_name}</span>
                    <span className="text-gray-500">→</span>
                    <span className="font-medium">{rel.target_name}</span>
                  </div>
                  {rel.evidence && (
                    <p className="mt-2 text-sm text-gray-400 italic">
                      "{rel.evidence}"
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "aliases" && (
          <div className="space-y-3">
            {details?.aliases.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Tag className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No aliases found</p>
                <p className="text-sm mt-1">Aliases help group different names for the same entity</p>
              </div>
            ) : (
              details?.aliases.map((alias) => (
                <div key={alias.id} className="flex items-center justify-between bg-gray-900/50 rounded-lg p-3">
                  <div className="flex items-center gap-3">
                    <Tag className="w-4 h-4 text-gray-500" />
                    <span>{alias.alias_name}</span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {((alias.confidence || 0) * 100).toFixed(0)}% match
                  </span>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "documents" && (
          <div className="space-y-3">
            {details?.documents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No documents found</p>
              </div>
            ) : (
              details?.documents.map((doc) => (
                <div key={doc.id} className="bg-gray-900/50 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-gray-500 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{doc.filename}</p>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(doc.processed_at).toLocaleDateString()}
                        </span>
                        <span className="uppercase">{doc.doc_type}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
