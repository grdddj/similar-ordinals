## Ordinals pictures similarity

Project focusing on creating a service showing similar ordinals pictures.

Classifies all the pictures using `imagehash.average_hash` into a bit sequence of 0 and 1 and then compares them using `hamming distance` - how many bits are common for both pictures.

It contains a `Rust` binary and library for the purpose of quick similarity search - which is much quicker than using `python`.

Description of the `average hash` algorithm can be seed under [this link](https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html).
