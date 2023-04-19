use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use serde::de::{Deserializer};
use serde::ser::{Serializer};
use std::collections::HashMap;
use std::fs;
use std::env;
 use bit_set::BitSet;
 
#[derive(Debug, Clone)]
pub struct BitSetWrapper {
    ones: BitSet,
    zeros: BitSet,
}

impl BitSetWrapper {
    pub fn new(bit_str: &str) -> Self {
        BitSetWrapper {
            ones: str_to_bitset(bit_str, 1).unwrap(),
            zeros: str_to_bitset(bit_str, 0).unwrap(),
        }
    }

    pub fn intersection_count(&self, other: &Self) -> usize {
        self.ones.intersection(&other.ones).count() + self.zeros.intersection(&other.zeros).count()
    }
}

impl Serialize for BitSetWrapper {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let binary_string = bitset_to_str(&self.ones);
        serializer.serialize_str(&binary_string)
    }
}

fn bitset_to_str(bitset: &BitSet) -> String {
    let mut binary_string = String::new();
    for i in 0..bitset.capacity() {
        binary_string.push(if bitset.contains(i) { '1' } else { '0' });
    }
    binary_string
}

impl<'de> Deserialize<'de> for BitSetWrapper {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let binary_string = String::deserialize(deserializer)?;
        let wrapper = BitSetWrapper::new(&binary_string);
        Ok(wrapper)
    }
}

fn str_to_bitset(bit_str: &str, zero_or_one: u8) -> Result<BitSet, String> {
    let mut bitset = BitSet::with_capacity(bit_str.len());
    match zero_or_one {
        0 => {
            for (i, c) in bit_str.chars().enumerate() {
                match c {
                    '0' => { bitset.insert(i); },
                    '1' => (),
                    _ => return Err(format!("Invalid character in binary string: {}", c)),
                }
            }
        },
        1 => {
            for (i, c) in bit_str.chars().enumerate() {
                match c {
                    '0' => (),
                    '1' => { bitset.insert(i); },
                    _ => return Err(format!("Invalid character in binary string: {}", c)),
                }
            }
        },
        _ => return Err(format!("Either zero or one could be supplied: {}", zero_or_one)),
    }
    Ok(bitset)
}

#[derive(Debug, Clone, Serialize)]
struct MatchItem {
    ord_id: String,
    match_sum: usize,
}

#[derive(Debug, Serialize, Deserialize)]
struct DbJSON {
    data: HashMap<String, String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct DbOptimized {
    data: HashMap<String, BitSetWrapper>,
}

async fn ord_id_handler(ord_id: web::Path<String>, db: web::Data<DbOptimized>) -> impl Responder {
    let file_bit_set_wrappet: BitSetWrapper = if let Some(bit_set_wrapper) = db.data.get(ord_id.as_str()) {
        bit_set_wrapper.clone()
    } else {
        // If the ord_id is not found, return an empty array
        return HttpResponse::Ok().body("[]".to_string());
    };
    let top_matches = get_top_matches(file_bit_set_wrappet, &db.data);
    let ret_value = serde_json::to_string(&top_matches).expect("Failed to serialize to JSON");
    HttpResponse::Ok().body(ret_value)
}

async fn file_hash_handler(file_hash: web::Path<String>, db: web::Data<DbOptimized>) -> impl Responder {
    let bit_set = BitSetWrapper::new(&file_hash);
    let top_matches = get_top_matches(bit_set, &db.data);
    let ret_value = serde_json::to_string(&top_matches).expect("Failed to serialize to JSON");
    HttpResponse::Ok().body(ret_value)
}

fn get_top_matches(file_bit_set_wrapper: BitSetWrapper, data: &HashMap<String, BitSetWrapper>) -> Vec<MatchItem> {
    let mut matches: Vec<MatchItem> = Vec::new();
    for (ord_id, current_bit_set_wrapper) in data {
        let match_sum = current_bit_set_wrapper.intersection_count(&file_bit_set_wrapper);
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
    let db: DbJSON = serde_json::from_str(&db_json).expect("Unable to parse JSON");

    // transform the DbJSON struct into a DbOptimized struct
    let mut db_optimized = DbOptimized { data: HashMap::new() };
    for (ord_id, file_hash) in db.data {
        db_optimized.data.insert(ord_id, BitSetWrapper::new(&file_hash));
    }

    // Share the DbOptimized instance across threads
    let shared_db = web::Data::new(db_optimized);

    let host = "127.0.0.1:8081";

    println!("Starting server - {}", host);

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
