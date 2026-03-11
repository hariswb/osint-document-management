import { invoke } from "@tauri-apps/api/core";

export interface Entity {
  id: number;
  name: string;
  entity_type: string;
  confidence: number | null;
  source_doc_id: number | null;
  created_at: string;
}

export interface Relationship {
  id: number;
  source_entity_id: number;
  target_entity_id: number;
  source_name: string;
  target_name: string;
  relationship_type: string;
  confidence: number | null;
  evidence: string | null;
  source_doc_id: number | null;
  created_at: string;
}

export interface EntityAlias {
  id: number;
  entity_id: number;
  alias_name: string;
  confidence: number | null;
  created_at: string;
}

export interface Document {
  id: number;
  filename: string;
  file_path: string;
  file_hash: string | null;
  doc_type: string;
  processed_at: string;
  status: "pending" | "processing" | "completed" | "error";
  entity_count: number;
  domain?: string;
}

export interface Stats {
  entities: number;
  documents: number;
  relationships: number;
}

export interface SearchResult {
  id: number;
  title: string;
  href: string;
  body: string;
  source: string;
  domain: string;
  publish_date: string | null;
}

export interface AddSearchResultsRequest {
  projectId: number;
  results: SearchResult[];
}

export interface AddSearchResultsResponse {
  success: boolean;
  message: string;
  documentsAdded: number;
  duplicatesSkipped: number;
  docIds: number[];
}

export interface SearchResponse {
  query: string;
  count: number;
  results: SearchResult[];
}

export interface ProcessResponse {
  success: boolean;
  message: string;
  articles_processed: number;
  entities_extracted: number;
}

export interface EntityDetails {
  entity: Entity;
  relationships: Relationship[];
  aliases: EntityAlias[];
  documents: Document[];
  coOccurring: Entity[];
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  status: string;
  document_count?: number;
  created_at: string;
  updated_at: string;
}

export interface NetworkNode {
  id: string;
  name: string;
  type: string;
  confidence: number | null;
}

export interface NetworkLink {
  source: string;
  target: string;
  relationship_type: string;
  confidence: number | null;
  evidence: string | null;
}

export interface NetworkData {
  nodes: NetworkNode[];
  links: NetworkLink[];
}

export interface NetworkFilters {
  projectId?: number;
  entityTypes?: string;
  excludeEntities?: string;
  contextWindow?: "sentence" | "paragraph" | "sliding";
  windowSize?: number;
}

export interface DocumentProcessOptions {
  nerEnabled?: boolean;
  extractRelationships?: boolean;
  entityTypes?: string[];
}

export interface DocumentProcessResult {
  success: boolean;
  message: string;
  entitiesExtracted: number;
  docId: number;
}

export interface BatchProcessResult {
  success: boolean;
  message: string;
  documentsProcessed: number;
  totalEntitiesExtracted: number;
  errors: string[];
}

export interface RemoveDocumentResult {
  success: boolean;
  message: string;
  cascadeResult?: {
    success: boolean;
    entitiesDeleted: number;
    documentDeleted: boolean;
  };
}

