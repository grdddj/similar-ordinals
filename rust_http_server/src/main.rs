extern crate num_bigint;

use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::env;
use serde::de::Deserializer;
use serde::ser::Serializer;
use num_bigint::BigUint;

#[derive(Debug, Clone)]
pub struct BigUintWrapper(pub BigUint);

impl BigUintWrapper {
    pub fn new(bin_str: &str) -> Self {
        let big_uint = binary_string_to_big_uint(bin_str);
        BigUintWrapper(big_uint)
    }
}

impl Serialize for BigUintWrapper {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {   
        let serialized = self.0.to_str_radix(2);
        serializer.serialize_str(&serialized)
    }
}

impl<'de> Deserialize<'de> for BigUintWrapper {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let binary_string = String::deserialize(deserializer)?;
        let wrapper = BigUintWrapper::new(&binary_string);
        Ok(wrapper)
    }
}

#[derive(Debug, Clone, Serialize)]
struct MatchItem {
    ord_id: String,
    match_sum: usize,
}

#[derive(Debug, Serialize, Deserialize)]
struct Db {
    data: HashMap<String, BigUintWrapper>,
}

async fn ord_id_handler(ord_id: web::Path<String>, db: web::Data<Db>) -> impl Responder {
    let file_hash_int: BigUint = if let Some(value) = db.data.get(ord_id.as_str()) {
        value.0.clone()
    } else {
        // If the ord_id is not found, return an empty array
        return HttpResponse::Ok().body("[]".to_string());
    };
    let top_matches = get_top_matches(file_hash_int, &db.data);
    let ret_value = serde_json::to_string(&top_matches).expect("Failed to serialize to JSON");
    HttpResponse::Ok().body(ret_value)
}

async fn file_hash_handler(file_hash: web::Path<String>, db: web::Data<Db>) -> impl Responder {
    let file_hash_int = binary_string_to_big_uint(file_hash.as_str());
    let top_matches = get_top_matches(file_hash_int, &db.data);
    let ret_value = serde_json::to_string(&top_matches).expect("Failed to serialize to JSON");
    HttpResponse::Ok().body(ret_value)
}

fn get_top_matches(file_hash: BigUint, data: &HashMap<String, BigUintWrapper>) -> Vec<MatchItem> {
    let mut matches: Vec<MatchItem> = Vec::new();
    for (ord_id, wrapped_hash) in data {
        let distance = hamming_distance(&file_hash, &wrapped_hash.0);
        let match_sum = (256 - distance).try_into().unwrap();
        matches.push(MatchItem { ord_id: ord_id.to_string(), match_sum });
    }
    matches.sort_by(|a, b| b.match_sum.cmp(&a.match_sum));
    let top_matches = &matches[..20];
    top_matches.to_vec()
}

fn binary_string_to_big_uint(bin_str: &str) -> BigUint {
    BigUint::from_bytes_be(&bin_str.as_bytes())
}

fn hamming_distance(a: &BigUint, b: &BigUint) -> u64 {
    let xor_result = a ^ b;
    xor_result.count_ones()
}


#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Read command-line arguments - get the JSON DB location
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <path_to_db_json_file> <optional-port>", args[0]);
        std::process::exit(1);
    }
    let json_file_path = &args[1];
    let port = if args.len() > 2 {
        args[2].clone()
    } else {
        "8081".to_string()
    };
    let host = format!("127.0.0.1:{}", port);

    // Read the JSON file and parse it into a Db struct
    let db_json = fs::read_to_string(json_file_path).expect("Unable to read file");
    let db: Db = serde_json::from_str(&db_json).expect("Unable to parse JSON");

    // Share the Db instance across threads
    let shared_db = web::Data::new(db);

    println!("Starting server on {}, reading {}", host, json_file_path);

    HttpServer::new(move || {
        App::new()
            .app_data(shared_db.clone())
            .route("/ord_id/{ord_id}", web::get().to(ord_id_handler))
            .route("/file_hash/{file_hash}", web::get().to(file_hash_handler))
    })
    .bind(host)?
    .run()
    .await
}
