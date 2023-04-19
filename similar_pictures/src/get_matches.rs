use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs::File;
use std::io::{BufReader, Read};
use std::collections::HashMap;

use std::fs::OpenOptions;
use std::io::Write;

use bit_set::BitSet;

#[derive(Debug, Serialize)]
struct MatchItem {
    ord_id: String,
    match_sum: usize,
}

#[derive(Debug, Serialize, Deserialize)]
struct Db {
    data: HashMap<String, String>,
}

const CHUNK_SIZE: usize = 30;
const TOP_N: usize = 20;

/// Get matches for specified ord_id or file_hash
pub fn get_matches(file_path: String, ord_id: Option<String>, file_hash: Option<String>, top_n: usize) -> String {
    let file = File::open(file_path).expect("Unable to open the file");
    let mut reader = BufReader::new(file);
    let mut content = String::new();
    reader.read_to_string(&mut content)
        .expect("Unable to read the file content");

    let db: Db = serde_json::from_str(&content).expect("Unable to parse JSON");

    // If ord ID is provided, use it, otherwise use the file hash
    let file_hash = if let Some(ord_id) = ord_id {
        if let Some(value) = db.data.get(&ord_id) {
            value.to_string()
        } else {
            return "[]".to_string();
        }
    } else if let Some(file_hash) = file_hash {
        file_hash
    } else {
        panic!("No ord ID or file hash provided");
    };

    let hash_length: usize = file_hash.len();

    let file_hash_bitset = str_to_bitset(&file_hash);
    
    let mut matches: Vec<MatchItem> = Vec::new();
    for (ord_id, hash) in db.data {
        let hash_bitset = str_to_bitset(&hash);
        // println!("hash_bitset: {:?}", hash_bitset);
        let different_bit_set = file_hash_bitset.symmetric_difference(&hash_bitset);
        // println!("different_bit_set: {:?}", different_bit_set);
        let different_bit_count = different_bit_set.count();
        // println!("different_bit_count: {:?}", different_bit_count);
        let same_bit_count = hash_length - different_bit_count;
        let match_sum = usize::max(same_bit_count, different_bit_count);
        // println!("same_bit_count: {:?}", same_bit_count);
        // let match_sum = file_hash
        // .chars()
        // .zip(hash.chars())
        // .filter(|(c1, c2)| c1 == c2)
        // .count();
        // println!("match_sum: {:?}", match_sum);
        matches.push(MatchItem { ord_id, match_sum });
    }

    matches.sort_by(|a, b| b.match_sum.cmp(&a.match_sum));

    let top_matches = &matches[..top_n];

    serde_json::to_string(top_matches).expect("Failed to serialize to JSON")
}


fn str_to_bitset(bit_str: &str) -> BitSet {
    let mut bitset = BitSet::with_capacity(bit_str.len());
    for (i, c) in bit_str.chars().enumerate() {
        if c == '1' {
            bitset.insert(i);
        }
    }
    bitset
}


#[allow(dead_code)]
/// Find similarity for all the pictures in the JSON file
pub fn index_all_pictures(file_path: String, result_file: String) {
    let mut json_file = File::open(file_path).expect("Unable to open the file");
    let mut content = String::new();
    json_file.read_to_string(&mut content)
        .expect("Unable to read the file content");
    
    let json_data: Value = serde_json::from_str(&content).expect("Unable to parse JSON");
    let mut data_map_all: Vec<_> = if let Value::Object(data_map) = json_data {
        data_map.into_iter().collect()
    } else {
        panic!("Unable to parse JSON");
    };
    // sort data map according to number keys - by their INT value
    data_map_all.sort_by(|a, b| a.0.parse::<usize>().unwrap().cmp(&b.0.parse::<usize>().unwrap()));
    // reverse it
    data_map_all.reverse();

    // Prepare the result file
    let mut output_file = OpenOptions::new()
        .append(true)
        .create(true)
        .open(result_file)
        .expect("Unable to open the result file");


    let chunks = data_map_all.chunks(CHUNK_SIZE);

    for chunk in chunks {
        let json_data: Value = serde_json::from_str(&content).expect("Unable to parse JSON");
        let mut my_dict: HashMap<String, Vec<MatchItem>> = HashMap::new();
        if let Value::Object(data_map) = json_data {
            for (ord_id, hash_value) in data_map {
                if let Value::String(hash) = hash_value {
                    for (inner_ord_id, file_hash) in chunk.iter() {
                        let match_list = my_dict.entry(inner_ord_id.to_string()).or_insert_with(Vec::new);
                        let match_sum = file_hash.as_str().unwrap()
                            .chars()
                            .zip(hash.chars())
                            .filter(|(c1, c2)| c1 == c2)
                            .count();
                         match_list.push(MatchItem { ord_id: ord_id.clone(), match_sum });
                    }
                }
            }
        }
        
        // Sort the match list and write it to the file
        for (i, mut match_list) in my_dict.into_iter() {
            match_list.sort_unstable_by(|a, b| b.match_sum.cmp(&a.match_sum));
            let top_matches = &match_list[..TOP_N];
            let json = serde_json::to_string(top_matches).expect("Failed to serialize to JSON");
            let to_write = format!("{} - {:?}\n", i, json);
            output_file.write_all(to_write.as_bytes()).expect("Unable to write data to the file");
        }
    }
}
