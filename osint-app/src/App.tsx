import { useState, useEffect } from "react";
import { Search, Database, Network, FileText, Settings } from "lucide-react";
import SearchPanel from "./components/SearchPanel";
import EntityList from "./components/EntityList";
import NetworkGraph from "./components/NetworkGraph";
import DocumentPanel from "./components/DocumentPanel";
import api, { Stats } from "./services/api";

type Tab = "search" | "entities" | "network" | "documents" | "settings";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("search");
  const [backendConnected, setBackendConnected] = useState(false);
  const [stats, setStats] = useState<Stats>({ entities: 0, documents: 0, relationships: 0 });

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkBackendHealth = async () => {
    try {
      const isHealthy = await api.checkHealth();
      setBackendConnected(isHealthy);
      if (isHealthy) {
        const statsData = await api.getStats();
        setStats(statsData);
      }
    } catch (error) {
      setBackendConnected(false);
    }
  };

  const tabs = [
    { id: "search" as Tab, label: "Search", icon: Search },
    { id: "entities" as Tab, label: "Entities", icon: Database },
    { id: "network" as Tab, label: "Network", icon: Network },
    { id: "documents" as Tab, label: "Documents", icon: FileText },
    { id: "settings" as Tab, label: "Settings", icon: Settings },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case "search":
        return <SearchPanel backendConnected={backendConnected} />;
      case "entities":
        return <EntityList />;
      case "network":
        return <NetworkGraph />;
      case "documents":
        return <DocumentPanel />;
      case "settings":
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">Settings</h2>
            <p className="text-gray-400">Application settings will be available here.</p>
          </div>
        );
      default:
        return <SearchPanel backendConnected={backendConnected} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
              <Network className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">OSINT NER Tool</h1>
              <p className="text-sm text-gray-400">v0.1.0</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full text-sm flex items-center gap-2 ${
              backendConnected 
                ? "bg-green-500/20 text-green-400" 
                : "bg-red-500/20 text-red-400"
            }`}>
              <span className={`w-2 h-2 rounded-full ${backendConnected ? "bg-green-400" : "bg-red-400"}`} />
              {backendConnected ? "Connected" : "Disconnected"}
            </span>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-gray-800 min-h-[calc(100vh-73px)] border-r border-gray-700">
          <div className="p-4">
            <ul className="space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <li key={tab.id}>
                    <button
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                        activeTab === tab.id
                          ? "bg-primary-600 text-white"
                          : "text-gray-400 hover:bg-gray-700 hover:text-white"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{tab.label}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Stats */}
          <div className="mt-8 px-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Statistics
            </h3>
            <div className="space-y-3">
              <div className="bg-gray-700/50 rounded-lg p-3">
                <p className="text-2xl font-bold text-primary-400">{stats.entities}</p>
                <p className="text-sm text-gray-400">Entities</p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-3">
                <p className="text-2xl font-bold text-green-400">{stats.documents}</p>
                <p className="text-sm text-gray-400">Documents</p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-3">
                <p className="text-2xl font-bold text-purple-400">{stats.relationships}</p>
                <p className="text-sm text-gray-400">Relationships</p>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;
