import { useState } from "react";
import { Search, Database, Network, FileText, Settings } from "lucide-react";
import SearchPanel from "./components/SearchPanel";
import EntityList from "./components/EntityList";
import NetworkGraph from "./components/NetworkGraph";
import DocumentPanel from "./components/DocumentPanel";

type Tab = "search" | "entities" | "network" | "documents" | "settings";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("search");

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
        return <SearchPanel />;
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
        return <SearchPanel />;
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
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
              ● Connected
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
                <p className="text-2xl font-bold text-primary-400">127</p>
                <p className="text-sm text-gray-400">Entities</p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-3">
                <p className="text-2xl font-bold text-green-400">2</p>
                <p className="text-sm text-gray-400">Documents</p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-3">
                <p className="text-2xl font-bold text-purple-400">0</p>
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
