import { invoke } from "@tauri-apps/api/core";

export interface Entity {
  id: number;
  name: string;
  entity_type: string;
  confidence: number | null;
  source_doc_id: number | null;
  created_at: string;
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
    limit: number = 100
  ): Promise<Entity[]> => {
    return await invoke("get_entities", {
      entityType: entityType || null,
      limit,
    });
  },

  // Search the web
  searchWeb: async (
    query: string,
    maxResults: number = 10
  ): Promise<SearchResponse> => {
    return await invoke("search_web", {
      query,
      maxResults,
    });
  },

  // Full pipeline: Search → Scrape → Extract → Store
  processQuery: async (
    query: string,
    maxResults: number = 5
  ): Promise<ProcessResponse> => {
    return await invoke("process_query", {
      query,
      maxResults,
    });
  },

  // Scrape a URL
  scrapeUrl: async (url: string): Promise<string> => {
    return await invoke("scrape_url", { url });
  },
};

export default api;
