use std::env;

mod get_matches;
use get_matches::get_matches;


fn main() {
    // Accept file hash as an argument
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        panic!("Please provide a json file and a file hash");
    }
    let json_file = &args[1];
    let file_hash = &args[2];

    let json_output = get_matches(json_file, file_hash);
    println!("{}", json_output);
}