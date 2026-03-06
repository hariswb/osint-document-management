import { useState } from "react";
import { Database, Filter, Download, User, Building2, MapPin, Calendar } from "lucide-react";

interface Entity {
  id: number;
  name: string;
  type: string;
  confidence: number;
  created_at: string;
}

const mockEntities: Entity[] = [
  { id: 1, name: "Prabowo Subianto", type: "PER", confidence: 0.98, created_at: "2026-03-06" },
  { id: 2, name: "Indonesia", type: "GPE", confidence: 0.95, created_at: "2026-03-06" },
  { id: 3, name: "Gerindra", type: "ORG", confidence: 0.92, created_at: "2026-03-06" },
  { id: 4, name: "Joko Widodo", type: "PER", confidence: 0.97, created_at: "2026-03-06" },
  { id: 5, name: "Jakarta", type: "GPE", confidence: 0.94, created_at: "2026-03-06" },
];

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
  const [filter, setFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");

  const filteredEntities = mockEntities.filter((entity) => {
    const matchesFilter = filter === "all" || entity.type === filter;
    const matchesSearch = entity.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const entityTypes = ["all", "PER", "ORG", "GPE", "DAT", "NOR", "ORG"];

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
        <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
          <Download className="w-4 h-4" />
          Export
        </button>
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
              <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${entityTypeColors[entity.type] || "bg-gray-500/20 text-gray-400"}`}>
                {entityTypeIcons[entity.type] || <Database className="w-4 h-4" />}
                {entity.type}
              </div>
              <span className="text-xs text-gray-500">{entity.created_at}</span>
            </div>
            <h3 className="font-semibold text-lg mb-2">{entity.name}</h3>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Confidence</span>
              <div className="flex items-center gap-2">
                <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${entity.confidence * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-primary-400">
                  {(entity.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats */}
      <div className="mt-6 grid grid-cols-4 gap-4">
        {[
          { label: "Total", count: 127, color: "text-white" },
          { label: "People", count: 25, color: "text-blue-400" },
          { label: "Organizations", count: 15, color: "text-purple-400" },
          { label: "Locations", count: 10, color: "text-green-400" },
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
