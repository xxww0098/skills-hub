use crate::utils::{config, extension, repo};
use anyhow::{Context, Result};
use colored::*;

pub fn run(repo_input: &str) -> Result<()> {
    let repo_key = repo::normalize_repo(repo_input)?;
    let info = config::get_repo(&repo_key)?
        .with_context(|| format!("{} is not installed. Run: crx install {}", repo_key, repo_key))?;

    let version = info.active_version.as_deref().unwrap_or("unknown");
    println!("{} {}", repo_key.bold(), version.dimmed());

    if let Some(pattern) = &info.asset_pattern {
        println!("  Asset pattern: {}", pattern);
    }

    if let Some(ext_id) = &info.ext_id {
        println!("  Extension ID:  {}", ext_id);
    }

    let current_path = config::get_current_path(&repo_key)?;
    let path_status = if current_path.join("manifest.json").exists() {
        "✓".green().to_string()
    } else {
        "✗ broken".red().to_string()
    };
    println!(
        "  Load path:     {} [{}]",
        current_path.display(),
        path_status
    );

    if let Some(checked) = &info.last_checked {
        println!("  Last checked:  {}", checked.format("%Y-%m-%d %H:%M UTC"));
    }

    let versions = extension::get_local_versions(&repo_key)?;
    if !versions.is_empty() {
        println!(
            "  Cached:        {} version(s): {}",
            versions.len(),
            versions.join(", ")
        );
    }

    // Disk size
    let repo_path = config::get_repo_path(&repo_key, None)?;
    if repo_path.exists() {
        let size = dir_size(&repo_path);
        println!("  Disk usage:    {}", format_size(size));
    }

    Ok(())
}

fn dir_size(path: &std::path::Path) -> u64 {
    walkdir::WalkDir::new(path)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .filter_map(|e| e.metadata().ok())
        .map(|m| m.len())
        .sum()
}

fn format_size(bytes: u64) -> String {
    const KB: u64 = 1024;
    const MB: u64 = 1024 * KB;

    if bytes >= MB {
        format!("{:.1} MB", bytes as f64 / MB as f64)
    } else if bytes >= KB {
        format!("{:.1} KB", bytes as f64 / KB as f64)
    } else {
        format!("{} B", bytes)
    }
}
