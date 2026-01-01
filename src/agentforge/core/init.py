# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-init
# @test_path: tests/unit/harness/test_tool_registry.py

"""
Project initialization for AgentForge.

Handles creating the .agentforge directory structure and populating
it with default agents and pipelines from package resources.
"""

import shutil
from pathlib import Path
from typing import Optional
from importlib import resources

import yaml


def get_package_resource_path(subpath: str) -> Path:
    """Get the path to a package resource.

    Uses importlib.resources for Python 3.11+ compatibility.
    Falls back to file-based paths if resources aren't bundled.
    """
    # For development, check if we're running from source
    package_dir = Path(__file__).parent.parent
    resource_path = package_dir / "defaults" / subpath
    if resource_path.exists():
        return resource_path

    # For installed packages, use importlib.resources
    try:
        with resources.as_file(resources.files("agentforge.defaults") / subpath) as path:
            return Path(path)
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        return resource_path  # Return expected path even if not found


def initialize_project(
    project_path: Optional[Path] = None,
    name: Optional[str] = None,
    force: bool = False,
) -> Path:
    """Initialize an AgentForge project.

    Creates the .agentforge directory structure and copies default
    configurations from package resources.

    Args:
        project_path: Root directory for the project. Defaults to CWD.
        name: Project name. Defaults to directory name.
        force: Overwrite existing .agentforge directory.

    Returns:
        Path to the initialized .agentforge directory.

    Raises:
        FileExistsError: If .agentforge exists and force=False.
    """
    project_path = Path(project_path or Path.cwd()).resolve()
    agentforge_dir = project_path / ".agentforge"

    # Check for existing directory
    if agentforge_dir.exists() and not force:
        raise FileExistsError(
            f"AgentForge already initialized at {agentforge_dir}. "
            "Use --force to reinitialize."
        )

    # Create directory structure
    dirs_to_create = [
        agentforge_dir,
        agentforge_dir / "agents",
        agentforge_dir / "pipelines",
        agentforge_dir / "violations",
        agentforge_dir / "tasks",
        agentforge_dir / "context",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Copy default agents
    _copy_defaults("agents", agentforge_dir / "agents", force)

    # Copy default pipelines
    _copy_defaults("pipelines", agentforge_dir / "pipelines", force)

    # Create repo.yaml if it doesn't exist
    repo_yaml = project_path / "repo.yaml"
    if not repo_yaml.exists() or force:
        project_name = name or project_path.name
        _create_repo_yaml(repo_yaml, project_name)

    return agentforge_dir


def _copy_defaults(resource_subdir: str, target_dir: Path, force: bool) -> None:
    """Copy default files from package resources to target directory."""
    source_dir = get_package_resource_path(resource_subdir)

    if not source_dir.exists():
        return

    for source_file in source_dir.glob("**/*"):
        if source_file.is_file():
            # Calculate relative path from source_dir
            rel_path = source_file.relative_to(source_dir)
            target_file = target_dir / rel_path

            # Create parent directories if needed
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy if doesn't exist or force=True
            if not target_file.exists() or force:
                shutil.copy2(source_file, target_file)


def _create_repo_yaml(path: Path, name: str) -> None:
    """Create a default repo.yaml configuration."""
    config = {
        "name": name,
        "version": "1.0",
        "description": f"AgentForge configuration for {name}",
        "language": "python",  # Default, user can change
        "type": "service",
        "contracts": {
            "version": "1.0",
            "inherit": ["agentforge:default"],
        },
        "paths": {
            "specs": "specs/",
            "tests": "tests/",
            "src": "src/",
        },
        "conformance": {
            "enabled": True,
            "violation_threshold": "error",
        },
    }

    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def is_initialized(path: Optional[Path] = None) -> bool:
    """Check if a directory has been initialized for AgentForge.

    Args:
        path: Directory to check. Defaults to CWD.

    Returns:
        True if .agentforge directory exists.
    """
    path = Path(path or Path.cwd()).resolve()
    return (path / ".agentforge").exists()


def get_agentforge_dir(path: Optional[Path] = None) -> Optional[Path]:
    """Find the .agentforge directory for a project.

    Searches up the directory tree from the given path.

    Args:
        path: Starting directory. Defaults to CWD.

    Returns:
        Path to .agentforge directory, or None if not found.
    """
    path = Path(path or Path.cwd()).resolve()

    # Search up the directory tree
    for parent in [path] + list(path.parents):
        agentforge_dir = parent / ".agentforge"
        if agentforge_dir.is_dir():
            return agentforge_dir

    return None