export const api = {
  // Check if Python backend is running
  checkHealth: async (): Promise<boolean> => {
    try {
      return await invoke("check_api_health");
    } catch (error) {
      console.error("Health check failed:", error);
      return false;
    }
  },

  // Get database statistics
  getStats: async (): Promise<Stats> => {
    return await invoke("get_stats");
  },

  // Get entities from database
  getEntities: async (
    entityType?: string,
    projectId?: number,
    limit: number = 100
  ): Promise<Entity[]> => {
    return await invoke("get_entities", {
      entityType: entityType || null,
      projectId: projectId || null,
      limit,
    });
  },

  // Search the web
  searchWeb: async (
    query: string,
    maxResults: number = 10,
    region: string = "id-id",
    provider: string = "duckduckgo"
  ): Promise<SearchResponse> => {
    return await invoke("search_web", {
      query,
      maxResults,
      region,
      provider,
    });
  },

  // Full pipeline: Search → Scrape → Extract → Store
  processQuery: async (
    query: string,
    maxResults: number = 5,
    region: string = "id-id"
  ): Promise<ProcessResponse> => {
    return await invoke("process_query", {
      query,
      maxResults,
      region,
    });
  },

  // Scrape a URL
  scrapeUrl: async (url: string): Promise<string> => {
    return await invoke("scrape_url", { url });
  },

  // Get entity details with relationships, aliases, and documents
  getEntityDetails: async (entityId: number): Promise<EntityDetails> => {
    return await invoke("get_entity_details", { entityId });
  },

  // Update entity
  updateEntity: async (entityId: number, data: Partial<Entity>): Promise<Entity> => {
    return await invoke("update_entity", { entityId, data });
  },

  // Delete entity
  deleteEntity: async (entityId: number): Promise<void> => {
    return await invoke("delete_entity", { entityId });
  },

  // Get relationships
  getRelationships: async (entityId?: number): Promise<Relationship[]> => {
    return await invoke("get_relationships", { entityId });
  },

  // Get all projects
  getProjects: async (): Promise<Project[]> => {
    return await invoke("get_projects");
  },

  // Create a new project
  createProject: async (name: string, description?: string): Promise<Project> => {
    return await invoke("create_project", { name, description });
  },

  // Update a project
  updateProject: async (projectId: number, data: Partial<Project>): Promise<Project> => {
    return await invoke("update_project", { projectId, data });
  },

  // Delete a project
  deleteProject: async (projectId: number): Promise<void> => {
    return await invoke("delete_project", { projectId });
  },

  // Get project details
  getProject: async (projectId: number): Promise<Project & { documents: Document[]; entities: Entity[] }> => {
    return await invoke("get_project", { projectId });
  },

  // Add document to project
  addDocumentToProject: async (projectId: number, docId: number): Promise<void> => {
    return await invoke("add_document_to_project", { projectId, docId });
  },

  // Remove document from project
  removeDocumentFromProject: async (projectId: number, docId: number): Promise<void> => {
    return await invoke("remove_document_from_project", { projectId, docId, cascade: false });
  },

  // Process a single document
  processDocument: async (docId: number, options: DocumentProcessOptions = {}): Promise<DocumentProcessResult> => {
    return await invoke("process_document", {
      docId,
      options: {
        ner_enabled: options.nerEnabled ?? true,
        extract_relationships: options.extractRelationships ?? true,
        entity_types: options.entityTypes || null,
      },
    });
  },

  // Batch process multiple documents
  batchProcessDocuments: async (docIds: number[], options: DocumentProcessOptions = {}): Promise<BatchProcessResult> => {
    return await invoke("batch_process_documents", {
      docIds,
      options: {
        ner_enabled: options.nerEnabled ?? true,
        extract_relationships: options.extractRelationships ?? true,
        entity_types: options.entityTypes || null,
      },
    });
  },

  // Remove document with cascade delete
  removeDocumentWithCascade: async (projectId: number, docId: number): Promise<RemoveDocumentResult> => {
    return await invoke("remove_document_from_project", { projectId, docId, cascade: true });
  },

  // Get network graph data
  getNetworkData: async (filters: NetworkFilters = {}): Promise<NetworkData> => {
    return await invoke("get_network_data", {
      projectId: filters.projectId || null,
      entityTypes: filters.entityTypes || null,
      excludeEntities: filters.excludeEntities || null,
      contextWindow: filters.contextWindow || null,
      windowSize: filters.windowSize || null,
    });
  },

  // Add search results to project
  addSearchResultsToProject: async (
    projectId: number, 
    results: SearchResult[],
    autoProcess: boolean = false
  ): Promise<AddSearchResultsResponse> => {
    return await invoke("add_search_results_to_project", {
      projectId,
      results,
      autoProcess,
    });
  },
};

export default api;
