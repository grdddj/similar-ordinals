use std::env;

mod get_matches;
use get_matches::get_matches;


fn main() {
    // Accept file hash as an argument
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        panic!("Please provide a json file and a file hash / ord_id");
    }
    let json_file = &args[1];
    let second_arg = &args[2];

    // If the second argument is less than 10 characters, assume it's an ord ID, otherwise it's a file hash
    let (ord_id, file_hash) = if second_arg.len() < 10 {
        (Some(second_arg.as_str()), None)
    } else {
        (None, Some(second_arg.as_str()))
    };

    let json_output = get_matches(json_file, ord_id, file_hash);
    println!("{}", json_output);
}