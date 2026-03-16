use anyhow::Result;
use clap::{Parser, Subcommand};
use std::ffi::OsString;
use std::process::ExitCode;

mod commands;
mod utils;

use commands::{cleanup, info, install, list, outdate, remove, update};
use utils::{github, repo};

#[derive(Parser)]
#[command(name = "crx")]
#[command(about = "Download and version browser extensions from GitHub Releases")]
#[command(version = "1.0.0")]
#[command(arg_required_else_help = true)]
struct Cli {
    #[arg(
        short = 'y',
        long = "yes",
        global = true,
        help = "Auto-select the first matching asset instead of prompting"
    )]
    yes: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    #[command(about = "Install the latest release")]
    Install {
        #[arg(help = "GitHub repo or URL")]
        repo: String,
        #[arg(help = "Asset name or glob (e.g. '*chrome*.zip')", required = false)]
        pattern: Option<String>,
        #[arg(
            short = 't',
            long = "tag",
            help = "Install a specific release tag (e.g. 1.5.6, v1.5.6)",
            value_name = "TAG"
        )]
        tag: Option<String>,
    },
    #[command(about = "Update installed extensions", visible_alias = "upgrade")]
    Update {
        #[arg(help = "GitHub repo or URL", required = false)]
        repo: Option<String>,
        #[arg(
            help = "Release selector: latest or a tag like 1.5.6",
            required = false,
            value_name = "TARGET"
        )]
        target: Option<String>,
    },
    #[command(
        about = "Check which installed extensions are outdated",
        visible_alias = "outdated"
    )]
    Outdate {
        #[arg(help = "GitHub repo or URL", required = false)]
        repo: Option<String>,
    },
    #[command(about = "Uninstall and remove the extension", visible_alias = "remove")]
    Uninstall {
        #[arg(help = "GitHub repo or URL")]
        repo: String,
    },
    #[command(about = "Remove old versions of installed extensions")]
    Cleanup {
        #[arg(help = "GitHub repo or URL (omit to cleanup all)", required = false)]
        repo: Option<String>,
        #[arg(
            short = 'n',
            long = "keep",
            help = "Number of versions to keep (default: 1, active version only)",
            default_value = "1"
        )]
        keep: usize,
    },
    #[command(about = "Show details of an installed extension")]
    Info {
        #[arg(help = "GitHub repo or URL")]
        repo: String,
    },
    #[command(about = "List installed extensions")]
    List,
}

fn should_infer_install(arg: &str) -> bool {
    if arg.starts_with('-') {
        return false;
    }

    !matches!(
        arg,
        "install"
            | "update"
            | "upgrade"
            | "outdate"
            | "outdated"
            | "uninstall"
            | "remove"
            | "cleanup"
            | "info"
            | "list"
            | "help"
    ) && repo::is_probably_repo_input(arg)
}

fn preprocess_args() -> Vec<OsString> {
    let mut args: Vec<OsString> = std::env::args_os().collect();
    if let Some(first) = args.get(1).and_then(|arg| arg.to_str()) {
        if should_infer_install(first) {
            args.insert(1, OsString::from("install"));
        }
    }
    args
}

fn run(cli: Cli) -> Result<()> {
    install::set_auto_confirm(cli.yes);

    match cli.command {
        Commands::Install {
            repo,
            pattern,
            tag,
        } => {
            let request = match tag {
                Some(t) => github::ReleaseRequest::tag(t),
                None => github::ReleaseRequest::latest(),
            };
            install::run_with_target(&repo, pattern, request)
        }
        Commands::Update { repo, target } => match repo {
            Some(repo) => update::run(&repo, target.as_deref()),
            None => match target.as_deref() {
                None | Some("latest") => update::run_all(),
                Some(selector) => anyhow::bail!(
                    "A repo is required when selecting a specific release target ({})",
                    selector
                ),
            },
        },
        Commands::Outdate { repo } => match repo {
            Some(repo) => outdate::run(&repo),
            None => outdate::run_all(),
        },
        Commands::Info { repo } => info::run(&repo),
        Commands::Uninstall { repo } => remove::run(&repo),
        Commands::Cleanup { repo, keep } => match repo {
            Some(repo) => cleanup::run_single(&repo, keep),
            None => cleanup::run_all(keep),
        },
        Commands::List => list::run(),
    }
}

fn main() -> ExitCode {
    let cli = Cli::parse_from(preprocess_args());

    match run(cli) {
        Ok(()) => ExitCode::SUCCESS,
        Err(err) => {
            eprintln!("Error: {err:#}");
            ExitCode::FAILURE
        }
    }
}
