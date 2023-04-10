use serde::Serialize;
use serde_json::Value;
use std::fs::File;
use std::io::Read;

#[derive(Serialize)]
struct MatchItem {
    ord_id: String,
    match_sum: usize,
}


pub fn get_matches(file_path: &str, ord_id: Option<&str>, file_hash: Option<&str>) -> String {
    let mut file = File::open(file_path).expect("Unable to open the file");
    let mut content = String::new();
    file.read_to_string(&mut content)
        .expect("Unable to read the file content");

    let json_data: Value = serde_json::from_str(&content).expect("Unable to parse JSON");
    let json_data_clone = json_data.clone();

    // If ord ID is provided, use it, otherwise use the file hash
    let file_hash = if let Some(ord_id) = ord_id {
        if let Some(value) = json_data_clone.get(ord_id) {
            value.as_str().expect("Unable to parse JSON")
        } else {
            panic!("Ord ID {} was not found in the JSON data", ord_id);
        }
    } else if let Some(file_hash) = file_hash {
        file_hash
    } else {
        panic!("No ord ID or file hash provided");
    };

    let mut matches: Vec<MatchItem> = Vec::new();
    if let Value::Object(data_map) = json_data {
        for (ord_id, hash_value) in data_map {
            if let Value::String(hash) = hash_value {
                let match_sum = file_hash
                    .chars()
                    .zip(hash.chars())
                    .filter(|(c1, c2)| c1 == c2)
                    .count();
                matches.push(MatchItem { ord_id, match_sum });
            }
        }
    }

    matches.sort_by(|a, b| b.match_sum.cmp(&a.match_sum));

    let top_matches = &matches[..20];

    serde_json::to_string(top_matches).expect("Failed to serialize to JSON")
}
