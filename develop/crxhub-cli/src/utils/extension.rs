use anyhow::{Context, Result};
use base64::{engine::general_purpose::STANDARD, Engine as _};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;
use zip::ZipArchive;

#[derive(Debug, Deserialize)]
pub struct Manifest {
    pub version: String,
    pub name: String,
    pub key: Option<String>,
    pub default_locale: Option<String>,
}

fn chrome_id_from_bytes(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    let result = hasher.finalize();
    let hex_str = hex::encode(&result[..16]);
    hex_str
        .chars()
        .map(|c| (b'a' + c.to_digit(16).unwrap_or(0) as u8) as char)
        .collect()
}

pub fn extension_id_from_manifest_key(key: &str) -> Result<String> {
    let compact_key: String = key.chars().filter(|ch| !ch.is_whitespace()).collect();
    let public_key = STANDARD
        .decode(compact_key)
        .context("manifest.key is not valid base64")?;
    Ok(chrome_id_from_bytes(&public_key))
}

pub fn unpack_extension(dest_dir: &Path) -> Result<PathBuf> {
    let entries = fs::read_dir(dest_dir).context("Failed to read destination directory")?;

    let mut crx_file: Option<PathBuf> = None;
    let mut zip_file: Option<PathBuf> = None;

    for entry in entries {
        let entry = entry?;
        let path = entry.path();
        if let Some(ext) = path.extension() {
            if ext == "crx" {
                crx_file = Some(path);
            } else if ext == "zip" {
                zip_file = Some(path);
            }
        }
    }

    let unpack_dir = dest_dir.join("unpacked");
    if unpack_dir.exists() {
        fs::remove_dir_all(&unpack_dir)?;
    }
    fs::create_dir_all(&unpack_dir)?;

    if let Some(crx) = crx_file {
        unpack_crx(&crx, &unpack_dir)?;
    } else if let Some(zip) = zip_file {
        unpack_zip(&zip, &unpack_dir)?;
    } else {
        anyhow::bail!("No .crx or .zip file found");
    }

    Ok(unpack_dir)
}

fn unpack_crx(crx_path: &Path, output_dir: &Path) -> Result<()> {
    let mut file = fs::File::open(crx_path)?;
    let mut header = [0u8; 12];
    file.read_exact(&mut header)?;

    let magic = std::str::from_utf8(&header[0..4])?;
    if magic != "Cr24" {
        anyhow::bail!("Invalid CRX file: magic={}", magic);
    }

    let version = u32::from_le_bytes([header[4], header[5], header[6], header[7]]);
    if version != 3 {
        anyhow::bail!("Unsupported CRX version: {}", version);
    }

    let header_len = u32::from_le_bytes([header[8], header[9], header[10], header[11]]) as u64;
    let zip_offset = 12 + header_len;
    let file_size = file.metadata()?.len();
    if zip_offset > file_size {
        anyhow::bail!("Invalid CRX header length: {}", header_len);
    }

    file.seek(SeekFrom::Start(zip_offset))?;
    unpack_zip_reader(file, output_dir)?;

    Ok(())
}

fn unpack_zip(zip_path: &Path, output_dir: &Path) -> Result<()> {
    let file = fs::File::open(zip_path)?;
    unpack_zip_reader(file, output_dir)
}

fn unpack_zip_reader<R>(reader: R, output_dir: &Path) -> Result<()>
where
    R: Read + Seek,
{
    let mut archive = ZipArchive::new(reader)?;

    for i in 0..archive.len() {
        let mut file = archive.by_index(i)?;
        let Some(safe_path) = file.enclosed_name().map(|path| path.to_path_buf()) else {
            continue;
        };
        let outpath = output_dir.join(safe_path);

        if file.name().ends_with('/') {
            fs::create_dir_all(&outpath)?;
        } else {
            if let Some(p) = outpath.parent() {
                if !p.exists() {
                    fs::create_dir_all(p)?;
                }
            }
            let mut outfile = fs::File::create(&outpath)?;
            std::io::copy(&mut file, &mut outfile)?;
        }
    }

    Ok(())
}

