use crate::utils::{config, extension, github, repo};
use anyhow::{bail, Result};
use colored::*;
use dialoguer::{theme::ColorfulTheme, Select};
use glob::Pattern;
use std::fs;
use std::io::IsTerminal;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use tempfile::Builder;

static AUTO_CONFIRM: AtomicBool = AtomicBool::new(false);

const ASSET_SCORE_SUFFIX_RULES: &[(&str, i32)] = &[(".crx", 100)];
const ASSET_SCORE_CONTAINS_RULES: &[(&str, i32)] = &[
    ("edge", 40),
    ("chrome", 30),
    ("chromium", 30),
    ("mv3", 10),
    ("manifestv3", 10),
];
const ASSET_SCORE_PENALTY_RULES: &[(&str, i32)] = &[
    ("firefox", -40),
    ("thunderbird", -40),
    ("safari", -40),
    ("opera", -40),
];

pub fn set_auto_confirm(enabled: bool) {
    AUTO_CONFIRM.store(enabled, Ordering::Relaxed);
}

fn is_supported_asset(name: &str) -> bool {
    let name = name.to_ascii_lowercase();
    name.ends_with(".crx") || name.ends_with(".zip")
}

fn asset_score(name: &str) -> i32 {
    let name = name.to_ascii_lowercase();
    ASSET_SCORE_SUFFIX_RULES
        .iter()
        .filter(|(pattern, _)| name.ends_with(pattern))
        .chain(
            ASSET_SCORE_CONTAINS_RULES
                .iter()
                .filter(|(pattern, _)| name.contains(pattern)),
        )
        .chain(
            ASSET_SCORE_PENALTY_RULES
                .iter()
                .filter(|(pattern, _)| name.contains(pattern)),
        )
        .map(|(_, weight)| *weight)
        .sum()
}

fn match_asset(name: &str, selector: &str) -> bool {
    if selector.contains('*') || selector.contains('?') || selector.contains('[') {
        Pattern::new(selector)
            .map(|pattern| pattern.matches(name))
            .unwrap_or(false)
    } else {
        name.eq_ignore_ascii_case(selector)
    }
}

fn choose_asset_interactively(
    candidates: Vec<github::Asset>,
    prompt: &str,
) -> Result<github::Asset> {
    if AUTO_CONFIRM.load(Ordering::Relaxed) {
        return Ok(candidates
            .into_iter()
            .next()
            .expect("interactive asset selection always has at least one candidate"));
    }

    if !std::io::stdin().is_terminal() {
        let available = candidates
            .iter()
            .map(|asset| format!("  - {}", asset.name))
            .collect::<Vec<_>>()
            .join("\n");
        bail!("{prompt}\n{available}");
    }

    let items = candidates
        .iter()
        .map(|asset| asset.name.as_str())
        .collect::<Vec<_>>();

    let selection = Select::with_theme(&ColorfulTheme::default())
        .with_prompt(prompt)
        .items(&items)
        .default(0)
        .interact()?;

    Ok(candidates
        .into_iter()
        .nth(selection)
        .expect("dialoguer selection is always within bounds"))
}

struct ScopedBackup {
    dest: PathBuf,
    backup_dest: PathBuf,
    had_previous_archive: bool,
    armed: bool,
}

impl ScopedBackup {
    fn new(dest: PathBuf, backup_dest: PathBuf, had_previous_archive: bool) -> Self {
        Self {
            dest,
            backup_dest,
            had_previous_archive,
            armed: true,
        }
    }

    fn disarm(&mut self) {
        self.armed = false;
    }
}

impl Drop for ScopedBackup {
    fn drop(&mut self) {
        if !self.armed {
            return;
        }

        let _ = fs::remove_dir_all(&self.dest);
        if self.had_previous_archive && self.backup_dest.exists() {
            let _ = fs::rename(&self.backup_dest, &self.dest);
        }
    }
}

