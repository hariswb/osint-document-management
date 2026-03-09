import { useState, useEffect } from "react";
import { Search, Database, Network, FileText, Settings, FolderKanban, Activity, AlertCircle } from "lucide-react";
import SearchPanel from "./components/SearchPanel";
import EntityList from "./components/EntityList";
import NetworkGraph from "./components/NetworkGraph";
import DocumentPanel from "./components/DocumentPanel";
import ProjectPanel from "./components/ProjectPanel";
import api, { Stats, Project } from "./services/api";

type Tab = "projects" | "search" | "documents" | "entities" | "network" | "settings";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("projects");
  const [backendConnected, setBackendConnected] = useState(false);
  const [stats, setStats] = useState<Stats>({ entities: 0, documents: 0, relationships: 0 });
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (backendConnected) {
      fetchProjects();
      // Auto-refresh projects every 10 seconds
      const interval = setInterval(fetchProjects, 10000);
      return () => clearInterval(interval);
    }
  }, [backendConnected]);

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

  const fetchProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
      // If current project no longer exists, clear it
      if (currentProject && !data.find((p: Project) => p.id === currentProject.id)) {
        setCurrentProject(null);
      }
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  const handleProjectSelect = (project: Project | null) => {
    setCurrentProject(project);
    if (project) {
      setActiveTab("search");
    }
  };

  const handleProjectsChanged = () => {
    fetchProjects();
  };

  const tabs = [
    { id: "projects" as Tab, label: "Projects", icon: FolderKanban, requiresProject: false },
    { id: "search" as Tab, label: "Search", icon: Search, requiresProject: true },
    { id: "documents" as Tab, label: "Documents", icon: FileText, requiresProject: true },
    { id: "entities" as Tab, label: "Entities", icon: Database, requiresProject: true },
    { id: "network" as Tab, label: "Network", icon: Network, requiresProject: true },
    { id: "settings" as Tab, label: "Settings", icon: Settings, requiresProject: false },
  ];

  const isTabEnabled = (tab: typeof tabs[0]) => {
    if (!backendConnected) return false;
    if (tab.requiresProject) return !!currentProject;
    return true;
  };

  const renderContent = () => {
    switch (activeTab) {
      case "projects":
        return (
          <ProjectPanel
            projects={projects}
            currentProject={currentProject}
            onProjectSelect={handleProjectSelect}
            onProjectsChanged={handleProjectsChanged}
          />
        );
      case "search":
        return currentProject ? (
          <SearchPanel
            backendConnected={backendConnected}
            currentProject={currentProject}
            onDocumentsAdded={handleProjectsChanged}
          />
        ) : (
          <NoProjectSelected onGoToProjects={() => setActiveTab("projects")} />
        );
      case "documents":
        return currentProject ? (
          <DocumentPanel currentProject={currentProject} />
        ) : (
          <NoProjectSelected onGoToProjects={() => setActiveTab("projects")} />
        );
      case "entities":
        return currentProject ? (
          <EntityList currentProject={currentProject} />
        ) : (
          <NoProjectSelected onGoToProjects={() => setActiveTab("projects")} />
        );
      case "network":
        return currentProject ? (
          <NetworkGraph currentProject={currentProject} />
        ) : (
          <NoProjectSelected onGoToProjects={() => setActiveTab("projects")} />
        );
      case "settings":
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">Settings</h2>
            <p className="text-slate-400">Application settings will be available here.</p>
          </div>
        );
      default:
        return <NoProjectSelected onGoToProjects={() => setActiveTab("projects")} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-4 py-2 h-14 flex-none">
        <div className="flex items-center justify-between h-full">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-sm flex items-center justify-center">
              <Network className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">OSINT NER</h1>
              <p className="text-xs text-slate-500 font-mono">v0.1.0</p>
            </div>
          </div>

          {/* Current Project Display */}
          <div className="flex items-center gap-4">
            {currentProject ? (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-900/30 border border-blue-700/50 rounded-sm">
                <FolderKanban className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-sm font-medium text-blue-300">{currentProject.name}</span>
                <span className="text-xs text-blue-500 font-mono">#{currentProject.id}</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-sm">
                <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                <span className="text-sm text-slate-400">No project selected</span>
              </div>
            )}

            {/* Backend Status */}
            <div className="flex items-center gap-2 px-2 py-1 bg-slate-900/50 rounded-sm">
              <span className={`w-1.5 h-1.5 rounded-full ${backendConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
              <span className="text-xs text-slate-400 font-mono">{backendConnected ? "ONLINE" : "OFFLINE"}</span>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-900/50 rounded-sm">
                <Database className="w-3 h-3 text-blue-500" />
                <span className="text-xs font-mono text-slate-300">{stats.entities}</span>
                <span className="text-xs text-slate-500">ENT</span>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-900/50 rounded-sm">
                <FileText className="w-3 h-3 text-green-500" />
                <span className="text-xs font-mono text-slate-300">{stats.documents}</span>
                <span className="text-xs text-slate-500">DOC</span>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-900/50 rounded-sm">
                <Activity className="w-3 h-3 text-purple-500" />
                <span className="text-xs font-mono text-slate-300">{stats.relationships}</span>
                <span className="text-xs text-slate-500">REL</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <nav className="w-14 bg-slate-800 border-r border-slate-700 flex flex-col">
          <div className="py-2">
            <ul className="space-y-0.5">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const enabled = isTabEnabled(tab);
                return (
                  <li key={tab.id}>
                    <button
                      onClick={() => enabled && setActiveTab(tab.id)}
                      disabled={!enabled}
                      className={`w-full flex items-center justify-center py-3 transition-colors relative group ${
                        activeTab === tab.id
                          ? "text-blue-500"
                          : enabled
                          ? "text-slate-500 hover:text-slate-300"
                          : "text-slate-700 cursor-not-allowed"
                      }`}
                    >
                      {activeTab === tab.id && (
                        <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-blue-500" />
                      )}
                      <Icon className="w-5 h-5" />
                      <span className="absolute left-14 px-2 py-1 bg-slate-700 text-xs rounded-sm opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                        {tab.label}
                        {!enabled && backendConnected && " (Select Project)"}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 overflow-auto bg-slate-900">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

function NoProjectSelected({ onGoToProjects }: { onGoToProjects: () => void }) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center p-8">
        <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">No Project Selected</h2>
        <p className="text-slate-400 mb-6 max-w-md">
          You need to select or create a project before you can search, view documents, entities, or network.
        </p>
        <button
          onClick={onGoToProjects}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-sm text-sm font-medium transition-colors"
        >
          Go to Projects
        </button>
      </div>
    </div>
  );
}

export default App;
