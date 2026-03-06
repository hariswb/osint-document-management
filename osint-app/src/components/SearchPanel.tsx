import { useState } from "react";
import { Search, Loader2, Globe, FileText, AlertCircle } from "lucide-react";
import api, { SearchResult } from "../services/api";

interface SearchPanelProps {
  backendConnected: boolean;
}

export default function SearchPanel({ backendConnected }: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !backendConnected) return;

    setIsSearching(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await api.searchWeb(query, 10);
      setResults(response.results);
    } catch (err) {
      setError("Failed to search. Please try again.");
      console.error("Search error:", err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleProcess = async () => {
    if (!query.trim() || !backendConnected) return;

    setIsProcessing(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await api.processQuery(query, 5);
      if (response.success) {
        setSuccess(`Processed ${response.articles_processed} articles and extracted ${response.entities_extracted} entities!`);
        setResults([]); // Clear search results
      }
    } catch (err) {
      setError("Failed to process query. Please try again.");
      console.error("Process error:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Web Search</h2>
        <p className="text-gray-400">
          Search the web and extract entities from articles
        </p>
      </div>

      {!backendConnected && (
        <div className="mb-6 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-400" />
          <p className="text-yellow-400">
            Backend not connected. Please start the Python API server.
          </p>
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-500/10 border border-green-500/30 rounded-lg p-4 flex items-center gap-3">
          <div className="w-5 h-5 rounded-full bg-green-400 flex items-center justify-center text-gray-900 font-bold">✓</div>
          <p className="text-green-400">{success}</p>
        </div>
      )}

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query (e.g., 'Prabowo Subianto')..."
              disabled={!backendConnected}
              className="w-full pl-12 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-white disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim() || !backendConnected}
            className="px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium flex items-center gap-2 transition-colors"
          >
            {isSearching ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Search
              </>
            )}
          </button>
          <button
            type="button"
            onClick={handleProcess}
            disabled={isProcessing || !query.trim() || !backendConnected}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium flex items-center gap-2 transition-colors"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <FileText className="w-5 h-5" />
                Full Pipeline
              </>
            )}
          </button>
        </div>

        {/* Options */}
        <div className="flex gap-4 mt-4">
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input type="checkbox" className="rounded bg-gray-800 border-gray-700" />
            News only
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input type="checkbox" className="rounded bg-gray-800 border-gray-700" defaultChecked />
            Auto-scrape results
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input type="checkbox" className="rounded bg-gray-800 border-gray-700" defaultChecked />
            Extract entities
          </label>
        </div>
      </form>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Search Results</h3>
          <div className="grid gap-4">
            {results.map((result) => (
              <div
                key={result.id}
                className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-primary-500 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {result.source === "Web" ? (
                        <Globe className="w-4 h-4 text-blue-400" />
                      ) : (
                        <FileText className="w-4 h-4 text-green-400" />
                      )}
                      <span className="text-sm text-gray-500">{result.source}</span>
                    </div>
                    <h4 className="text-lg font-medium text-primary-400 mb-1">
                      {result.title}
                    </h4>
                    <p className="text-sm text-gray-400 mb-2">{result.href}</p>
                    <p className="text-gray-300">{result.body}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
