// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn search_web(query: String, max_results: u32) -> Result<String, String> {
    // This would call the Python backend
    // For now, return mock data
    Ok(format!("Searched for: {} (max {} results)", query, max_results))
}

#[tauri::command]
async fn scrape_url(url: String) -> Result<String, String> {
    // This would call the Python backend
    Ok(format!("Scraped: {}", url))
}

#[tauri::command]
async fn extract_entities(text: String) -> Result<String, String> {
    // This would call the Python backend
    Ok(format!("Extracted entities from text ({} chars)", text.len()))
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            search_web,
            scrape_url,
            extract_entities
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
