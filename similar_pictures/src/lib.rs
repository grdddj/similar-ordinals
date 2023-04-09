use std::ffi::{CStr, CString};
use std::os::raw::c_char;

mod get_matches;
use get_matches::get_matches;

#[no_mangle]
pub unsafe extern "C" fn get_matches_c(file_path: *const c_char, file_hash: *const c_char) -> *mut c_char {
    let file_path = unsafe { CStr::from_ptr(file_path).to_str().expect("Invalid file path string") };
    let file_hash = unsafe { CStr::from_ptr(file_hash).to_str().expect("Invalid file hash string") };

    let json_output = get_matches(file_path, file_hash);
    let c_string = CString::new(json_output).unwrap();
    c_string.into_raw()
}
