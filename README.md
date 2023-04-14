## Ordinals pictures similarity

This project focuses on creating a service that displays similar ordinal pictures.

The pictures are classified using the `average hash` algorithm, which converts them into a bit sequence of 0s and 1s. They are then compared using the `Hamming distance`, which measures how many bits are common between two pictures. A detailed description can be found at [this link](https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html).

The average hashes of all ordinals are stored in a `JSON` file. Example data can be seen in [`average_hash_example.json`](average_hash_example.json).

*NOTE: we use JSON file instead of a "normal DB" because we need to always loop through all the data inside, and it turns out it is much faster to load all data from JSON file than from some DB like sqlite3.*

The main processing function is `get_matches_from_data` in [`get_matches.py`](get_matches.py). This function iterates through all the given average hashes and compares their similarity with the average hash calculated from the provided data - either an ordinal ID or the custom picture content. It returns a list of most similar ordinals, sorted by their similarity.

[`get_matches.py`](get_matches.py) also provides `CLI` access to the function. See `python get_matches.py --help` for more details.

### API

The API is implemented in `python` using the `FastAPI` framework. On startup, it loads the average hashes from the JSON file into memory. Then, for each request, it provides this data to the above-mentioned `get_matches_from_data` function and collects the result. Before returning the `JSON` result to the client, it enriches the similar ordinals data with additional useful properties or links.

*NOTE: The API actually calls the `Rust` API, which provides much better performance. See the `Rust server` section for more details.*

The API includes multiple endpoints for similarity searches, which are defined in  [`api.py`](api.py):

- `GET /ord_id/{ord_id}?top_n=N`
  - Returns the top N similar ordinal pictures for the given ordinal picture ID.
  - The maximum value for `top_n` is 20, and it is optional. If not specified, it defaults to 20.
- `POST /file?top_n=N`
  - Returns the top N similar ordinal pictures for the uploaded ordinal picture, which should be included as a "file" form-data argument.
  - Example usage:  `curl -X POST -H "Content-Type: multipart/form-data" -F "file=@images/1.jpg" http://localhost:8001/file?top_n=10` 
  - `top_n` is unlimited in this case, and is optional. If not specified, it defaults to 20.


### Rust bin/lib

For improved performance, the `get_matches` functionality has also been implemented in `Rust`, to speed up the similarity search.

[`similar_pictures`](similar_pictures) contains a `Rust` binary and library for this purpose.

The connection to `Rust` from `python` is established in [`get_matches_rust.py`](get_matches_rust.py), which exposes the same `CLI` interface as [`get_matches.py`](get_matches.py). This connection is made possible by a `Rust` shared library, residing under [`similar_pictures/target/release/libsimilar_pictures.so`](similar_pictures/target/release/libsimilar_pictures.so).

Additionally, a standalone `Rust` binary acting as `CLI` is created, under [`similar_pictures/target/release/similar_pictures`](similar_pictures/target/release/similar_pictures). `CLI` help can be seen by running `./similar_pictures/target/release/similar_pictures --help`. Its usage is similar to the `python` version.

Both the `Rust` library and binary utilize the common `get_matches` function from [`similar_pictures/src/get_matches.rs`](similar_pictures/src/get_matches.rs), which performs the same task as its `python` version.
To build the Rust binary and library for your operating system, run  `cargo build --release`.


### Rust server

The approach with loading the average hashes into memory on server startup to serve requests much faster was also replicated in `Rust` - in [`rust_http_server`](rust_http_server).

It contains a (nonpublic) server with similar endpoints as the `python` API - the only difference is that it does not accept file object, it needs to be given a file_hash directly.

It should not be used directly, but rather as a backend for the `python` API. The connection is being established in [`rust_server.py`](rust_server.py).
