use crate::utils::{config, extension, repo as repo_util};
use anyhow::Result;
use colored::*;
use std::fs;
use std::time::SystemTime;

fn version_modified_time(repo: &str, version: &str) -> SystemTime {
    let Ok(path) = config::get_repo_path(repo, Some(version)) else {
        return SystemTime::UNIX_EPOCH;
    };
    fs::metadata(path)
        .and_then(|metadata| metadata.modified())
        .unwrap_or(SystemTime::UNIX_EPOCH)
}

fn sort_versions_by_recency(repo: &str, versions: Vec<String>) -> Vec<String> {
    let mut versions = versions
        .into_iter()
        .map(|version| {
            let modified = version_modified_time(repo, &version);
            (version, modified)
        })
        .collect::<Vec<_>>();

    versions.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| b.0.cmp(&a.0)));
    versions.into_iter().map(|(version, _)| version).collect()
}

pub fn run(repo: &str, keep: usize) -> Result<()> {
    let local_info = config::get_repo(repo)?;
    let active_version = local_info
        .as_ref()
        .and_then(|i| i.active_version.as_deref());
    let versions = extension::get_local_versions(repo)?;

    let inactive: Vec<String> = versions
        .into_iter()
        .filter(|v| active_version != Some(v.as_str()))
        .collect();
    let keep_inactive = keep.saturating_sub(1); // 1 slot reserved for active

    if inactive.len() <= keep_inactive {
        return Ok(());
    }

    println!(
        "{}",
        format!(
            "  Active: {} | Keeping latest {}",
            active_version.unwrap_or("none"),
            keep
        )
        .dimmed()
    );

    let sorted = sort_versions_by_recency(repo, inactive);
    let mut deleted = 0usize;

    for v in sorted.iter().skip(keep_inactive) {
        let v_path = config::get_repo_path(repo, Some(v))?;
        fs::remove_dir_all(&v_path)?;
        println!("  🗑  {} deleted", v);
        deleted += 1;
    }

    if deleted == 0 {
        println!("{}", "  Nothing to cleanup".dimmed());
    }

    Ok(())
}

pub fn run_single(repo: &str, keep: usize) -> Result<()> {
    let repo = repo_util::normalize_repo(repo)?;
    println!("==> {}", repo);
    run(&repo, keep)?;
    println!("{}", "✓ Cleanup complete".green());
    Ok(())
}

pub fn run_all(keep: usize) -> Result<()> {
    let registry = config::read_registry()?;
    let repos = config::get_all_repos_from(&registry);

    if repos.is_empty() {
        println!("{}", "No installed extensions".yellow());
        return Ok(());
    }

    let mut any_cleaned = false;

    for repo in &repos {
        let versions = extension::get_local_versions(repo)?;
        let active = config::get_repo_from(&registry, repo)
            .and_then(|i| i.active_version.as_deref());
        let removable_count = versions
            .iter()
            .filter(|v| active != Some(v.as_str()))
            .count();

        if versions.len() <= keep || removable_count == 0 {
            continue;
        }

        any_cleaned = true;
        println!("==> {}", repo);
        run(repo, keep)?;
    }

    if !any_cleaned {
        println!("{}", "✓ Nothing to cleanup — all extensions are clean".green());
    } else {
        println!("{}", "\n✓ Cleanup complete".green());
    }

    Ok(())
}
