use super::repo_check::parallel_check_repos;
use crate::utils::{config, github, repo};
use anyhow::{Context, Result};
use colored::*;

enum RepoStatus {
    UpToDate {
        local_tag: String,
    },
    Outdated {
        local_tag: String,
        remote_tag: String,
    },
}

fn check_repo(repo: &str, current: config::RepoInfo) -> Result<RepoStatus> {
    let local_tag = current.active_version.context("No active version found")?;
    let remote_tag = github::get_latest_release(repo)?.tag_name;

    if remote_tag == local_tag {
        return Ok(RepoStatus::UpToDate { local_tag });
    }

    Ok(RepoStatus::Outdated {
        local_tag,
        remote_tag,
    })
}

pub fn run(repo: &str) -> Result<()> {
    let repo = repo::normalize_repo(repo)?;
    let registry = config::read_registry()?;
    let current = config::get_repo_from(&registry, &repo)
        .cloned()
        .with_context(|| format!("{} not installed. Run: crx install {}", repo, repo))?;

    println!("{}", format!("Checking for updates: {}...", repo).cyan());

    match check_repo(&repo, current)? {
        RepoStatus::Outdated {
            local_tag,
            remote_tag,
        } => {
            println!(
                "{}",
                format!("Update available: {} {} → {}", repo, local_tag, remote_tag).yellow()
            );
        }
        RepoStatus::UpToDate { local_tag } => {
            println!(
                "{}",
                format!("✓ {} is up to date ({})", repo, local_tag).green()
            );
        }
    }

    Ok(())
}

pub fn run_all() -> Result<()> {
    let registry = config::read_registry()?;
    let repos = config::get_all_repos_from(&registry);

    if repos.is_empty() {
        println!("{}", "No installed extensions".yellow());
        return Ok(());
    }

    println!(
        "{}",
        format!("Checking {} extension(s) for updates...\n", repos.len()).cyan()
    );

    let mut outdated = Vec::new();

    let checks = parallel_check_repos(
        &registry,
        &repos,
        "outdate check thread panicked",
        check_repo,
    );

    for (repo, result) in checks {
        match result {
            Ok(RepoStatus::Outdated {
                local_tag,
                remote_tag,
            }) => {
                outdated.push((repo, local_tag, remote_tag));
            }
            Ok(RepoStatus::UpToDate { .. }) => {}
            Err(err) => eprintln!("{}", format!("error: {err:#}").red()),
        }
    }

    if outdated.is_empty() {
        println!("{}", "✓ All installed extensions are up to date".green());
        return Ok(());
    }

    for (repo, local_tag, remote_tag) in outdated {
        println!(
            "{}",
            format!("{} {} → {}", repo, local_tag, remote_tag).yellow()
        );
    }

    Ok(())
}
