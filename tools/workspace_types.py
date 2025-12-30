#!/usr/bin/env python3
"""
Workspace Type Definitions
==========================

Data classes and exceptions for workspace management.

Extracted from workspace.py for modularity.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List


# =============================================================================
# Exceptions
# =============================================================================

class WorkspaceError(Exception):
    """Base exception for workspace errors."""
    pass


class RepoNotFoundError(WorkspaceError):
    """Raised when a referenced repo doesn't exist."""
    pass


class WorkspaceSchemaError(WorkspaceError):
    """Raised when workspace.yaml has invalid schema."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when workspace cannot be found."""
    pass


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class RepoConfig:
    """Configuration for a single repository."""
    name: str
    path: str  # Relative path from workspace.yaml
    type: str  # service, library, application, meta
    language: str
    framework: Optional[str] = None
    lsp: Optional[str] = None
    layers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Resolved at runtime
    resolved_path: Optional[Path] = None
    is_available: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'RepoConfig':
        """Create RepoConfig from dictionary."""
        return cls(
            name=data['name'],
            path=data['path'],
            type=data.get('type', 'service'),
            language=data.get('language', 'unknown'),
            framework=data.get('framework'),
            lsp=data.get('lsp'),
            layers=data.get('layers', []),
            tags=data.get('tags', []),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        result = {
            'name': self.name,
            'path': self.path,
            'type': self.type,
            'language': self.language,
        }
        if self.framework:
            result['framework'] = self.framework
        if self.lsp:
            result['lsp'] = self.lsp
        if self.layers:
            result['layers'] = self.layers
        if self.tags:
            result['tags'] = self.tags
        return result


@dataclass
class WorkspaceContext:
    """Resolved workspace context."""

    # Workspace location and config
    workspace_path: Optional[Path] = None
    workspace_config: Optional[dict] = None

    # Current repo context
    current_repo: Optional[str] = None
    current_repo_path: Optional[Path] = None

    # Discovery information
    discovery_method: str = "none"

    # Resolved repos
    repos: Dict[str, RepoConfig] = field(default_factory=dict)
    available_repos: Dict[str, Path] = field(default_factory=dict)
    unavailable_repos: List[str] = field(default_factory=list)

    @property
    def is_workspace_mode(self) -> bool:
        """Check if we're in workspace mode (vs single-repo mode)."""
        return self.discovery_method != "none" and self.workspace_config is not None

    @property
    def workspace_name(self) -> Optional[str]:
        """Get workspace name."""
        if self.workspace_config:
            return self.workspace_config.get('workspace', {}).get('name')
        return None

    @property
    def workspace_description(self) -> Optional[str]:
        """Get workspace description."""
        if self.workspace_config:
            return self.workspace_config.get('workspace', {}).get('description')
        return None

    @property
    def workspace_version(self) -> Optional[str]:
        """Get workspace version."""
        if self.workspace_config:
            return self.workspace_config.get('workspace', {}).get('version')
        return None

    @property
    def workspace_dir(self) -> Optional[Path]:
        """Get workspace directory (parent of workspace.yaml)."""
        if self.workspace_path:
            return self.workspace_path.parent
        return None

    def get_repo(self, name: str) -> Optional[RepoConfig]:
        """Get repo config by name."""
        return self.repos.get(name)

    def get_repo_path(self, name: str) -> Optional[Path]:
        """Get resolved path for a repo."""
        return self.available_repos.get(name)

    def get_repos_by_tag(self, tag: str) -> List[RepoConfig]:
        """Get all repos with a specific tag."""
        return [r for r in self.repos.values() if tag in r.tags]

    def get_repos_by_type(self, repo_type: str) -> List[RepoConfig]:
        """Get all repos of a specific type."""
        return [r for r in self.repos.values() if r.type == repo_type]

    def get_repos_by_language(self, language: str) -> List[RepoConfig]:
        """Get all repos with a specific language."""
        return [r for r in self.repos.values() if r.language == language]
