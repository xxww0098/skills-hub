use crate::utils::config::{self, Registry, RepoInfo};
use anyhow::{Context, Result};

pub fn parallel_check_repos<T, F>(
    registry: &Registry,
    repos: &[String],
    panic_message: &str,
    check: F,
) -> Vec<(String, Result<T>)>
where
    T: Send,
    F: Fn(&str, RepoInfo) -> Result<T> + Sync,
{
    std::thread::scope(|scope| {
        let check = &check;
        let handles = repos
            .iter()
            .map(|repo| {
                let repo_key = repo.clone();
                let current = config::get_repo_from(registry, repo).cloned();

                scope.spawn(move || {
                    let result = current
                        .with_context(|| format!("Registry entry missing for {}", repo_key))
                        .and_then(|current| check(&repo_key, current));

                    (repo_key, result)
                })
            })
            .collect::<Vec<_>>();

        handles
            .into_iter()
            .map(|handle| handle.join().expect(panic_message))
            .collect::<Vec<_>>()
    })
}
