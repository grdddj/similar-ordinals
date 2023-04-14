use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::env;

#[derive(Debug, Clone, Serialize)]
struct MatchItem {
    ord_id: String,
    match_sum: usize,
}

#[derive(Debug, Serialize, Deserialize)]
struct Db {
    data: HashMap<String, String>,
}

async fn ord_id_handler(ord_id: web::Path<String>, db: web::Data<Db>) -> impl Responder {
    let file_hash: String = if let Some(value) = db.data.get(ord_id.as_str()) {
        value.to_string()
    } else {
        // If the ord_id is not found, return an empty array
        return HttpResponse::Ok().body("[]".to_string());
    };
    let top_matches = get_top_matches(file_hash, &db.data);
    let ret_value = serde_json::to_string(&top_matches).expect("Failed to serialize to JSON");
    HttpResponse::Ok().body(ret_value)
}

async fn file_hash_handler(file_hash: web::Path<String>, db: web::Data<Db>) -> impl Responder {
    let top_matches = get_top_matches(file_hash.to_string(), &db.data);
    let ret_value = serde_json::to_string(&top_matches).expect("Failed to serialize to JSON");
    HttpResponse::Ok().body(ret_value)
}

fn get_top_matches(file_hash: String, data: &HashMap<String, String>) -> Vec<MatchItem> {
    let mut matches: Vec<MatchItem> = Vec::new();
    for (ord_id, hash_value) in data {
        let match_sum = file_hash
            .chars()
            .zip(hash_value.chars())
            .filter(|(c1, c2)| c1 == c2)
            .count();
        matches.push(MatchItem { ord_id: ord_id.to_string(), match_sum });
    }
    matches.sort_by(|a, b| b.match_sum.cmp(&a.match_sum));
    let top_matches = &matches[..20];
    top_matches.to_vec()
}


#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Read command-line arguments - get the JSON DB location
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <path_to_db_json_file>", args[0]);
        std::process::exit(1);
    }
    let json_file_path = &args[1];

    // Read the JSON file and parse it into a Db struct
    let db_json = fs::read_to_string(json_file_path).expect("Unable to read file");
    let db: Db = serde_json::from_str(&db_json).expect("Unable to parse JSON");

    // Share the Db instance across threads
    let shared_db = web::Data::new(db);

    HttpServer::new(move || {
        App::new()
            .app_data(shared_db.clone())
            .route("/ord_id/{ord_id}", web::get().to(ord_id_handler))
            .route("/file_hash/{file_hash}", web::get().to(file_hash_handler))
    })
    .bind("127.0.0.1:8081")?
    .run()
    .await
}
