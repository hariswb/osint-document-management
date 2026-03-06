// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};

const API_BASE_URL: &str = "http://127.0.0.1:8000";

#[derive(Serialize, Deserialize)]
struct ProcessRequest {
    query: String,
    max_results: u32,
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
    limit: i32,
) -> Result<Vec<Entity>, String> {
    let client = reqwest::Client::new();
    let mut url = format!("{}/api/entities?limit={}", API_BASE_URL, limit);
    
    if let Some(et) = entity_type {
        url.push_str(&format!("&entity_type={}", et));
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
async fn search_web(query: String, max_results: u32) -> Result<SearchResponse, String> {
    let client = reqwest::Client::new();
    let request = ProcessRequest {
        query,
        max_results,
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
async fn process_query(query: String, max_results: u32) -> Result<ProcessResponse, String> {
    let client = reqwest::Client::new();
    let request = ProcessRequest {
        query,
        max_results,
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
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await;
    
    match response {
        Ok(resp) => Ok(resp.status().is_success()),
        Err(_) => Ok(false),
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
            check_api_health
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
