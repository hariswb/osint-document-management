import { useState } from "react";
import { 
  Search, 
  Loader2, 
  AlertCircle, 
  MapPin,
  CheckSquare,
  Square,
  Plus,
  ArrowRight,
  FolderKanban
} from "lucide-react";
import api, { SearchResult, Project } from "../services/api";

interface SearchPanelProps {
  backendConnected: boolean;
  currentProject: Project;
  onDocumentsAdded?: () => void;
}

const REGION_OPTIONS = [
  { value: "id-id", label: "Indonesia (id-id)" },
  { value: "wt-wt", label: "International (wt-wt)" },
];

const PROVIDER_OPTIONS = [
  { value: "duckduckgo", label: "DuckDuckGo", description: "Privacy-focused, no API key needed" },
  { value: "google", label: "Google", description: "Better results, may need fallback" },
];

function extractDomain(url: string): string {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
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

export default function SearchPanel({ backendConnected, currentProject, onDocumentsAdded }: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("id-id");
  const [provider, setProvider] = useState("duckduckgo");
  const [autoProcess, setAutoProcess] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedResults, setSelectedResults] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !backendConnected) return;

    setIsSearching(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await api.searchWeb(query, 10, region, provider);
      setResults(response.results);
      // Select all results by default
      setSelectedResults(new Set(response.results.map(r => r.id)));
    } catch (err) {
      setError("Failed to search. Please try again.");
      console.error("Search error:", err);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleSelectAll = () => {
    if (selectedResults.size === results.length) {
      setSelectedResults(new Set());
    } else {
      setSelectedResults(new Set(results.map(r => r.id)));
    }
  };

  const toggleSelectResult = (resultId: number) => {
    const newSelected = new Set(selectedResults);
    if (newSelected.has(resultId)) {
      newSelected.delete(resultId);
    } else {
      newSelected.add(resultId);
    }
    setSelectedResults(newSelected);
  };

  const handleAddToProject = async () => {
    if (!currentProject || selectedResults.size === 0) return;

    setIsAdding(true);
    setError(null);
    setSuccess(null);
    
    try {
      const selectedItems = results.filter(r => selectedResults.has(r.id));
      const response = await api.addSearchResultsToProject(currentProject.id, selectedItems, autoProcess);
      
      if (response.success) {
        setSuccess(response.message);
        setResults([]);
        setSelectedResults(new Set());
        
        // Notify parent that documents were added
        if (onDocumentsAdded) {
          onDocumentsAdded();
        }
      } else {
        setError(response.message || "Failed to add documents");
      }
    } catch (err) {
      setError("Failed to add documents to project. Please try again.");
      console.error("Add to project error:", err);
    } finally {
      setIsAdding(false);
    }
  };

  const canAddToProject = currentProject !== null && selectedResults.size > 0;

  return (
    <div className="p-4">
      {/* Page Header */}
      <div className="flex items-center gap-2 text-xs text-slate-500 mb-4">
        <Search className="w-3.5 h-3.5" />
        <span className="text-slate-300 font-medium">Web Search</span>
        <span className="text-slate-600">·</span>
        <FolderKanban className="w-3 h-3 text-blue-500" />
        <span className="text-blue-400">{currentProject.name}</span>
        <span className="text-slate-600 font-mono">#{currentProject.id}</span>
      </div>

      {!backendConnected && (
        <div className="mb-6 bg-yellow-500/10 border border-yellow-500/30 rounded-sm p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-400" />
          <p className="text-yellow-400">
            Backend not connected. Please start the Python API server.
          </p>
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-sm p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-500/10 border border-green-500/30 rounded-sm p-4 flex items-center gap-3">
          <div className="w-5 h-5 rounded-full bg-green-400 flex items-center justify-center text-slate-900 font-bold text-sm">✓</div>
          <p className="text-green-400">{success}</p>
        </div>
      )}

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query..."
              disabled={!backendConnected}
              className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-sm focus:outline-none focus:ring-2 focus:ring-slate-500 text-slate-200 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim() || !backendConnected}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm font-medium flex items-center gap-2 transition-colors text-sm"
          >
            {isSearching ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Search
              </>
            )}
          </button>
        </div>

        {/* Options */}
        <div className="flex flex-wrap items-center gap-4 mt-4">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-slate-500" />
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              disabled={!backendConnected || isSearching}
              className="bg-slate-800 border border-slate-700 rounded-sm px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {REGION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-slate-500" />
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              disabled={!backendConnected || isSearching}
              className="bg-slate-800 border border-slate-700 rounded-sm px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {PROVIDER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <span className="text-xs text-slate-500">
              {PROVIDER_OPTIONS.find(p => p.value === provider)?.description}
            </span>
          </div>
        </div>
      </form>

      {/* Results Header */}
      {results.length > 0 && (
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={toggleSelectAll}
              className="flex items-center gap-2 text-sm text-slate-300 hover:text-slate-200"
            >
              {selectedResults.size === results.length ? (
                <CheckSquare className="w-4 h-4 text-blue-400" />
              ) : (
                <Square className="w-4 h-4 text-slate-600" />
              )}
              <span className="font-mono text-xs">
                {selectedResults.size}/{results.length} selected
              </span>
            </button>
            
            {/* Auto-process checkbox */}
            <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer hover:text-slate-300">
              <input
                type="checkbox"
                checked={autoProcess}
                onChange={(e) => setAutoProcess(e.target.checked)}
                disabled={!backendConnected}
                className="w-4 h-4 rounded-sm border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-900"
              />
              <span>Auto-process after adding</span>
            </label>
          </div>
          
          <button
            onClick={handleAddToProject}
            disabled={!canAddToProject || isAdding}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm text-sm font-medium transition-colors"
          >
            {isAdding ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Adding...
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                Add to "{currentProject.name}"
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-2">
          {results.slice(0, 10).map((result) => {
            const isSelected = selectedResults.has(result.id);
            const domain = extractDomain(result.href);
            const date = formatDate(result.publish_date);
            
            return (
              <div
                key={result.id}
                onClick={() => toggleSelectResult(result.id)}
                className={`bg-slate-800 border rounded-sm p-3 cursor-pointer transition-colors ${
                  isSelected 
                    ? "border-blue-500 bg-blue-900/10" 
                    : "border-slate-700 hover:border-slate-600"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 text-blue-400" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-600" />
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-slate-200 mb-1 truncate">
                      {result.title}
                    </h4>
                    
                    <div className="flex items-center gap-3 mb-1.5">
                      <span className="text-xs text-slate-500 font-mono">
                        {domain}
                      </span>
                      {date && (
                        <>
                          <span className="text-slate-600">•</span>
                          <span className="text-xs text-slate-500">
                            {date}
                          </span>
                        </>
                      )}
                    </div>
                    
                    <p className="text-xs text-slate-400 line-clamp-2">
                      {result.body}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
          
          {results.length > 10 && (
            <p className="text-center text-xs text-slate-500 py-2">
              Showing first 10 of {results.length} results
            </p>
          )}
        </div>
      )}

      {/* Empty State */}
      {results.length === 0 && !isSearching && query && !error && (
        <div className="text-center py-12">
          <Search className="w-12 h-12 mx-auto mb-4 text-slate-700" />
          <p className="text-slate-500 text-sm">No results found</p>
        </div>
      )}

      {/* Initial State */}
      {results.length === 0 && !isSearching && !query && (
        <div className="text-center py-12 border border-dashed border-slate-700 rounded-sm">
          <Search className="w-12 h-12 mx-auto mb-4 text-slate-600" />
          <p className="text-slate-400 text-sm mb-1">Enter a search query to find documents</p>
          <p className="text-slate-500 text-xs">
            Results will be added to project "{currentProject.name}"
          </p>
        </div>
      )}
    </div>
  );
}
