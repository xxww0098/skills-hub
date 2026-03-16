use super::repo_check::parallel_check_repos;
use crate::utils::{config, extension, github, repo};
use anyhow::{Context, Result};
use chrono::Utc;
use colored::*;

fn normalize_request(target: Option<&str>) -> Result<github::ReleaseRequest> {
    let Some(target) = target else {
        return Ok(github::ReleaseRequest::latest());
    };

    let target = target.trim();
    if target.is_empty() {
        anyhow::bail!("Release selector cannot be empty");
    }

    if target.eq_ignore_ascii_case("latest") {
        return Ok(github::ReleaseRequest::latest());
    }

    Ok(github::ReleaseRequest::tag(target))
}

fn repair_stable_load_path(repo: &str, current: &config::RepoInfo) -> Result<bool> {
    let current_path = config::get_current_path(repo)?;
    let manifest_ok = current_path.join("manifest.json").exists();
    let recorded_root_ok = current.ext_root.as_deref() == Some(current_path.as_path());

    if manifest_ok && recorded_root_ok {
        return Ok(false);
    }

    let active_tag = current
        .active_version
        .as_deref()
        .context("No active version found")?;
    let cached_version_path = config::get_repo_path(repo, Some(active_tag))?;
    if !cached_version_path.exists() {
        anyhow::bail!(
            "Stable load path is missing and cached files for {} were not found. Re-run: crx install {}",
            active_tag,
            repo
        );
    }

    let ext_info = extension::get_extension_info(&cached_version_path)?;
    extension::replace_extension_root(&ext_info.root, &current_path)?;

    let repaired = config::RepoInfo {
        active_version: Some(active_tag.to_string()),
        asset_pattern: current.asset_pattern.clone(),
        ext_id: ext_info.id,
        ext_root: Some(current_path.clone()),
        last_checked: Some(Utc::now()),
    };
    config::update_repo(repo, repaired)?;

    println!(
        "{}",
        format!("✓ Repaired stable load path: {}", current_path.display()).green()
    );
    Ok(true)
}

fn run_with_request(
    repo: &str,
    current: config::RepoInfo,
    request: github::ReleaseRequest,
    latest_release: Option<github::Release>,
) -> Result<()> {
    let local_tag = current
        .active_version
        .as_deref()
        .context("No active version found")?;

    match request {
        github::ReleaseRequest::Latest => {
            println!("{}", format!("Checking for updates: {}...", repo).cyan());

            let release = match latest_release {
                Some(release) => release,
                None => github::get_latest_release(repo)?,
            };
            let remote_tag = release.tag_name.as_str();

            if remote_tag == local_tag {
                let repaired = repair_stable_load_path(repo, &current)?;
                println!(
                    "{}",
                    format!(
                        "✓ {} is up to date ({}){}",
                        repo,
                        local_tag,
                        if repaired {
                            " and stable path was repaired"
                        } else {
                            ""
                        }
                    )
                    .green()
                );
                return Ok(());
            }

            println!(
                "{}",
                format!("Update available: {} → {}", local_tag, remote_tag).cyan()
            );

            super::install::run_with_release(repo, current.asset_pattern.clone(), release)?;
        }
        github::ReleaseRequest::Tag(requested_tag) => {
            let release =
                github::resolve_release(repo, &github::ReleaseRequest::Tag(requested_tag.clone()))?;
            let target_tag = release.tag_name.as_str();

            if target_tag == local_tag {
                let repaired = repair_stable_load_path(repo, &current)?;
                println!(
                    "{}",
                    format!(
                        "✓ {} is already on {}{}",
                        repo,
                        target_tag,
                        if repaired {
                            " and stable path was repaired"
                        } else {
                            ""
                        }
                    )
                    .green()
                );
                return Ok(());
            }

            println!(
                "{}",
                format!(
                    "Switching {}: {} → {} (requested {})",
                    repo, local_tag, target_tag, requested_tag
                )
                .cyan()
            );

            super::install::run_with_release(repo, current.asset_pattern.clone(), release)?;
        }
    }

    super::cleanup::run(repo, 3)?;
    Ok(())
}

fn run_with_current(repo: &str, current: config::RepoInfo, target: Option<&str>) -> Result<()> {
    let request = normalize_request(target)?;
    run_with_request(repo, current, request, None)
}

pub fn run(repo: &str, target: Option<&str>) -> Result<()> {
    let repo = repo::normalize_repo(repo)?;
    let current = config::get_repo(&repo)?
        .with_context(|| format!("{} not installed. Run: crx install {}", repo, repo))?;
    run_with_current(&repo, current, target)
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
        format!("Updating {} extension(s)...\n", repos.len()).cyan()
    );

    let checks = parallel_check_repos(
        &registry,
        &repos,
        "release check thread panicked",
        |repo, current| github::get_latest_release(repo).map(|release| (current, release)),
    );

    for (repo, result) in checks {
        println!("==> {}", repo);
        match result {
            Ok((current, release)) => {
                if let Err(err) = run_with_request(
                    &repo,
                    current,
                    github::ReleaseRequest::Latest,
                    Some(release),
                ) {
                    eprintln!("{}", format!("error: {err:#}").red());
                }
            }
            Err(err) => eprintln!("{}", format!("error: {err:#}").red()),
        }
        println!();
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::normalize_request;
    use crate::utils::github::ReleaseRequest;

    #[test]
    fn normalizes_latest_selector() {
        assert_eq!(normalize_request(None).unwrap(), ReleaseRequest::Latest);
        assert_eq!(
            normalize_request(Some("latest")).unwrap(),
            ReleaseRequest::Latest
        );
    }

    #[test]
    fn normalizes_version_selector() {
        assert_eq!(
            normalize_request(Some("1.5.6")).unwrap(),
            ReleaseRequest::Tag("1.5.6".to_string())
        );
        assert_eq!(
            normalize_request(Some("v1.5.6")).unwrap(),
            ReleaseRequest::Tag("v1.5.6".to_string())
        );
    }
}
