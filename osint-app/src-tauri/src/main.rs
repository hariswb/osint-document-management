// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};

const API_BASE_URL: &str = "http://127.0.0.1:8000";

#[derive(Serialize, Deserialize)]
struct ProcessRequest {
    query: String,
    max_results: u32,
    region: String,
    provider: String,
}

#[derive(Serialize, Deserialize)]
struct ProcessResponse {
    success: bool,
    message: String,
    articles_processed: i32,
    entities_extracted: i32,
}

#[derive(Serialize, Deserialize)]
struct Entity {
    id: i32,
    name: String,
    entity_type: String,
    confidence: Option<f32>,
    source_doc_id: Option<i32>,
    created_at: String,
}

#[derive(Serialize, Deserialize)]
struct Stats {
    entities: i32,
    documents: i32,
    relationships: i32,
}

#[derive(Serialize, Deserialize)]
struct SearchResponse {
    query: String,
    count: i32,
    results: Vec<SearchResult>,
}

#[derive(Serialize, Deserialize)]
struct SearchResult {
    id: i32,
    title: String,
    href: String,
    body: String,
    source: String,
    domain: String,
    publish_date: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct AddSearchResultsRequest {
    project_id: i32,
    results: Vec<SearchResult>,
    auto_process: bool,
}

#[derive(Serialize, Deserialize)]
struct AddSearchResultsResponse {
    success: bool,
    message: String,
    documents_added: i32,
    duplicates_skipped: i32,
    doc_ids: Vec<i32>,
}

#[derive(Serialize, Deserialize)]
struct Relationship {
    id: i32,
    source_entity_id: i32,
    target_entity_id: i32,
    source_name: String,
    target_name: String,
    relationship_type: String,
    confidence: Option<f32>,
    evidence: Option<String>,
    source_doc_id: Option<i32>,
    created_at: String,
}

#[derive(Serialize, Deserialize)]
struct EntityAlias {
    id: i32,
    entity_id: i32,
    alias_name: String,
    confidence: Option<f32>,
    created_at: String,
}

#[derive(Serialize, Deserialize)]
struct Document {
    id: i32,
    filename: String,
    file_path: String,
    file_hash: Option<String>,
    doc_type: Option<String>,
    processed_at: String,
}

#[derive(Serialize, Deserialize)]
struct EntityDetails {
    entity: Entity,
    relationships: Vec<Relationship>,
    aliases: Vec<EntityAlias>,
    documents: Vec<Document>,
    coOccurring: Vec<Entity>,
}

#[derive(Serialize, Deserialize)]
struct UpdateEntityRequest {
    name: Option<String>,
    entity_type: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct Project {
    id: i32,
    name: String,
    description: Option<String>,
    status: String,
    document_count: i32,
    created_at: String,
    updated_at: String,
}

#[derive(Serialize, Deserialize)]
struct CreateProjectRequest {
    name: String,
    description: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct NetworkNode {
    id: String,
    name: String,
    #[serde(rename = "type")]
    node_type: String,
    confidence: Option<f32>,
}

#[derive(Serialize, Deserialize)]
struct NetworkLink {
    source: String,
    target: String,
    #[serde(rename = "relationship_type")]
    relationship_type: String,
    confidence: Option<f32>,
    evidence: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct NetworkData {
    nodes: Vec<NetworkNode>,
    links: Vec<NetworkLink>,
}

#[derive(Serialize, Deserialize)]
struct NetworkFilters {
    project_id: Option<i32>,
    entity_types: Option<String>,
    exclude_entities: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct DocumentProcessOptions {
    ner_enabled: bool,
    extract_relationships: bool,
    entity_types: Option<Vec<String>>,
}

#[derive(Serialize, Deserialize)]
struct DocumentProcessResult {
    success: bool,
    message: String,
    entities_extracted: i32,
    doc_id: i32,
}

#[derive(Serialize, Deserialize)]
struct BatchProcessResult {
    success: bool,
    message: String,
    documents_processed: i32,
    total_entities_extracted: i32,
    errors: Vec<String>,
}

#[derive(Serialize, Deserialize)]
struct RemoveDocumentResult {
    success: bool,
    message: String,
    cascade_result: Option<serde_json::Value>,
}

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn get_stats() -> Result<Stats, String> {
    let client = reqwest::Client::new();
    let response = client
        .get(format!("{}/api/stats", API_BASE_URL))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let stats: Stats = response.json().await.map_err(|e| e.to_string())?;
        Ok(stats)
    } else {
        Err(format!("Failed to get stats: {}", response.status()))
    }
}

#[tauri::command]
async fn get_entities(
    entity_type: Option<String>,
    project_id: Option<i32>,
    limit: i32,
) -> Result<Vec<Entity>, String> {
    let client = reqwest::Client::new();
    let mut url = format!("{}/api/entities?limit={}", API_BASE_URL, limit);
    
    if let Some(et) = entity_type {
        url.push_str(&format!("&entity_type={}", et));
    }
    
    if let Some(pid) = project_id {
        url.push_str(&format!("&project_id={}", pid));
    }
    
    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let entities: Vec<Entity> = response.json().await.map_err(|e| e.to_string())?;
        Ok(entities)
    } else {
        Err(format!("Failed to get entities: {}", response.status()))
    }
}

#[tauri::command]
async fn search_web(query: String, max_results: u32, region: String, provider: String) -> Result<SearchResponse, String> {
    let client = reqwest::Client::new();
    let request = ProcessRequest {
        query,
        max_results,
        region,
        provider,
    };
    
    let response = client
        .post(format!("{}/api/search", API_BASE_URL))
        .json(&request)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let result: SearchResponse = response.json().await.map_err(|e| e.to_string())?;
        Ok(result)
    } else {
        Err(format!("Failed to search: {}", response.status()))
    }
}

#[tauri::command]
async fn process_query(query: String, max_results: u32, region: String, provider: Option<String>) -> Result<ProcessResponse, String> {
    let client = reqwest::Client::new();
    let request = ProcessRequest {
        query,
        max_results,
        region,
        provider: provider.unwrap_or_else(|| "duckduckgo".to_string()),
    };
    
    let response = client
        .post(format!("{}/api/process", API_BASE_URL))
        .json(&request)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let result: ProcessResponse = response.json().await.map_err(|e| e.to_string())?;
        Ok(result)
    } else {
        Err(format!("Failed to process: {}", response.status()))
    }
}

#[tauri::command]
async fn scrape_url(url: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .post(format!("{}/api/scrape?url={}", API_BASE_URL, url))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let result: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
        Ok(result.to_string())
    } else {
        Err(format!("Failed to scrape: {}", response.status()))
    }
}