pub fn find_manifest_root(unpack_dir: &Path) -> Result<PathBuf> {
    let manifest_path = unpack_dir.join("manifest.json");
    if manifest_path.exists() {
        return Ok(unpack_dir.to_path_buf());
    }

    let mut candidates = Vec::new();
    for entry in WalkDir::new(unpack_dir).min_depth(1).max_depth(4) {
        let entry = entry?;
        if entry.file_type().is_file() && entry.file_name() == "manifest.json" {
            if let Some(parent) = entry.path().parent() {
                candidates.push(parent.to_path_buf());
            }
        }
    }

    candidates.sort_by_key(|path| path.components().count());
    candidates
        .into_iter()
        .next()
        .context("manifest.json not found in extracted extension")
}

pub fn get_extension_info(dest_dir: &Path) -> Result<ExtensionInfo> {
    let unpack_dir = dest_dir.join("unpacked");
    let ext_root = find_manifest_root(&unpack_dir)?;
    let manifest_path = ext_root.join("manifest.json");

    if !manifest_path.exists() {
        anyhow::bail!("manifest.json not found in extracted extension");
    }

    let manifest_content = fs::read_to_string(&manifest_path)?;
    let mut manifest: Manifest = serde_json::from_str(&manifest_content)?;

    manifest.name = resolve_i18n_field(&ext_root, &manifest.name, &manifest.default_locale);

    let id = manifest
        .key
        .as_deref()
        .map(extension_id_from_manifest_key)
        .transpose()?;

    Ok(ExtensionInfo {
        root: ext_root,
        manifest,
        id,
    })
}

fn resolve_i18n_field(ext_root: &Path, value: &str, default_locale: &Option<String>) -> String {
    let Some(msg_key) = value
        .strip_prefix("__MSG_")
        .and_then(|rest| rest.strip_suffix("__"))
    else {
        return value.to_string();
    };

    let locales_dir = ext_root.join("_locales");
    let mut candidates = vec!["en".to_string(), "en_US".to_string()];
    if let Some(locale) = default_locale {
        if !candidates.iter().any(|c| c.eq_ignore_ascii_case(locale)) {
            candidates.insert(0, locale.clone());
        }
    }

    for locale in &candidates {
        let messages_path = locales_dir.join(locale).join("messages.json");
        if let Ok(content) = fs::read_to_string(&messages_path) {
            if let Ok(messages) = serde_json::from_str::<std::collections::HashMap<String, I18nMessage>>(&content) {
                // Try exact key first, then case-insensitive
                if let Some(msg) = messages.get(msg_key) {
                    return msg.message.clone();
                }
                let key_lower = msg_key.to_ascii_lowercase();
                for (k, v) in &messages {
                    if k.to_ascii_lowercase() == key_lower {
                        return v.message.clone();
                    }
                }
            }
        }
    }

    value.to_string()
}

#[derive(Debug, Deserialize)]
struct I18nMessage {
    message: String,
}

#[derive(Debug)]
pub struct ExtensionInfo {
    pub root: PathBuf,
    pub manifest: Manifest,
    pub id: Option<String>,
}

pub fn get_local_versions(repo_key: &str) -> Result<Vec<String>> {
    use crate::utils::config;

    let repo_path = config::get_repo_path(repo_key, None)?;
    if !repo_path.exists() {
        return Ok(vec![]);
    }

    let mut versions = vec![];
    for entry in fs::read_dir(repo_path)? {
        let entry = entry?;
        let name = entry.file_name();
        let name_str = name.to_string_lossy();
        if entry.file_type()?.is_dir()
            && name_str != "latest"
            && name_str != "current"
            && !name_str.starts_with('.')
        {
            versions.push(name_str.to_string());
        }
    }

    versions.sort_unstable_by(|a, b| b.cmp(a));
    Ok(versions)
}

fn remove_path(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path)?;
    let file_type = metadata.file_type();

    if file_type.is_dir() && !file_type.is_symlink() {
        fs::remove_dir_all(path)?;
    } else {
        fs::remove_file(path)?;
    }

    Ok(())
}

