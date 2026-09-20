use std::env;
use std::path::{Path, PathBuf};
use std::process::Command;

fn python_command() -> &'static str {
    for candidate in ["python", "python3"] {
        if Command::new(candidate)
            .arg("--version")
            .output()
            .is_ok_and(|output| output.status.success())
        {
            return candidate;
        }
    }
    panic!("Diet Rust integration requires Python 3.11 or newer");
}

fn main() {
    let project_root = PathBuf::from(
        env::var_os("CARGO_MANIFEST_DIR").expect("Cargo provides CARGO_MANIFEST_DIR"),
    );
    let output = Path::new(
        &env::var_os("OUT_DIR").expect("Cargo provides OUT_DIR for build scripts"),
    )
    .join("sorting_tasks.rs");
    let source = project_root.join("examples").join("sorting_tasks.dc");

    println!("cargo:rerun-if-changed={}", source.display());
    println!("cargo:rerun-if-changed=dietc");

    let status = Command::new(python_command())
        .args(["-m", "dietc"])
        .arg(&source)
        .arg("-o")
        .arg(&output)
        .current_dir(&project_root)
        .status()
        .expect("run the Diet Rust translator");

    assert!(status.success(), "Diet Rust translation failed");
}
