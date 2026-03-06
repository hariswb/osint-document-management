import { useState, useEffect } from "react";
import { Database, Filter, Download, User, Building2, MapPin, Calendar, Loader2, AlertCircle } from "lucide-react";
import api, { Entity } from "../services/api";

const entityTypeIcons: Record<string, React.ReactNode> = {
  PER: <User className="w-4 h-4" />,
  ORG: <Building2 className="w-4 h-4" />,
  GPE: <MapPin className="w-4 h-4" />,
  DAT: <Calendar className="w-4 h-4" />,
};

const entityTypeColors: Record<string, string> = {
  PER: "bg-blue-500/20 text-blue-400",
  ORG: "bg-purple-500/20 text-purple-400",
  GPE: "bg-green-500/20 text-green-400",
  DAT: "bg-yellow-500/20 text-yellow-400",
  NOR: "bg-gray-500/20 text-gray-400",
  EVT: "bg-red-500/20 text-red-400",
};

export default function EntityList() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [stats, setStats] = useState({ entities: 0, people: 0, organizations: 0, locations: 0 });

  useEffect(() => {
    fetchEntities();
  }, []);

  const fetchEntities = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEntities(undefined, 100);
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
    const matchesFilter = filter === "all" || entity.entity_type === filter;
    const matchesSearch = entity.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const entityTypes = ["all", "PER", "ORG", "GPE", "DAT", "NOR"];

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
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
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <Database className="w-6 h-6" />
            Entity Database
          </h2>
          <p className="text-gray-400">
            Browse and filter extracted named entities
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={fetchEntities}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            title="Refresh"
          >
            <Loader2 className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-400">Filter by type:</span>
        </div>
        <div className="flex gap-2">
          {entityTypes.map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                filter === type
                  ? "bg-primary-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {type === "all" ? "All" : type}
            </button>
          ))}
        </div>
        <div className="flex-1" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search entities..."
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-white text-sm"
        />
      </div>

      {/* Entity Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredEntities.map((entity) => (
          <div
            key={entity.id}
            className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-primary-500/50 transition-colors cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${entityTypeColors[entity.entity_type] || "bg-gray-500/20 text-gray-400"}`}>
                {entityTypeIcons[entity.entity_type] || <Database className="w-4 h-4" />}
                {entity.entity_type}
              </div>
              <span className="text-xs text-gray-500">{new Date(entity.created_at).toLocaleDateString()}</span>
            </div>
            <h3 className="font-semibold text-lg mb-2">{entity.name}</h3>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Confidence</span>
              <div className="flex items-center gap-2">
                <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${(entity.confidence || 0) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-primary-400">
                  {((entity.confidence || 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats */}
      <div className="mt-6 grid grid-cols-4 gap-4">
        {[
          { label: "Total", count: stats.entities, color: "text-white" },
          { label: "People", count: stats.people, color: "text-blue-400" },
          { label: "Organizations", count: stats.organizations, color: "text-purple-400" },
          { label: "Locations", count: stats.locations, color: "text-green-400" },
        ].map((stat) => (
          <div key={stat.label} className="bg-gray-800 rounded-lg p-4 text-center">
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.count}</p>
            <p className="text-sm text-gray-400">{stat.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