fn resolve_asset(release: &github::Release, selector: Option<&str>) -> Result<github::Asset> {
    let supported = release
        .assets
        .iter()
        .filter(|asset| is_supported_asset(&asset.name))
        .cloned()
        .collect::<Vec<_>>();

    if supported.is_empty() {
        bail!(
            "No supported assets found in {}. Expected a .crx or .zip release asset",
            release.tag_name
        );
    }

    if let Some(selector) = selector {
        let matches = supported
            .iter()
            .filter(|asset| match_asset(&asset.name, selector))
            .cloned()
            .collect::<Vec<_>>();

        return match matches.len() {
            0 => {
                let available = supported
                    .iter()
                    .map(|asset| format!("  - {}", asset.name))
                    .collect::<Vec<_>>()
                    .join("\n");
                bail!(
                    "No assets matched '{}'. Available assets:\n{}",
                    selector,
                    available
                );
            }
            1 => Ok(matches
                .into_iter()
                .next()
                .expect("single matching asset must exist")),
            _ => choose_asset_interactively(matches, "Multiple assets matched. Pick one"),
        };
    }

    if supported.len() == 1 {
        return Ok(supported
            .into_iter()
            .next()
            .expect("single supported asset must exist"));
    }

    let mut ranked = supported
        .into_iter()
        .map(|asset| (asset_score(&asset.name), asset))
        .collect::<Vec<_>>();
    ranked.sort_by(|a, b| b.0.cmp(&a.0));

    if let Some((top_score, _)) = ranked.first() {
        let tied_count = ranked
            .iter()
            .take_while(|(score, _)| score == top_score)
            .count();
        if *top_score > 0 && tied_count == 1 {
            return Ok(ranked
                .into_iter()
                .next()
                .expect("ranked assets must not be empty")
                .1);
        }
    }

    let ranked_assets = ranked
        .into_iter()
        .map(|(_, asset)| asset)
        .collect::<Vec<_>>();
    choose_asset_interactively(ranked_assets, "Multiple browser assets found. Pick one")
}

pub fn run_with_target(
    repo: &str,
    pattern: Option<String>,
    request: github::ReleaseRequest,
) -> Result<()> {
    let repo = repo::normalize_repo(repo)?;
    let selector = pattern.filter(|value| !value.trim().is_empty());

    println!(
        "{}",
        match &request {
            github::ReleaseRequest::Latest => format!("Fetching release info for {}...", repo),
            github::ReleaseRequest::Tag(tag) => {
                format!("Fetching release info for {} ({})...", repo, tag)
            }
        }
        .cyan()
    );

    let release = github::resolve_release(&repo, &request)?;
    run_with_release(&repo, selector, release)
}

pub fn run_with_release(
    repo: &str,
    pattern: Option<String>,
    release: github::Release,
) -> Result<()> {
    let selector = pattern.filter(|value| !value.trim().is_empty());
    let current_path = config::get_current_path(repo)?;
    let already_loaded = current_path.exists();
    let repo_root = config::get_repo_path(repo, None)?;
    config::ensure_dir(repo_root.as_path())?;

    let asset = resolve_asset(&release, selector.as_deref())?;
    let tag = release.tag_name;
    println!(
        "{}",
        format!("Found {} {} ({})", repo, tag, asset.name).cyan()
    );

    let staging_root = Builder::new().prefix(".install-").tempdir_in(&repo_root)?;
    let staged_dest = staging_root.path().join("version");
    config::ensure_dir(staged_dest.as_path())?;

    println!("{}", "Downloading...".cyan());
    github::download_release_asset(&repo, &tag, &asset.name, &staged_dest)?;
    println!("{}", "Verifying download...".cyan());
    github::verify_downloaded_asset(&asset, &staged_dest)?;

    println!("{}", "Unpacking...".cyan());
    extension::unpack_extension(&staged_dest)?;

    println!("{}", "Inspecting extension...".cyan());
    let ext_info = extension::get_extension_info(&staged_dest)?;
    println!(
        "{}",
        format!(
            "Detected extension: {} ({})",
            ext_info.manifest.name, ext_info.manifest.version
        )
        .cyan()
    );

    let dest = config::get_repo_path(repo, Some(&tag))?;
    let backup_root = Builder::new().prefix(".backup-").tempdir_in(&repo_root)?;
    let backup_dest = backup_root.path().join("version");
    let had_previous_archive = dest.exists();
    if had_previous_archive {
        fs::rename(&dest, &backup_dest)?;
    }
    let mut backup = ScopedBackup::new(dest.clone(), backup_dest, had_previous_archive);

    fs::rename(&staged_dest, &dest)?;
    let final_ext_info = extension::get_extension_info(&dest)?;

    println!("{}", "Updating stable load path...".cyan());
    extension::replace_extension_root(&final_ext_info.root, &current_path)?;
    backup.disarm();

    let repo_info = config::RepoInfo {
        active_version: Some(tag.clone()),
        asset_pattern: selector,
        ext_id: final_ext_info.id,
        ext_root: Some(current_path.clone()),
        last_checked: Some(chrono::Utc::now()),
    };

    config::update_repo(repo, repo_info)?;

    println!(
        "{}",
        format!("\n✓ {} {} installed successfully", repo, tag).green()
    );
    println!(
        "{}",
        format!("  Stable load path: {}", current_path.display()).cyan()
    );
    if already_loaded {
        println!(
            "{}",
            "  Browser path is unchanged. Reload the extension or restart the browser to pick up the new files."
                .cyan()
        );
    } else {
        println!(
            "{}",
            "  Load this folder once from your browser's extensions page. Future installs and updates will replace these files automatically."
                .cyan()
        );
    }

    Ok(())
}
