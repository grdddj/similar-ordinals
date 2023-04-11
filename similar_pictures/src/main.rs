use clap::Parser;

mod get_matches;
use get_matches::{get_matches, index_all_pictures};


#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Location of JSON DB file
    #[arg(short, long)]
    path_to_json: String,

    /// Optional ord ID
    #[arg(short, long)]
    ord_id: Option<String>,

    /// Optional file hash
    #[arg(short, long)]
    file_hash: Option<String>,

    /// How many matches to return
    #[arg(short, long, default_value = "20")]
    top_n: usize,

    // Indexing options below

    /// Whether to index all the pictures in the JSON file
    #[arg(long)]
    index: bool,

    /// Location of the result file
    #[arg(short, long, default_value = "result.txt")]
    result_file: String,
}


fn main() {
    // Accept CLI arguments
    let args = Args::parse();

    // if there is index in args, call the indexing function
    if args.index {
        index_all_pictures(args.path_to_json, args.result_file);
        return;
    }

    let json_output = get_matches(args.path_to_json, args.ord_id, args.file_hash, args.top_n);
    println!("{}", json_output);
}
