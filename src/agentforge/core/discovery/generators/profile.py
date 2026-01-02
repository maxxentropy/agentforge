# @spec_file: .agentforge/specs/core-discovery-generators-v1.yaml
# @spec_id: core-discovery-generators-v1
# @component_id: discovery-generators-profile
# @test_path: tests/unit/tools/bridge/test_profile_loader.py

"""
Profile Generator
=================

Generates codebase_profile.yaml from discovery results.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ..analyzers.patterns import PatternAnalysisResult
from ..analyzers.structure import StructureAnalysisResult
from ..domain import (
    CodebaseProfile,
    DependencyInfo,
    Detection,
    DetectionSource,
    DiscoveryMetadata,
    LanguageInfo,
    TestAnalysis,
)


class ProfileGenerator:
    """
    Generates codebase_profile.yaml from discovery analysis results.

    Combines results from multiple analyzers into a single profile
    that conforms to the codebase_profile.schema.yaml specification.
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self._profile: CodebaseProfile | None = None

    def generate(
        self,
        languages: list[LanguageInfo],
        structure_result: StructureAnalysisResult,
        pattern_result: PatternAnalysisResult,
        dependencies: list[DependencyInfo],
        phases_completed: list[str],
        duration_seconds: float,
        test_analysis: TestAnalysis | None = None,
    ) -> CodebaseProfile:
        """
        Generate a CodebaseProfile from analysis results.

        Args:
            languages: Detected language information
            structure_result: Results from structure analysis
            pattern_result: Results from pattern analysis
            dependencies: Project dependencies
            phases_completed: List of completed discovery phases
            duration_seconds: Total discovery duration
            test_analysis: Results from test linkage analysis

        Returns:
            Complete CodebaseProfile
        """
        now = datetime.now()

        # Create discovery metadata
        metadata = DiscoveryMetadata(
            discovery_version="1.0",
            run_date=now,
            root_path=str(self.root_path),
            phases_completed=phases_completed,
            total_files_analyzed=pattern_result.total_files_analyzed,
            duration_seconds=duration_seconds,
        )

        # Build structure dict
        structure = self._build_structure_dict(structure_result)

        # Build patterns dict
        patterns = self._build_patterns_dict(pattern_result)

        # Build architecture dict
        architecture = self._build_architecture_dict(structure_result)

        # Create profile
        self._profile = CodebaseProfile(
            schema_version=self.SCHEMA_VERSION,
            generated_at=now,
            discovery_metadata=metadata,
            languages=languages,
            structure=structure,
            patterns=patterns,
            architecture=architecture,
            dependencies=dependencies,
            test_analysis=test_analysis,
        )

        return self._profile

    def _build_structure_dict(self, result: StructureAnalysisResult) -> dict[str, Any]:
        """Build structure section of profile."""
        return {
            "architecture_style": result.architecture_style,
            "confidence": round(result.confidence, 2),
            "source_root": str(result.source_root) if result.source_root else None,
            "layers": {
                name: {
                    "paths": layer.paths,
                    "file_count": layer.file_count,
                    "line_count": layer.line_count,
                    "confidence": round(layer.detection.confidence, 2),
                    "signals": layer.detection.signals[:5],  # Limit signals
                }
                for name, layer in result.layers.items()
            },
            "entry_points": [str(p) for p in result.entry_points[:5]],
            "test_directories": [str(p) for p in result.test_directories],
            "signals": result.signals[:10],
        }

    def _build_patterns_dict(self, result: PatternAnalysisResult) -> dict[str, Any]:
        """Build patterns section of profile."""
        patterns_dict = {}

        for name, pattern in result.patterns.items():
            patterns_dict[name] = {
                "description": pattern.description,
                "confidence": round(pattern.detection.confidence, 2),
                "source": pattern.detection.source.value,
                "file_count": pattern.file_count,
                "locations": pattern.locations[:5],  # Limit examples
                "signals": pattern.detection.signals,
            }

        # Add frameworks as patterns
        for fw_name, detection in result.frameworks.items():
            patterns_dict[f"framework_{fw_name}"] = {
                "description": f"{fw_name} framework detected",
                "confidence": round(detection.confidence, 2),
                "source": detection.source.value,
                "signals": detection.signals,
                "metadata": detection.metadata,
            }

        return patterns_dict

    def _build_architecture_dict(self, result: StructureAnalysisResult) -> dict[str, Any]:
        """Build architecture section of profile."""
        return {
            "style": result.architecture_style,
            "layers": list(result.layers.keys()),
            "layer_dependencies": {},  # Would need import analysis
            "violations": [],  # Would need conformance check
        }

    def to_yaml(self) -> str:
        """Convert profile to YAML string."""
        if not self._profile:
            raise ValueError("No profile generated. Call generate() first.")

        data = self._profile_to_dict(self._profile)
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def save(self, output_path: Path | None = None) -> Path:
        """
        Save profile to YAML file.

        Args:
            output_path: Custom output path, or uses default .agentforge/codebase_profile.yaml

        Returns:
            Path to saved file
        """
        if not self._profile:
            raise ValueError("No profile generated. Call generate() first.")

        if output_path is None:
            agentforge_dir = self.root_path / ".agentforge"
            agentforge_dir.mkdir(exist_ok=True)
            output_path = agentforge_dir / "codebase_profile.yaml"

        yaml_content = self.to_yaml()
        output_path.write_text(yaml_content, encoding='utf-8')

        return output_path

    def _profile_to_dict(self, profile: CodebaseProfile) -> dict[str, Any]:
        """Convert CodebaseProfile to serializable dict."""
        return {
            "schema_version": profile.schema_version,
            "generated_at": profile.generated_at.isoformat(),
            "discovery_metadata": {
                "discovery_version": profile.discovery_metadata.discovery_version,
                "run_date": profile.discovery_metadata.run_date.isoformat(),
                "root_path": profile.discovery_metadata.root_path,
                "phases_completed": profile.discovery_metadata.phases_completed,
                "total_files_analyzed": profile.discovery_metadata.total_files_analyzed,
                "duration_seconds": round(profile.discovery_metadata.duration_seconds, 2),
            },
            "languages": [
                {
                    "name": lang.name,
                    "version": lang.version,
                    "confidence": round(lang.detection.confidence, 2),
                    "file_count": lang.file_count,
                    "line_count": lang.line_count,
                    "frameworks": lang.frameworks,
                    "primary": lang.primary,
                }
                for lang in profile.languages
            ],
            "structure": profile.structure,
            "patterns": profile.patterns,
            "architecture": profile.architecture,
            "dependencies": [
                {
                    "name": dep.name,
                    "version": dep.version,
                    "source": dep.source,
                    "is_dev": dep.is_dev,
                    "category": dep.category,
                }
                for dep in profile.dependencies
            ] if profile.dependencies else [],
            "test_analysis": profile.test_analysis.to_dict() if profile.test_analysis else None,
        }

    @classmethod
    def load(cls, path: Path) -> 'ProfileGenerator':
        """Load an existing profile from YAML file."""
        content = path.read_text(encoding='utf-8')
        data = yaml.safe_load(content)

        root_path = Path(data.get("discovery_metadata", {}).get("root_path", "."))
        generator = cls(root_path)

        # Reconstruct profile from data
        # This is a simplified version - full implementation would reconstruct all objects
        generator._profile = cls._dict_to_profile(data, root_path)

        return generator

    @classmethod
    def _dict_to_profile(cls, data: dict[str, Any], root_path: Path) -> CodebaseProfile:
        """Convert dict back to CodebaseProfile."""
        metadata = DiscoveryMetadata(
            discovery_version=data.get("discovery_metadata", {}).get("discovery_version", "1.0"),
            run_date=datetime.fromisoformat(data.get("discovery_metadata", {}).get("run_date", datetime.now().isoformat())),
            root_path=str(root_path),
            phases_completed=data.get("discovery_metadata", {}).get("phases_completed", []),
            total_files_analyzed=data.get("discovery_metadata", {}).get("total_files_analyzed", 0),
            duration_seconds=data.get("discovery_metadata", {}).get("duration_seconds", 0),
        )

        languages = []
        for lang_data in data.get("languages", []):
            languages.append(LanguageInfo(
                name=lang_data.get("name", "unknown"),
                version=lang_data.get("version"),
                detection=Detection(
                    value=lang_data.get("name", "unknown"),
                    confidence=lang_data.get("confidence", 0.0),
                    source=DetectionSource.EXPLICIT,
                    signals=[],
                ),
                file_count=lang_data.get("file_count", 0),
                line_count=lang_data.get("line_count", 0),
                frameworks=lang_data.get("frameworks", []),
                primary=lang_data.get("primary", False),
            ))

        dependencies = []
        for dep_data in data.get("dependencies", []):
            dependencies.append(DependencyInfo(
                name=dep_data.get("name", ""),
                version=dep_data.get("version"),
                source=dep_data.get("source", "unknown"),
                is_dev=dep_data.get("is_dev", False),
                category=dep_data.get("category"),
            ))

        return CodebaseProfile(
            schema_version=data.get("schema_version", "1.0"),
            generated_at=datetime.fromisoformat(data.get("generated_at", datetime.now().isoformat())),
            discovery_metadata=metadata,
            languages=languages,
            structure=data.get("structure", {}),
            patterns=data.get("patterns", {}),
            architecture=data.get("architecture"),
            dependencies=dependencies,
        )