#[tauri::command]
async fn check_api_health() -> Result<bool, String> {
    let client = reqwest::Client::new();
    let response = client
        .get(format!("{}/health", API_BASE_URL))
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await;
    
    match response {
        Ok(resp) => Ok(resp.status().is_success()),
        Err(_) => Ok(false),
    }
}

#[tauri::command]
async fn get_entity_details(entity_id: i32) -> Result<EntityDetails, String> {
    let client = reqwest::Client::new();
    let response = client
        .get(format!("{}/api/entities/{}", API_BASE_URL, entity_id))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let details: EntityDetails = response.json().await.map_err(|e| e.to_string())?;
        Ok(details)
    } else {
        Err(format!("Failed to get entity details: {}", response.status()))
    }
}

#[tauri::command]
async fn update_entity(entity_id: i32, data: UpdateEntityRequest) -> Result<Entity, String> {
    let client = reqwest::Client::new();
    let response = client
        .patch(format!("{}/api/entities/{}", API_BASE_URL, entity_id))
        .json(&data)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let entity: Entity = response.json().await.map_err(|e| e.to_string())?;
        Ok(entity)
    } else {
        Err(format!("Failed to update entity: {}", response.status()))
    }
}

#[tauri::command]
async fn delete_entity(entity_id: i32) -> Result<(), String> {
    let client = reqwest::Client::new();
    let response = client
        .delete(format!("{}/api/entities/{}", API_BASE_URL, entity_id))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        Ok(())
    } else {
        Err(format!("Failed to delete entity: {}", response.status()))
    }
}

#[tauri::command]
async fn get_relationships(entity_id: Option<i32>) -> Result<Vec<Relationship>, String> {
    let client = reqwest::Client::new();
    let mut url = format!("{}/api/relationships", API_BASE_URL);

    if let Some(id) = entity_id {
        url.push_str(&format!("?entity_id={}", id));
    }

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let relationships: Vec<Relationship> = response.json().await.map_err(|e| e.to_string())?;
        Ok(relationships)
    } else {
        Err(format!("Failed to get relationships: {}", response.status()))
    }
}

#[tauri::command]
async fn get_projects() -> Result<Vec<Project>, String> {
    let client = reqwest::Client::new();
    let response = client
        .get(format!("{}/api/projects", API_BASE_URL))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let projects: Vec<Project> = response.json().await.map_err(|e| e.to_string())?;
        Ok(projects)
    } else {
        Err(format!("Failed to get projects: {}", response.status()))
    }
}

#[tauri::command]
async fn create_project(name: String, description: Option<String>) -> Result<Project, String> {
    let client = reqwest::Client::new();
    let request = CreateProjectRequest { name, description };

    let response = client
        .post(format!("{}/api/projects", API_BASE_URL))
        .json(&request)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let project: Project = response.json().await.map_err(|e| e.to_string())?;
        Ok(project)
    } else {
        Err(format!("Failed to create project: {}", response.status()))
    }
}

#[tauri::command]
async fn update_project(project_id: i32, data: serde_json::Value) -> Result<Project, String> {
    let client = reqwest::Client::new();

    let response = client
        .patch(format!("{}/api/projects/{}", API_BASE_URL, project_id))
        .json(&data)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let project: Project = response.json().await.map_err(|e| e.to_string())?;
        Ok(project)
    } else {
        Err(format!("Failed to update project: {}", response.status()))
    }
}

