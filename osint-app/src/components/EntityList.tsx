import { useState, useEffect } from "react";
import { Database, Filter, Download, User, Building2, MapPin, Landmark, Scale, Package, DollarSign, Map, Loader2, AlertCircle, FolderKanban } from "lucide-react";
import api, { Entity, Project } from "../services/api";
import EntityDetailPanel from "./EntityDetailPanel";

const ALLOWED_ENTITY_TYPES = ["PER", "ORG", "NOR", "LAW", "PRD", "GPE", "MON", "LOC"];

const entityTypeIcons: Record<string, React.ReactNode> = {
  PER: <User className="w-3.5 h-3.5" />,
  ORG: <Building2 className="w-3.5 h-3.5" />,
  GPE: <MapPin className="w-3.5 h-3.5" />,
  NOR: <Landmark className="w-3.5 h-3.5" />,
  LAW: <Scale className="w-3.5 h-3.5" />,
  PRD: <Package className="w-3.5 h-3.5" />,
  MON: <DollarSign className="w-3.5 h-3.5" />,
  LOC: <Map className="w-3.5 h-3.5" />,
};

const entityTypeColors: Record<string, string> = {
  PER: "bg-blue-500/20 text-blue-400",
  ORG: "bg-purple-500/20 text-purple-400",
  GPE: "bg-green-500/20 text-green-400",
  NOR: "bg-orange-500/20 text-orange-400",
  LAW: "bg-amber-500/20 text-amber-400",
  PRD: "bg-cyan-500/20 text-cyan-400",
  MON: "bg-yellow-500/20 text-yellow-400",
  LOC: "bg-emerald-500/20 text-emerald-400",
};

interface EntityListProps {
  currentProject: Project;
}

export default function EntityList({ currentProject }: EntityListProps) {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [stats, setStats] = useState({ entities: 0, people: 0, organizations: 0, locations: 0 });
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [minConfidence, setMinConfidence] = useState(0);

  useEffect(() => {
    fetchEntities();
  }, [currentProject.id]);

  const fetchEntities = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEntities(undefined, currentProject.id, 100);
      setEntities(data);
      
      // Calculate stats
      const people = data.filter(e => e.entity_type === "PER").length;
      const orgs = data.filter(e => e.entity_type === "ORG").length;
      const locations = data.filter(e => e.entity_type === "GPE").length;
      
      setStats({
        entities: data.length,
        people,
        organizations: orgs,
        locations
      });
    } catch (err) {
      setError("Failed to fetch entities. Make sure the backend is running.");
      console.error("Error fetching entities:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredEntities = entities.filter((entity) => {
    const matchesAllowed = ALLOWED_ENTITY_TYPES.includes(entity.entity_type);
    const matchesFilter = filter === "all" || entity.entity_type === filter;
    const matchesSearch = entity.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesConfidence = (entity.confidence ?? 0) >= minConfidence;
    return matchesAllowed && matchesFilter && matchesSearch && matchesConfidence;
  });

  const entityTypes = ["all", ...ALLOWED_ENTITY_TYPES];

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
              onClick={fetchEntities}
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
    <div className="p-4">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Database className="w-3.5 h-3.5" />
          <span className="text-slate-300 font-medium">Entities</span>
          <span className="text-slate-600">·</span>
          <FolderKanban className="w-3 h-3 text-blue-500" />
          <span className="text-blue-400">{currentProject.name}</span>
          <span className="text-slate-600">·</span>
          <span className="font-mono text-slate-300">{stats.entities}</span>
          <span>total</span>
          <span className="text-blue-400 font-mono ml-1">{stats.people}</span><span>PER</span>
          <span className="text-purple-400 font-mono ml-1">{stats.organizations}</span><span>ORG</span>
          <span className="text-green-400 font-mono ml-1">{stats.locations}</span><span>GPE</span>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={fetchEntities}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-sm transition-colors"
            title="Refresh"
          >
            <Loader2 className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button className="flex items-center gap-1.5 px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded-sm transition-colors text-xs">
            <Download className="w-3.5 h-3.5" />
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <Filter className="w-3.5 h-3.5 text-slate-500" />
        <div className="flex flex-wrap gap-1">
          {entityTypes.map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-2 py-0.5 rounded-sm text-xs font-medium transition-colors ${
                filter === type
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              }`}
            >
              {type === "all" ? "All" : type}
            </button>
          ))}
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-slate-500">Score &gt;</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={minConfidence}
            onChange={(e) => setMinConfidence(Number(e.target.value))}
            className="w-20 accent-blue-500"
          />
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={minConfidence}
            onChange={(e) => {
              const v = Math.min(1, Math.max(0, Number(e.target.value)));
              setMinConfidence(v);
            }}
            className="w-14 px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-200 text-xs font-mono"
          />
        </div>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search entities..."
          className="px-2 py-1 bg-slate-800 border border-slate-700 rounded-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-200 text-xs"
        />
      </div>

      {/* Entity Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
        {filteredEntities.map((entity) => (
          <div
            key={entity.id}
            onClick={() => setSelectedEntity(entity)}
            className="bg-slate-800 border border-slate-700 rounded-sm p-3 hover:border-blue-500/50 transition-colors cursor-pointer"
          >
            <div className="flex items-center justify-between mb-2">
              <div className={`px-1.5 py-0.5 rounded-sm text-xs font-medium flex items-center gap-1 ${entityTypeColors[entity.entity_type] || "bg-slate-500/20 text-slate-400"}`}>
                {entityTypeIcons[entity.entity_type] || <Database className="w-3.5 h-3.5" />}
                {entity.entity_type}
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(entity.confidence || 0) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-slate-400">
                  {((entity.confidence || 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <p className="font-medium text-sm text-slate-200 truncate">{entity.name}</p>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredEntities.length === 0 && (
        <div className="text-center py-10">
          <Database className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-400">
            {searchTerm ? "No entities found" : "No entities yet"}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {searchTerm
              ? "Try adjusting your search or filters"
              : "Process documents in this project to extract entities"}
          </p>
        </div>
      )}

      {/* Entity Detail Panel */}
      {selectedEntity && (
        <EntityDetailPanel
          entity={selectedEntity}
          onClose={() => setSelectedEntity(null)}
          onEntityUpdated={fetchEntities}
        />
      )}
    </div>
  );
}
