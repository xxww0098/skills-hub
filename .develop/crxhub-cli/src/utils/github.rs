use anyhow::{Context, Result};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;
use std::process::{Child, Command, ExitStatus, Output, Stdio};
use std::time::Duration;
use std::{collections::HashSet, fmt};
use wait_timeout::ChildExt;

const GH_TIMEOUT: Duration = Duration::from_secs(30);

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ReleaseRequest {
    Latest,
    Tag(String),
}

impl ReleaseRequest {
    pub fn latest() -> Self {
        Self::Latest
    }

    pub fn tag(tag: impl Into<String>) -> Self {
        Self::Tag(tag.into())
    }
}

impl fmt::Display for ReleaseRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ReleaseRequest::Latest => write!(f, "latest"),
            ReleaseRequest::Tag(tag) => write!(f, "{tag}"),
        }
    }
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Release {
    pub tag_name: String,
    pub assets: Vec<Asset>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Asset {
    pub name: String,
    pub digest: Option<String>,
}

fn spawn_gh_capture(args: &[&str]) -> Result<Child> {
    Command::new("gh")
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .context("GitHub CLI (`gh`) is required. Install it from https://cli.github.com/")
}

fn kill_timed_out(mut child: Child, description: &str) -> anyhow::Error {
    let _ = child.kill();
    let _ = child.wait();
    anyhow::anyhow!(
        "GitHub CLI timed out after {} seconds while running `{}`",
        GH_TIMEOUT.as_secs(),
        description
    )
}

fn wait_for_output(mut child: Child, description: &str) -> Result<Output> {
    match child
        .wait_timeout(GH_TIMEOUT)
        .context("Failed while waiting for GitHub CLI")?
    {
        Some(_) => child
            .wait_with_output()
            .context("Failed to collect GitHub CLI output"),
        None => Err(kill_timed_out(child, description)),
    }
}

fn wait_for_status(mut child: Child, description: &str) -> Result<ExitStatus> {
    match child
        .wait_timeout(GH_TIMEOUT)
        .context("Failed while waiting for GitHub CLI")?
    {
        Some(status) => Ok(status),
        None => Err(kill_timed_out(child, description)),
    }
}

fn run_gh(args: &[&str]) -> Result<Vec<u8>> {
    let description = format!("gh {}", args.join(" "));
    let output = wait_for_output(spawn_gh_capture(args)?, &description)?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        if stderr.contains("authentication required") || stderr.contains("not logged into") {
            anyhow::bail!("GitHub CLI is not authenticated. Run: gh auth login");
        }

        anyhow::bail!("GitHub CLI error: {}", stderr);
    }

    Ok(output.stdout)
}

pub fn get_latest_release(repo_key: &str) -> Result<Release> {
    let output = run_gh(&[
        "release",
        "view",
        "--repo",
        repo_key,
        "--json",
        "tagName,assets",
    ])?;

    let release: Release =
        serde_json::from_slice(&output).context("Failed to parse release JSON")?;
    Ok(release)
}

pub fn get_release(repo_key: &str, tag: &str) -> Result<Release> {
    let output = run_gh(&[
        "release",
        "view",
        tag,
        "--repo",
        repo_key,
        "--json",
        "tagName,assets",
    ])?;

    let release: Release =
        serde_json::from_slice(&output).context("Failed to parse release JSON")?;
    Ok(release)
}

fn is_release_not_found_error(err: &anyhow::Error) -> bool {
    let message = err.to_string();
    message.contains("release not found") || message.contains("HTTP 404")
}

pub fn resolve_release(repo_key: &str, request: &ReleaseRequest) -> Result<Release> {
    match request {
        ReleaseRequest::Latest => get_latest_release(repo_key),
        ReleaseRequest::Tag(requested) => {
            let requested = requested.trim();
            let mut candidates = Vec::new();
            let mut seen = HashSet::new();

            for candidate in [
                requested.to_string(),
                format!("v{}", requested.trim_start_matches('v')),
                requested.trim_start_matches('v').to_string(),
            ] {
                if !candidate.is_empty() && seen.insert(candidate.clone()) {
                    candidates.push(candidate);
                }
            }

            for candidate in candidates {
                match get_release(repo_key, &candidate) {
                    Ok(release) => return Ok(release),
                    Err(err) if is_release_not_found_error(&err) => {}
                    Err(err) => return Err(err),
                }
            }

            anyhow::bail!(
                "Release '{}' not found in {}. Use the exact tag shown on GitHub Releases",
                requested,
                repo_key
            );
        }
    }
}

pub fn download_release_asset(
    repo_key: &str,
    tag: &str,
    asset_name: &str,
    dest_dir: &std::path::Path,
) -> Result<()> {
    let description = format!(
        "gh release download {} --repo {} -p {}",
        tag, repo_key, asset_name
    );
    let child = Command::new("gh")
        .args([
            "release",
            "download",
            tag,
            "--repo",
            repo_key,
            "-p",
            asset_name,
            "-D",
            &dest_dir.to_string_lossy(),
            "--clobber",
        ])
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .spawn()
        .context("Failed to execute gh download command")?;
    let status = wait_for_status(child, &description)?;

    if !status.success() {
        anyhow::bail!(
            "Failed to download asset '{}' from {} {}",
            asset_name,
            repo_key,
            tag
        );
    }

    Ok(())
}

pub fn verify_downloaded_asset(asset: &Asset, dest_dir: &Path) -> Result<()> {
    let Some(expected) = asset.digest.as_deref() else {
        return Ok(());
    };

    let Some(expected_sha256) = expected.strip_prefix("sha256:") else {
        return Ok(());
    };

    let asset_path = dest_dir.join(&asset.name);
    let mut file = fs::File::open(&asset_path)
        .with_context(|| format!("Downloaded asset missing at {}", asset_path.display()))?;
    let mut hasher = Sha256::new();
    std::io::copy(&mut file, &mut hasher)?;

    let actual_sha256 = hex::encode(hasher.finalize());
    if actual_sha256 != expected_sha256 {
        anyhow::bail!(
            "Digest mismatch for {}: expected sha256:{}, got sha256:{}",
            asset.name,
            expected_sha256,
            actual_sha256
        );
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{verify_downloaded_asset, Asset};
    use sha2::{Digest, Sha256};
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn verifies_matching_sha256_digest() {
        let temp = tempdir().unwrap();
        let asset_path = temp.path().join("extension.zip");
        fs::write(&asset_path, b"hello extension").unwrap();

        let digest = hex::encode(Sha256::digest(b"hello extension"));
        let asset = Asset {
            name: "extension.zip".to_string(),
            digest: Some(format!("sha256:{digest}")),
        };

        verify_downloaded_asset(&asset, temp.path()).unwrap();
    }

    #[test]
    fn rejects_mismatched_sha256_digest() {
        let temp = tempdir().unwrap();
        let asset_path = temp.path().join("extension.zip");
        fs::write(&asset_path, b"hello extension").unwrap();

        let asset = Asset {
            name: "extension.zip".to_string(),
            digest: Some("sha256:deadbeef".to_string()),
        };

        let err = verify_downloaded_asset(&asset, temp.path()).unwrap_err();
        assert!(err.to_string().contains("Digest mismatch"));
    }
}
