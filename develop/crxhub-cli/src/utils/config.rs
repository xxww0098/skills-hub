use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use fs2::FileExt;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::{self, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

use crate::utils::repo;

#[derive(Debug, Serialize, Deserialize, Default, Clone)]
pub struct Registry {
    pub repos: HashMap<String, RepoInfo>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RepoInfo {
    pub active_version: Option<String>,
    pub asset_pattern: Option<String>,
    pub ext_id: Option<String>,
    pub ext_root: Option<PathBuf>,
    pub last_checked: Option<DateTime<Utc>>,
}

pub fn get_crxhub_home() -> Result<PathBuf> {
    let home_dir = dirs::home_dir().context("Cannot find home directory")?;
    Ok(home_dir.join(".crxhub-cli"))
}

pub fn get_registry_path() -> Result<PathBuf> {
    Ok(get_crxhub_home()?.join("registry.json"))
}

pub fn get_extensions_dir() -> Result<PathBuf> {
    Ok(get_crxhub_home()?.join("extensions"))
}

pub fn get_repo_path(repo_key: &str, tag: Option<&str>) -> Result<PathBuf> {
    let (owner, repo_name) = repo::split_repo_key(repo_key)?;

    let base = get_extensions_dir()?.join(owner).join(repo_name);
    Ok(match tag {
        Some(t) => base.join(t),
        None => base,
    })
}

pub fn get_current_path(repo_key: &str) -> Result<PathBuf> {
    Ok(get_repo_path(repo_key, None)?.join("current"))
}

pub fn ensure_dir(path: &Path) -> Result<()> {
    if !path.exists() {
        fs::create_dir_all(path)?;
    }
    Ok(())
}

fn open_registry_file() -> Result<(PathBuf, fs::File)> {
    let path = get_registry_path()?;
    let parent = path
        .parent()
        .context("Registry path has no parent directory")?;
    ensure_dir(parent)?;

    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .open(&path)
        .with_context(|| format!("Failed to open registry at {:?}", path))?;

    Ok((path, file))
}

fn read_registry_from_file(file: &mut fs::File, path: &Path) -> Result<Registry> {
    file.seek(SeekFrom::Start(0))?;

    let mut content = String::new();
    file.read_to_string(&mut content)
        .with_context(|| format!("Failed to read registry from {:?}", path))?;

    if content.trim().is_empty() {
        return Ok(Registry::default());
    }

    let registry: Registry =
        serde_json::from_str(&content).with_context(|| "Failed to parse registry JSON")?;

    Ok(registry)
}

fn write_registry_to_file(file: &mut fs::File, path: &Path, registry: &Registry) -> Result<()> {
    let content = serde_json::to_string_pretty(registry)?;
    file.set_len(0)?;
    file.seek(SeekFrom::Start(0))?;
    file.write_all(content.as_bytes())
        .with_context(|| format!("Failed to write registry to {:?}", path))?;
    file.sync_all()
        .with_context(|| format!("Failed to flush registry to {:?}", path))?;

    Ok(())
}

fn with_registry_lock<T, F>(exclusive: bool, mut f: F) -> Result<T>
where
    F: FnMut(&mut Registry) -> Result<T>,
{
    let (path, mut file) = open_registry_file()?;

    if exclusive {
        file.lock_exclusive()
            .with_context(|| format!("Failed to lock registry at {:?}", path))?;
    } else {
        file.lock_shared()
            .with_context(|| format!("Failed to lock registry at {:?}", path))?;
    }

    let mut registry = read_registry_from_file(&mut file, &path)?;
    let result = f(&mut registry)?;

    if exclusive {
        write_registry_to_file(&mut file, &path, &registry)?;
    }

    Ok(result)
}

pub fn read_registry() -> Result<Registry> {
    with_registry_lock(false, |registry| Ok(registry.clone()))
}

pub fn get_repo_from<'a>(registry: &'a Registry, repo_key: &str) -> Option<&'a RepoInfo> {
    registry.repos.get(repo_key)
}

pub fn get_all_repos_from(registry: &Registry) -> Vec<String> {
    let mut repos = registry.repos.keys().cloned().collect::<Vec<_>>();
    repos.sort_unstable();
    repos
}

pub fn get_repo(repo_key: &str) -> Result<Option<RepoInfo>> {
    let registry = read_registry()?;
    Ok(get_repo_from(&registry, repo_key).cloned())
}

pub fn update_repo(repo_key: &str, info: RepoInfo) -> Result<()> {
    let mut info = Some(info);
    with_registry_lock(true, |registry| {
        registry.repos.insert(
            repo_key.to_string(),
            info.take()
                .expect("registry update closure should only run once"),
        );
        Ok(())
    })?;
    Ok(())
}

pub fn remove_repo(repo_key: &str) -> Result<()> {
    with_registry_lock(true, |registry| {
        registry.repos.remove(repo_key);
        Ok(())
    })?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{get_crxhub_home, get_current_path, get_extensions_dir, get_repo_path};

    #[test]
    fn crxhub_home_uses_hidden_dir_in_user_home() {
        assert_eq!(
            get_crxhub_home()
                .unwrap()
                .file_name()
                .and_then(|name| name.to_str()),
            Some(".crxhub-cli")
        );
    }

    #[test]
    fn repo_path_is_versioned_under_crxhub_extensions() {
        let path = get_repo_path("alibaba/page-agent", Some("v1.5.7")).unwrap();

        assert!(path.starts_with(get_extensions_dir().unwrap()));
        assert_eq!(
            path.file_name().and_then(|name| name.to_str()),
            Some("v1.5.7")
        );
        assert_eq!(
            path.parent()
                .and_then(|path| path.file_name())
                .and_then(|name| name.to_str()),
            Some("page-agent")
        );
        assert_eq!(
            path.parent()
                .and_then(|path| path.parent())
                .and_then(|path| path.file_name())
                .and_then(|name| name.to_str()),
            Some("alibaba")
        );
    }

    #[test]
    fn current_path_is_stable_under_repo_directory() {
        let path = get_current_path("alibaba/page-agent").unwrap();

        assert!(path.starts_with(get_extensions_dir().unwrap()));
        assert_eq!(
            path.file_name().and_then(|name| name.to_str()),
            Some("current")
        );
        assert_eq!(
            path.parent()
                .and_then(|path| path.file_name())
                .and_then(|name| name.to_str()),
            Some("page-agent")
        );
    }
}
