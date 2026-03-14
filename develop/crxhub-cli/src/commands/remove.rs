use crate::utils::{config, repo};
use anyhow::Result;
use colored::*;
use std::fs;

pub fn run(repo: &str) -> Result<()> {
    let repo = repo::normalize_repo(repo)?;

    let repo_path = config::get_repo_path(&repo, None)?;
    if repo_path.exists() {
        fs::remove_dir_all(&repo_path)?;
    }

    config::remove_repo(&repo)?;
    println!("{}", format!("✓ {} removed", repo).green());
    println!(
        "{}",
        "  If your browser still has this extension loaded, remove it from the browser extensions page."
            .cyan()
    );

    Ok(())
}
