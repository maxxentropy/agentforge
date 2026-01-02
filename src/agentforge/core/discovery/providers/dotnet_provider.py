"""
.NET Language Provider
======================

Provides .NET/C#-specific analysis using:
- LSP (OmniSharp/csharp-ls) for symbol extraction
- XML parsing for .csproj/.sln files
- Regex fallback for basic pattern detection
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .base import Dependency, Import, LanguageProvider, Symbol


class DotNetProvider(LanguageProvider):
    """
    .NET language provider using LSP and XML parsing.

    Uses OmniSharp or csharp-ls for semantic analysis when available,
    falls back to regex-based extraction otherwise.
    """

    @property
    def language_name(self) -> str:
        return "csharp"

    @property
    def file_extensions(self) -> set[str]:
        return {".cs", ".csx"}

    @property
    def project_markers(self) -> set[str]:
        return {"*.sln", "*.csproj"}

    def __init__(self):
        self._lsp_adapter = None
        self._lsp_available = None
        self._solution_info: dict[str, Any] | None = None
        self._projects: dict[str, dict[str, Any]] = {}

    def detect_project(self, path: Path) -> dict[str, Any] | None:
        """Detect .NET project and extract metadata."""
        if not path.is_dir():
            path = path.parent

        # Look for solution file first
        sln_files = list(path.glob("*.sln"))
        if sln_files:
            return self._parse_solution(sln_files[0])

        # Look for csproj files
        csproj_files = list(path.glob("**/*.csproj"))
        if csproj_files:
            # Use the first one as the main project
            project_info = self._parse_csproj(csproj_files[0])
            project_info["all_projects"] = [str(f) for f in csproj_files]
            return project_info

        return None

    def _parse_solution(self, sln_path: Path) -> dict[str, Any]:
        """Parse .sln file to extract solution structure."""
        result = {
            "name": sln_path.stem,
            "solution_file": str(sln_path),
            "projects": [],
            "frameworks": set(),
        }

        try:
            content = sln_path.read_text(encoding='utf-8-sig')

            # Extract project references from solution
            # Format: Project("{GUID}") = "ProjectName", "Path\Project.csproj", "{GUID}"
            project_pattern = r'Project\("[^"]+"\)\s*=\s*"([^"]+)",\s*"([^"]+\.csproj)"'

            for match in re.finditer(project_pattern, content):
                proj_name = match.group(1)
                proj_path = match.group(2).replace("\\", "/")
                full_path = sln_path.parent / proj_path

                if full_path.exists():
                    proj_info = self._parse_csproj(full_path)
                    proj_info["name"] = proj_name
                    result["projects"].append(proj_info)

                    # Collect frameworks
                    if proj_info.get("frameworks"):
                        result["frameworks"].update(proj_info["frameworks"])

            result["frameworks"] = list(result["frameworks"])
            if result["frameworks"]:
                result["framework"] = result["frameworks"][0]

        except Exception:
            pass

        return result

    def _parse_csproj(self, csproj_path: Path) -> dict[str, Any]:
        """Parse .csproj file to extract project metadata."""
        result = {
            "name": csproj_path.stem,
            "project_file": str(csproj_path),
            "target_framework": None,
            "output_type": None,
            "packages": [],
            "project_references": [],
            "frameworks": [],
            "is_test": False,
            "is_web": False,
        }

        try:
            tree = ET.parse(csproj_path)
            root = tree.getroot()

            # Handle namespace in modern csproj
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            # Target framework
            for tf in root.iter(f"{ns}TargetFramework"):
                result["target_framework"] = tf.text
                break
            for tf in root.iter(f"{ns}TargetFrameworks"):
                result["target_framework"] = tf.text.split(";")[0] if tf.text else None
                break

            # Output type
            for ot in root.iter(f"{ns}OutputType"):
                result["output_type"] = ot.text
                break

            # Package references
            for pkg in root.iter(f"{ns}PackageReference"):
                pkg_name = pkg.get("Include") or pkg.get("include")
                pkg_version = pkg.get("Version") or pkg.get("version")
                if pkg_name:
                    result["packages"].append({
                        "name": pkg_name,
                        "version": pkg_version,
                    })

                    # Detect frameworks from packages
                    frameworks = self._detect_frameworks_from_package(pkg_name)
                    result["frameworks"].extend(frameworks)

            # Project references
            for ref in root.iter(f"{ns}ProjectReference"):
                ref_path = ref.get("Include") or ref.get("include")
                if ref_path:
                    result["project_references"].append(ref_path.replace("\\", "/"))

            # Detect test project
            result["is_test"] = any(
                pkg["name"].lower() in ("xunit", "nunit", "mstest.testframework", "microsoft.net.test.sdk")
                for pkg in result["packages"]
            )

            # Detect web project
            result["is_web"] = any(
                pkg["name"].startswith("Microsoft.AspNetCore")
                for pkg in result["packages"]
            ) or "Microsoft.NET.Sdk.Web" in (csproj_path.read_text() if csproj_path.exists() else "")

            result["frameworks"] = list(set(result["frameworks"]))
            if result["frameworks"]:
                result["framework"] = result["frameworks"][0]

            self._projects[str(csproj_path)] = result

        except Exception:
            pass

        return result

    def _detect_frameworks_from_package(self, package_name: str) -> list[str]:
        """Detect frameworks from NuGet package names."""
        frameworks = []
        pkg_lower = package_name.lower()

        framework_markers = {
            "mediatr": "MediatR",
            "fluentvalidation": "FluentValidation",
            "automapper": "AutoMapper",
            "efcore": "Entity Framework Core",
            "entityframeworkcore": "Entity Framework Core",
            "microsoft.entityframeworkcore": "Entity Framework Core",
            "microsoft.aspnetcore": "ASP.NET Core",
            "swashbuckle": "Swagger",
            "serilog": "Serilog",
            "newtonsoft.json": "Newtonsoft.Json",
            "system.text.json": "System.Text.Json",
            "polly": "Polly",
            "hangfire": "Hangfire",
            "quartz": "Quartz.NET",
            "dapper": "Dapper",
            "xunit": "xUnit",
            "nunit": "NUnit",
            "moq": "Moq",
            "nsubstitute": "NSubstitute",
            "fluentassertions": "FluentAssertions",
        }

        for marker, name in framework_markers.items():
            if marker in pkg_lower:
                frameworks.append(name)

        return frameworks

    def parse_file(self, path: Path) -> Any | None:
        """Parse C# file - returns content for regex analysis."""
        try:
            return path.read_text(encoding='utf-8')
        except Exception:
            return None

    def extract_symbols(self, path: Path) -> list[Symbol]:
        """Extract symbols from C# file using LSP or regex fallback."""
        # Try LSP first
        symbols = self._extract_symbols_lsp(path)
        if symbols:
            return symbols

        # Fallback to regex
        return self._extract_symbols_regex(path)

    def _extract_symbols_lsp(self, path: Path) -> list[Symbol]:
        """Extract symbols using LSP adapter."""
        if not self._ensure_lsp():
            return []

        try:
            lsp_symbols = self._lsp_adapter.get_symbols(str(path))
            return self._convert_lsp_symbols(lsp_symbols, path)
        except Exception:
            return []

    def _ensure_lsp(self) -> bool:
        """Ensure LSP adapter is available and initialized."""
        if self._lsp_available is False:
            return False

        if self._lsp_adapter is not None:
            return True

        try:
            from ..providers import _get_lsp_adapter
            self._lsp_adapter = _get_lsp_adapter()
            if self._lsp_adapter:
                self._lsp_adapter.initialize()
                self._lsp_available = True
                return True
        except Exception:
            pass

        self._lsp_available = False
        return False

    def _convert_lsp_symbols(self, lsp_symbols: list, path: Path) -> list[Symbol]:
        """Convert LSP symbols to discovery symbols."""
        symbols = []

        for lsp_sym in lsp_symbols:
            # Extract base classes and interfaces from detail
            base_classes = []
            decorators = []

            if lsp_sym.detail:
                # Parse detail like "class Foo : Bar, IBaz"
                if ":" in lsp_sym.detail:
                    bases_str = lsp_sym.detail.split(":", 1)[1]
                    base_classes = [b.strip() for b in bases_str.split(",")]

            symbol = Symbol(
                name=lsp_sym.name,
                kind=lsp_sym.kind,
                file_path=path,
                line_number=lsp_sym.location.line + 1,  # Convert to 1-based
                end_line=lsp_sym.location.end_line + 1 if lsp_sym.location.end_line else None,
                parent=lsp_sym.container,
                visibility=self._infer_visibility(lsp_sym.name),
                signature=lsp_sym.detail,
                base_classes=base_classes,
                decorators=decorators,
            )
            symbols.append(symbol)

            # Process children
            if hasattr(lsp_sym, 'children') and lsp_sym.children:
                child_symbols = self._convert_lsp_symbols(lsp_sym.children, path)
                for child in child_symbols:
                    child.parent = lsp_sym.name
                symbols.extend(child_symbols)

        return symbols

    def _extract_symbols_regex(self, path: Path) -> list[Symbol]:
        """Extract symbols using regex patterns (fallback)."""
        content = self.parse_file(path)
        if not content:
            return []

        symbols = []
        lines = content.split('\n')

        # Track current namespace and class
        current_namespace = None
        current_class = None

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Namespace
            ns_match = re.match(r'namespace\s+([\w.]+)', stripped)
            if ns_match:
                current_namespace = ns_match.group(1)
                continue

            # Class/Interface/Record/Struct
            type_match = re.match(
                r'(public|private|protected|internal)?\s*(static\s+)?(abstract\s+)?(sealed\s+)?'
                r'(partial\s+)?(class|interface|record|struct)\s+(\w+)(?:<[^>]+>)?'
                r'(?:\s*:\s*(.+?))?(?:\s*{|\s*$)',
                stripped
            )
            if type_match:
                visibility = type_match.group(1) or "internal"
                type_kind = type_match.group(6)
                name = type_match.group(7)
                bases = type_match.group(8)

                base_classes = []
                if bases:
                    base_classes = [b.strip() for b in bases.split(",")]

                symbols.append(Symbol(
                    name=name,
                    kind=type_kind,
                    file_path=path,
                    line_number=line_num,
                    parent=current_namespace,
                    visibility=visibility,
                    base_classes=base_classes,
                ))
                current_class = name
                continue

            # Method
            method_match = re.match(
                r'(public|private|protected|internal)?\s*(static\s+)?(async\s+)?'
                r'(virtual\s+)?(override\s+)?(abstract\s+)?'
                r'([\w<>\[\],\s]+?)\s+(\w+)\s*\([^)]*\)',
                stripped
            )
            if method_match and current_class:
                visibility = method_match.group(1) or "private"
                return_type = method_match.group(7).strip()
                name = method_match.group(8)

                # Skip if it looks like a control flow statement
                if name in ('if', 'while', 'for', 'foreach', 'switch', 'catch', 'using'):
                    continue

                symbols.append(Symbol(
                    name=name,
                    kind="method",
                    file_path=path,
                    line_number=line_num,
                    parent=current_class,
                    visibility=visibility,
                    return_type=return_type,
                ))
                continue

            # Property
            prop_match = re.match(
                r'(public|private|protected|internal)?\s*(static\s+)?(virtual\s+)?'
                r'(override\s+)?(required\s+)?'
                r'([\w<>\[\],\s?]+?)\s+(\w+)\s*{\s*(get|set|init)',
                stripped
            )
            if prop_match and current_class:
                visibility = prop_match.group(1) or "private"
                prop_type = prop_match.group(6).strip()
                name = prop_match.group(7)

                symbols.append(Symbol(
                    name=name,
                    kind="property",
                    file_path=path,
                    line_number=line_num,
                    parent=current_class,
                    visibility=visibility,
                    return_type=prop_type,
                ))

        return symbols

    def _infer_visibility(self, name: str) -> str:
        """Infer visibility from name (C# convention)."""
        if name.startswith("_"):
            return "private"
        return "public"

    def get_imports(self, path: Path) -> list[Import]:
        """Extract using statements from C# file."""
        content = self.parse_file(path)
        if not content:
            return []

        imports = []

        for line_num, line in enumerate(content.split('\n'), 1):
            stripped = line.strip()

            # using Namespace;
            match = re.match(r'using\s+([\w.]+)\s*;', stripped)
            if match:
                imports.append(Import(
                    module=match.group(1),
                    names=[match.group(1).split(".")[-1]],
                    file_path=path,
                    line_number=line_num,
                ))
                continue

            # using Alias = Namespace.Type;
            alias_match = re.match(r'using\s+(\w+)\s*=\s*([\w.]+)\s*;', stripped)
            if alias_match:
                imports.append(Import(
                    module=alias_match.group(2),
                    names=[alias_match.group(2).split(".")[-1]],
                    alias=alias_match.group(1),
                    file_path=path,
                    line_number=line_num,
                ))
                continue

            # using static Namespace.Type;
            static_match = re.match(r'using\s+static\s+([\w.]+)\s*;', stripped)
            if static_match:
                imports.append(Import(
                    module=static_match.group(1),
                    names=[static_match.group(1).split(".")[-1]],
                    file_path=path,
                    line_number=line_num,
                ))

        return imports

    def get_dependencies(self, project_path: Path) -> list[Dependency]:
        """Extract NuGet dependencies from project files."""
        dependencies = []

        if project_path.is_file():
            project_path = project_path.parent

        # Find all csproj files
        for csproj in project_path.rglob("*.csproj"):
            proj_info = self._parse_csproj(csproj)

            for pkg in proj_info.get("packages", []):
                # Check if it's a dev dependency (test packages)
                is_dev = any(
                    marker in pkg["name"].lower()
                    for marker in ("test", "mock", "fake", "xunit", "nunit", "coverlet")
                )

                dependencies.append(Dependency(
                    name=pkg["name"],
                    version=pkg.get("version"),
                    source="nuget",
                    is_dev=is_dev,
                ))

        return dependencies

    def get_project_references(self, csproj_path: Path) -> list[str]:
        """Get project references from a csproj file."""
        if str(csproj_path) in self._projects:
            return self._projects[str(csproj_path)].get("project_references", [])

        proj_info = self._parse_csproj(csproj_path)
        return proj_info.get("project_references", [])

    def detect_layer_from_project_name(self, project_name: str) -> str | None:
        """
        Detect architectural layer from project name.

        Follows Clean Architecture naming conventions:
        - *.Domain, *.Core, *.Entities → domain
        - *.Application, *.UseCases → application
        - *.Infrastructure, *.Persistence, *.Data → infrastructure
        - *.Api, *.Web, *.Presentation → presentation
        """
        name_lower = project_name.lower()

        # Domain layer indicators
        if any(ind in name_lower for ind in [".domain", ".core", ".entities", ".model"]):
            return "domain"

        # Application layer indicators
        if any(ind in name_lower for ind in [".application", ".usecases", ".services"]):
            return "application"

        # Infrastructure layer indicators
        if any(ind in name_lower for ind in [".infrastructure", ".persistence", ".data", ".repository"]):
            return "infrastructure"

        # Presentation layer indicators
        if any(ind in name_lower for ind in [".api", ".web", ".presentation", ".ui", ".mvc", ".blazor"]):
            return "presentation"

        # Test indicators (not a layer, but useful)
        if any(ind in name_lower for ind in [".test", ".tests", ".unittests", ".integrationtests"]):
            return "tests"

        return None

    def get_source_files(self, root: Path, exclude_patterns: list[str] = None) -> list[Path]:
        """Find all C# source files under root."""
        exclude_patterns = exclude_patterns or []
        default_excludes = [
            "bin", "obj", ".git", "node_modules", "packages",
            ".vs", "TestResults", "artifacts",
        ]

        files = []
        for ext in self.file_extensions:
            for path in root.rglob(f"*{ext}"):
                skip = False
                path_str = str(path)
                for pattern in default_excludes + exclude_patterns:
                    if f"/{pattern}/" in path_str or f"\\{pattern}\\" in path_str:
                        skip = True
                        break
                if not skip:
                    files.append(path)

        return sorted(files)

    def count_lines(self, path: Path) -> int:
        """Count non-empty, non-comment lines of code."""
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
                count = 0
                in_block_comment = False

                for line in f:
                    stripped = line.strip()

                    # Skip empty lines
                    if not stripped:
                        continue

                    # Handle block comments
                    if "/*" in stripped and "*/" in stripped:
                        # Single line block comment
                        continue
                    elif "/*" in stripped:
                        in_block_comment = True
                        continue
                    elif "*/" in stripped:
                        in_block_comment = False
                        continue
                    elif in_block_comment:
                        continue

                    # Skip single-line comments
                    if stripped.startswith("//"):
                        continue

                    count += 1

                return count
        except Exception:
            return 0
