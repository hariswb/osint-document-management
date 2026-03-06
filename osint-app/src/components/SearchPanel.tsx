import { useState } from "react";
import { Search, Loader2, Globe, FileText } from "lucide-react";

interface SearchResult {
  id: number;
  title: string;
  url: string;
  snippet: string;
  source: string;
}

export default function SearchPanel() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    
    // Simulate search results for now
    // In production, this would call the Tauri command to run Python search
    setTimeout(() => {
      setResults([
        {
          id: 1,
          title: `Search results for "${query}"`,
          url: "https://example.com/article-1",
          snippet: "This is a sample search result showing content related to your query...",
          source: "Web",
        },
        {
          id: 2,
          title: `Another article about ${query}`,
          url: "https://example.com/article-2",
          snippet: "More content related to your search query appears here...",
          source: "News",
        },
      ]);
      setIsSearching(false);
    }, 1500);
  };

  const handleScrape = async (result: SearchResult) => {
    setSelectedResult(result);
    // In production, this would call the Tauri command to scrape the URL
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Web Search</h2>
        <p className="text-gray-400">
          Search the web and extract entities from articles
        </p>
      </div>

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
              className="w-full pl-12 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-white"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
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
                    <p className="text-sm text-gray-400 mb-2">{result.url}</p>
                    <p className="text-gray-300">{result.snippet}</p>
                  </div>
                  <button
                    onClick={() => handleScrape(result)}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
                  >
                    Scrape & Extract
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected Result Detail */}
      {selectedResult && (
        <div className="mt-6 p-4 bg-gray-800/50 border border-primary-500/30 rounded-lg">
          <h3 className="font-semibold mb-2">Processing: {selectedResult.title}</h3>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            Scraping content and extracting entities...
          </div>
        </div>
      )}
    </div>
  );
}