fn copy_dir_recursive(source: &Path, target: &Path) -> Result<()> {
    fs::create_dir_all(target)?;

    for entry in WalkDir::new(source).min_depth(1) {
        let entry = entry?;
        let relative = entry
            .path()
            .strip_prefix(source)
            .context("Failed to build relative extension path")?;
        let destination = target.join(relative);

        if entry.file_type().is_dir() {
            fs::create_dir_all(&destination)?;
            continue;
        }

        if entry.file_type().is_symlink() {
            anyhow::bail!(
                "Unsupported symlink in extension payload: {}",
                entry.path().display()
            );
        }

        if let Some(parent) = destination.parent() {
            fs::create_dir_all(parent)?;
        }

        fs::copy(entry.path(), &destination)?;
        let permissions = fs::metadata(entry.path())?.permissions();
        fs::set_permissions(&destination, permissions)?;
    }

    Ok(())
}

pub fn replace_extension_root(source: &Path, target: &Path) -> Result<()> {
    let parent = target
        .parent()
        .context("Stable extension path must have a parent directory")?;
    fs::create_dir_all(parent)?;

    let staging = parent.join(".current.next");
    let backup = parent.join(".current.prev");

    if staging.exists() {
        remove_path(&staging)?;
    }
    if backup.exists() {
        remove_path(&backup)?;
    }

    copy_dir_recursive(source, &staging)?;

    let target_exists = target.exists() || fs::symlink_metadata(target).is_ok();
    if target_exists {
        if let Err(err) = fs::rename(target, &backup) {
            let _ = remove_path(&staging);
            return Err(err).with_context(|| {
                format!(
                    "Failed to prepare stable extension directory at {}",
                    target.display()
                )
            });
        }
    }

    if let Err(err) = fs::rename(&staging, target) {
        if backup.exists() {
            let _ = fs::rename(&backup, target);
        }
        return Err(err).with_context(|| {
            format!(
                "Failed to replace stable extension directory at {}",
                target.display()
            )
        });
    }

    if backup.exists() {
        remove_path(&backup)?;
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{extension_id_from_manifest_key, replace_extension_root};
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn derives_32_char_extension_id() {
        let key = "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE9nSLy4hQx8Qm1lM2wL5mdx6x0sW2n9QzWm2z5AbxPD9PqHzlOAqxCLv7saEh1PQuLzpTUN324j6nU5zTh+S4Ng==";
        let id = extension_id_from_manifest_key(key).unwrap();
        assert_eq!(id.len(), 32);
        assert!(id.chars().all(|ch| ('a'..='p').contains(&ch)));
    }

    #[test]
    fn replaces_stable_extension_directory_in_place() {
        let temp = tempdir().unwrap();
        let source_v1 = temp.path().join("source-v1");
        let source_v2 = temp.path().join("source-v2");
        let stable = temp.path().join("repo").join("current");

        fs::create_dir_all(source_v1.join("assets")).unwrap();
        fs::write(source_v1.join("manifest.json"), "{\"version\":\"1.0.0\"}").unwrap();
        fs::write(source_v1.join("assets").join("main.js"), "v1").unwrap();

        replace_extension_root(&source_v1, &stable).unwrap();
        assert_eq!(
            fs::read_to_string(stable.join("manifest.json")).unwrap(),
            "{\"version\":\"1.0.0\"}"
        );

        fs::create_dir_all(source_v2.join("assets")).unwrap();
        fs::write(source_v2.join("manifest.json"), "{\"version\":\"2.0.0\"}").unwrap();
        fs::write(source_v2.join("assets").join("main.js"), "v2").unwrap();
        fs::write(source_v2.join("assets").join("extra.js"), "extra").unwrap();

        replace_extension_root(&source_v2, &stable).unwrap();

        assert_eq!(
            fs::read_to_string(stable.join("manifest.json")).unwrap(),
            "{\"version\":\"2.0.0\"}"
        );
        assert_eq!(
            fs::read_to_string(stable.join("assets").join("main.js")).unwrap(),
            "v2"
        );
        assert_eq!(
            fs::read_to_string(stable.join("assets").join("extra.js")).unwrap(),
            "extra"
        );
    }
}
