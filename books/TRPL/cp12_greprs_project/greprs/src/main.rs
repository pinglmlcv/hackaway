extern crate greprs;

use std::env;
use std::process;
use std::io::Write;

use greprs::Config;

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut stderr = std::io::stderr();

    let config = Config::new(&args).unwrap_or_else(|err| {
        writeln!(
            &mut stderr,
            "Problem parsing arguments: {}", 
            err
        ).expect("Could not write to stderr");
        process::exit(1);
    });

    if let Err(e) = greprs::run(config) {
        // new way to print error!
        eprintln!("Application error: {}", e);
        process::exit(1);
    }
}