#[tauri::command]
async fn delete_project(project_id: i32) -> Result<(), String> {
    let client = reqwest::Client::new();

    let response = client
        .delete(format!("{}/api/projects/{}", API_BASE_URL, project_id))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        Ok(())
    } else {
        Err(format!("Failed to delete project: {}", response.status()))
    }
}

#[tauri::command]
async fn get_project(project_id: i32) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();

    let response = client
        .get(format!("{}/api/projects/{}", API_BASE_URL, project_id))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let project: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
        Ok(project)
    } else {
        Err(format!("Failed to get project: {}", response.status()))
    }
}

#[tauri::command]
async fn add_document_to_project(project_id: i32, doc_id: i32) -> Result<(), String> {
    let client = reqwest::Client::new();

    let response = client
        .post(format!("{}/api/projects/{}/documents/{}", API_BASE_URL, project_id, doc_id))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        Ok(())
    } else {
        Err(format!("Failed to add document to project: {}", response.status()))
    }
}

#[tauri::command]
async fn remove_document_from_project(project_id: i32, doc_id: i32, cascade: bool) -> Result<RemoveDocumentResult, String> {
    let client = reqwest::Client::new();

    let response = client
        .delete(format!("{}/api/projects/{}/documents/{}?cascade={}", API_BASE_URL, project_id, doc_id, cascade))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let result: RemoveDocumentResult = response.json().await.map_err(|e| e.to_string())?;
        Ok(result)
    } else {
        Err(format!("Failed to remove document from project: {}", response.status()))
    }
}

#[tauri::command]
async fn process_document(docId: i32, options: DocumentProcessOptions) -> Result<DocumentProcessResult, String> {
    let client = reqwest::Client::new();

    let response = client
        .post(format!("{}/api/documents/{}/process", API_BASE_URL, docId))
        .json(&options)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let result: DocumentProcessResult = response.json().await.map_err(|e| e.to_string())?;
        Ok(result)
    } else {
        let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
        Err(format!("Failed to process document: {}", error_text))
    }
}

#[tauri::command]
async fn batch_process_documents(doc_ids: Vec<i32>, options: DocumentProcessOptions) -> Result<BatchProcessResult, String> {
    let client = reqwest::Client::new();

    let request = serde_json::json!({
        "doc_ids": doc_ids,
        "options": options
    });

    let response = client
        .post(format!("{}/api/documents/batch-process", API_BASE_URL))
        .json(&request)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let result: BatchProcessResult = response.json().await.map_err(|e| e.to_string())?;
        Ok(result)
    } else {
        Err(format!("Failed to batch process documents: {}", response.status()))
    }
}

#[tauri::command]
async fn get_network_data(
    project_id: Option<i32>,
    entity_types: Option<String>,
    exclude_entities: Option<String>,
    context_window: Option<String>,
    window_size: Option<i32>,
) -> Result<NetworkData, String> {
    let client = reqwest::Client::new();
    let mut url = format!("{}/api/network", API_BASE_URL);

    // Build query parameters
    let mut params = Vec::new();
    if let Some(pid) = project_id {
        params.push(format!("project_id={}", pid));
    }
    if let Some(types) = entity_types {
        params.push(format!("entity_types={}", urlencoding::encode(&types)));
    }
    if let Some(exclude) = exclude_entities {
        params.push(format!("exclude_entities={}", urlencoding::encode(&exclude)));
    }
    if let Some(cw) = context_window {
        params.push(format!("context_window={}", cw));
    }
    if let Some(ws) = window_size {
        params.push(format!("window_size={}", ws));
    }

    if !params.is_empty() {
        url.push_str("?");
        url.push_str(&params.join("&"));
    }

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let data: NetworkData = response.json().await.map_err(|e| e.to_string())?;
        Ok(data)
    } else {
        Err(format!("Failed to get network data: {}", response.status()))
    }
}

#[tauri::command]
async fn add_search_results_to_project(project_id: i32, results: Vec<SearchResult>, auto_process: bool) -> Result<AddSearchResultsResponse, String> {
    let client = reqwest::Client::new();
    let request = AddSearchResultsRequest {
        project_id,
        results,
        auto_process,
    };
    
    let response = client
        .post(format!("{}/api/search/add-to-project", API_BASE_URL))
        .json(&request)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let result: AddSearchResultsResponse = response.json().await.map_err(|e| e.to_string())?;
        Ok(result)
    } else {
        Err(format!("Failed to add search results to project: {}", response.status()))
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            get_stats,
            get_entities,
            search_web,
            process_query,
            scrape_url,
            check_api_health,
            get_entity_details,
            update_entity,
            delete_entity,
            get_relationships,
            get_projects,
            create_project,
            update_project,
            delete_project,
            get_project,
            add_document_to_project,
            remove_document_from_project,
            get_network_data,
            process_document,
            batch_process_documents,
            add_search_results_to_project
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
