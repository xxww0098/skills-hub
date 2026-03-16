use anyhow::{bail, Result};

pub fn normalize_repo(input: &str) -> Result<String> {
    let mut value = input.trim();

    if value.is_empty() {
        bail!("Repository cannot be empty. Use owner/repo or a GitHub URL");
    }

    if let Some(rest) = value.strip_prefix("git@github.com:") {
        value = rest;
    }

    for prefix in ["https://github.com/", "http://github.com/", "github.com/"] {
        if let Some(rest) = value.strip_prefix(prefix) {
            value = rest;
            break;
        }
    }

    if let Some((head, _)) = value.split_once('?') {
        value = head;
    }

    if let Some((head, _)) = value.split_once('#') {
        value = head;
    }

    value = value.trim_matches('/').trim_end_matches(".git");

    let parts: Vec<&str> = value.split('/').filter(|part| !part.is_empty()).collect();
    if parts.len() < 2 {
        bail!(
            "Invalid repository '{}'. Use owner/repo or a GitHub URL",
            input.trim()
        );
    }

    let owner = parts[0];
    let repo = parts[1];

    if owner.contains(char::is_whitespace) || repo.contains(char::is_whitespace) {
        bail!(
            "Invalid repository '{}'. Use owner/repo or a GitHub URL",
            input.trim()
        );
    }

    Ok(format!("{owner}/{repo}"))
}

pub fn split_repo_key(input: &str) -> Result<(String, String)> {
    let normalized = normalize_repo(input)?;
    let (owner, repo) = normalized
        .split_once('/')
        .expect("normalize_repo always returns owner/repo");
    Ok((owner.to_string(), repo.to_string()))
}

pub fn is_probably_repo_input(input: &str) -> bool {
    let trimmed = input.trim();
    trimmed.contains('/')
        || trimmed.contains("github.com")
        || trimmed.starts_with("git@github.com:")
}

#[cfg(test)]
mod tests {
    use super::{is_probably_repo_input, normalize_repo};

    #[test]
    fn normalizes_plain_repo() {
        assert_eq!(normalize_repo("owner/repo").unwrap(), "owner/repo");
    }

    #[test]
    fn normalizes_github_url() {
        assert_eq!(
            normalize_repo("https://github.com/owner/repo/releases/tag/v1").unwrap(),
            "owner/repo"
        );
    }

    #[test]
    fn normalizes_repo_homepage_url() {
        assert_eq!(
            normalize_repo("https://github.com/owner/repo").unwrap(),
            "owner/repo"
        );
        assert_eq!(
            normalize_repo("https://github.com/owner/repo/").unwrap(),
            "owner/repo"
        );
    }

    #[test]
    fn normalizes_git_remote() {
        assert_eq!(
            normalize_repo("git@github.com:owner/repo.git").unwrap(),
            "owner/repo"
        );
    }

    #[test]
    fn rejects_invalid_repo() {
        assert!(normalize_repo("owner").is_err());
    }

    #[test]
    fn detects_repo_like_input() {
        assert!(is_probably_repo_input("https://github.com/owner/repo"));
        assert!(is_probably_repo_input("owner/repo"));
        assert!(!is_probably_repo_input("status"));
    }
}
