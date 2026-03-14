use crate::utils::config;
use anyhow::Result;
use colored::*;

pub fn run() -> Result<()> {
    let registry = config::read_registry()?;
    let repos = config::get_all_repos_from(&registry);

    if repos.is_empty() {
        println!("{}", "No installed extensions".cyan());
        return Ok(());
    }

    for repo in repos {
        let info = config::get_repo_from(&registry, &repo);
        let version = info
            .and_then(|item| item.active_version.as_deref())
            .unwrap_or("unknown");
        let load_path = config::get_current_path(&repo)?;
        println!("{} {}", repo, version.dimmed());
        println!("  {}", load_path.display().to_string().cyan());
    }

    Ok(())
}
