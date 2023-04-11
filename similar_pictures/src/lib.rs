use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int};

mod get_matches;
use get_matches::get_matches;

#[no_mangle]
/// # Safety
/// 
/// This function is unsafe because it dereferences raw pointers.
pub unsafe extern "C" fn get_matches_c(json_file: *const c_char, ord_id: *const c_char, file_hash: *const c_char, top_n: c_int) -> *mut c_char {
    let json_file = unsafe { CStr::from_ptr(json_file).to_str().expect("Invalid json file string") };
    let ord_id = unsafe { CStr::from_ptr(ord_id).to_str().expect("Invalid ord ID string") };
    let file_hash = unsafe { CStr::from_ptr(file_hash).to_str().expect("Invalid file hash string") };
    let top_n = top_n as usize;

    let ord_id = if ord_id.is_empty() { None } else { Some(ord_id.to_string()) };
    let file_hash = if file_hash.is_empty() { None } else { Some(file_hash.to_string()) };

    let json_output = get_matches(json_file.to_string(), ord_id, file_hash, top_n);
    let c_string = CString::new(json_output).unwrap();
    c_string.into_raw()
}
