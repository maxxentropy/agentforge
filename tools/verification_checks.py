#!/usr/bin/env python3
"""
Verification Check Implementations - command, regex, file_exists, import, custom, contracts, lsp, ast.
Extracted from verification_runner.py for modularity.
"""
import os, re, glob, shlex, subprocess, fnmatch, importlib.util
from pathlib import Path
from typing import Dict, Any, List, Callable

try:
    from .verification_types import CheckResult, CheckStatus, Severity
    from .verification_contracts_check import (
        get_contract_results, build_contract_errors, aggregate_contract_stats, build_contract_message)
except ImportError:
    from verification_types import CheckResult, CheckStatus, Severity
    from verification_contracts_check import (
        get_contract_results, build_contract_errors, aggregate_contract_stats, build_contract_message)


class CheckRunner:
    """Mixin class providing check implementations for VerificationRunner."""

    # These attributes are expected to exist on the class using this mixin
    project_root: Path
    context: Dict[str, Any]

    def _substitute_variables(self, text: str) -> str:
        """Replace {variable} placeholders with context values."""
        raise NotImplementedError

    # --- Command Check ---

    def _run_command_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run a shell command check."""
        check_id, severity = check["id"], Severity(check.get("severity", "required"))
        check_name, timeout = check.get("name", check_id), check.get("timeout", settings.get("default_timeout", 300))
        command = self._substitute_variables(check["command"])
        wd = self._substitute_variables(check.get("working_dir", settings.get("working_dir", ".")))
        cwd = wd if os.path.isabs(wd) else str(self.project_root / wd)

        try:
            r = subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=timeout, cwd=cwd)
            output, ok = r.stdout + r.stderr, r.returncode == 0
            # Indicators override exit code
            for ind in check.get("failure_indicators", []):
                ok = ok and ind not in output
            for ind in check.get("success_indicators", []):
                ok = ok or ind in output

            pattern = check.get("error_parser", {}).get("pattern", "")
            errors = [m.groupdict() for m in re.finditer(pattern, output)][:50] if pattern else []
            return CheckResult(check_id=check_id, check_name=check_name, severity=severity, errors=errors if not ok else [],
                               status=CheckStatus.PASSED if ok else CheckStatus.FAILED, output=output[:5000],
                               message=check.get("message") or f"Command {'succeeded' if ok else 'failed'}",
                               details=f"Exit code: {r.returncode}")
        except Exception as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR, severity=severity,
                               message=f"Command timed out after {timeout}s" if "TimeoutExpired" in type(e).__name__ else str(e))

    # --- Regex Check ---

    def _collect_files_for_check(self, include_patterns: list, exclude_patterns: list) -> list:
        """Collect files matching include patterns, excluding those matching exclude patterns."""
        all_files = []
        for pattern in include_patterns:
            pattern = self._substitute_variables(pattern)
            matches = glob.glob(str(self.project_root / pattern), recursive=True)
            all_files.extend(matches)

        files = []
        for f in all_files:
            rel_path = os.path.relpath(f, self.project_root)
            excluded = any(
                fnmatch.fnmatch(rel_path, self._substitute_variables(exc))
                for exc in exclude_patterns
            )
            if not excluded:
                files.append(f)
        return files

    def _search_patterns_in_file(self, file_path: str, patterns: list) -> list:
        """Search for patterns in a single file, returning matches."""
        matches = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for pat_def in patterns:
                pat_name = pat_def.get("name", "pattern")
                pattern = pat_def["pattern"]
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    rel_path = os.path.relpath(file_path, self.project_root)
                    matches.append({
                        "file": rel_path, "line": line_num,
                        "pattern_name": pat_name, "match": match.group()[:100],
                    })
        except Exception:
            pass
        return matches

    def _run_regex_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run a regex pattern check on source files."""
        check_id, severity = check["id"], Severity(check.get("severity", "required"))
        check_name = check.get("name", check_id)

        patterns = check.get("patterns") or [{"name": "pattern", "pattern": check.get("pattern", "")}]
        files = self._collect_files_for_check(
            check.get("file_patterns", settings.get("include_patterns", ["**/*.cs"])),
            check.get("exclude_patterns", settings.get("exclude_patterns", [])))

        matches_found = [m for f in files for m in self._search_patterns_in_file(f, patterns)]
        found_count, negative_match = len(matches_found), check.get("negative_match", False)
        passed = (found_count == 0) == negative_match or (found_count > 0) != negative_match

        errors = [{"file": m["file"], "line": m["line"], "match": m["match"]} for m in matches_found[:20]] if not passed else []
        msg = check.get("message") or (f"Found {found_count} match(es)" if passed else "Pattern match failed")

        return CheckResult(check_id=check_id, check_name=check_name, severity=severity, errors=errors,
                           status=CheckStatus.PASSED if passed else CheckStatus.FAILED, message=msg,
                           details=f"Searched {len(files)} files, found {found_count} matches")

    # --- File Exists Check ---

    def _run_file_exists_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Check if required files exist."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        files = check.get("files", [])
        missing = []
        found = []

        for file_spec in files:
            if isinstance(file_spec, str):
                file_path = file_spec
                file_message = f"{file_spec} not found"
            else:
                file_path = file_spec.get("path")
                file_message = file_spec.get("message", f"{file_path} not found")

            file_path = self._substitute_variables(file_path)
            full_path = self.project_root / file_path

            if full_path.exists():
                found.append(file_path)
            else:
                missing.append({"path": file_path, "message": file_message})

        passed = len(missing) == 0

        return CheckResult(
            check_id=check_id, check_name=check_name,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            severity=severity,
            message=check.get("message", "All required files exist") if passed else f"Missing {len(missing)} file(s)",
            errors=missing,
            details=f"Found {len(found)} of {len(files)} required files",
        )

    # --- Import Check ---

    def _find_forbidden_import_violations(self, source_file: str, forbidden_imports: list,
                                           rule_message: str) -> list:
        """Check a single file for forbidden import violations."""
        violations = []
        try:
            with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.split("\n")
            using_pattern = r"using\s+([a-zA-Z0-9_.]+)\s*;"
            usings = re.findall(using_pattern, content)
            rel_path = os.path.relpath(source_file, self.project_root)

            for using in usings:
                for forbidden in forbidden_imports:
                    if forbidden in using:
                        # Find line number of using statement
                        line_num = next((i for i, ln in enumerate(lines, 1) if f"using {using}" in ln), None)
                        violations.append({
                            "file": rel_path, "line": line_num, "import": using,
                            "forbidden": forbidden, "message": rule_message,
                        })
        except Exception:
            pass
        return violations

    def _run_import_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Check import/dependency rules (layer isolation)."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        rules = check.get("rules", [])
        violations = []

        for rule in rules:
            source_pattern = self._substitute_variables(rule["source_pattern"])
            forbidden_imports = rule.get("forbidden_imports", [])
            rule_message = rule.get("message", "Forbidden import")

            source_files = glob.glob(str(self.project_root / source_pattern), recursive=True)
            for source_file in source_files:
                violations.extend(self._find_forbidden_import_violations(
                    source_file, forbidden_imports, rule_message))

        passed = len(violations) == 0
        return CheckResult(
            check_id=check_id, check_name=check_name,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            severity=severity,
            message=check.get("message", "Layer dependencies OK") if passed else f"Found {len(violations)} violation(s)",
            errors=violations[:20], details=f"Checked {len(rules)} rules",
        )

    # --- Custom Check ---

    def _load_custom_function(self, function_path: str) -> Callable:
        """Load a custom function from module.function path."""
        parts = function_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid function path: {function_path}")

        module_name, func_name = parts
        tools_dir = Path(__file__).parent
        module_file = tools_dir / f"{module_name}.py"

        if module_file.exists():
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            module = importlib.import_module(module_name)

        return getattr(module, func_name)

    def _convert_custom_result(self, result: Any, check_id: str, check_name: str,
                                severity: Severity, default_message: str) -> CheckResult:
        """Convert custom function result to CheckResult."""
        if isinstance(result, CheckResult):
            return result
        if isinstance(result, dict):
            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if result.get("passed", False) else CheckStatus.FAILED,
                severity=severity, message=result.get("message", default_message),
                errors=result.get("errors", []), details=result.get("details"),
            )
        if isinstance(result, bool):
            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if result else CheckStatus.FAILED,
                severity=severity, message=default_message,
            )
        return CheckResult(
            check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
            severity=severity, message=f"Custom check returned unexpected type: {type(result)}",
        )

    def _run_custom_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run a custom Python function check."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        function_path = check.get("function")
        parameters = {k: self._substitute_variables(v) if isinstance(v, str) else v
                      for k, v in check.get("parameters", {}).items()}

        try:
            func = self._load_custom_function(function_path)
            result = func(project_root=self.project_root, context=self.context, **parameters)
            return self._convert_custom_result(result, check_id, check_name, severity, check.get("message", ""))
        except Exception as e:
            return CheckResult(
                check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                severity=severity, message=f"Custom check failed: {str(e)}", details=str(e),
            )

    # --- Contracts Check ---

    def _run_contracts_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run contract-based checks using the contracts module."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        try:
            results, error_msg = get_contract_results(check, self.project_root)
            if error_msg:
                return CheckResult(check_id=check_id, check_name=check_name,
                                   status=CheckStatus.ERROR, severity=severity, message=error_msg)

            stats = aggregate_contract_stats(results)
            passed = stats["all_passed"] and (stats["warnings"] == 0 if check.get("fail_on_warning") else True)

            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity, message=build_contract_message(results, stats),
                errors=build_contract_errors(results)[:50],
                details=f"Contracts: {', '.join(r.contract_name for r in results)}",
            )

        except ImportError as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                               severity=severity, message=f"Could not import contracts module: {e}")
        except Exception as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                               severity=severity, message=f"Contracts check failed: {str(e)}", details=str(e))

    # --- LSP Query Check (Pyright) ---

    def _run_lsp_query_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run semantic Python analysis using pyright CLI."""
        check_id, severity = check["id"], Severity(check.get("severity", "required"))
        check_name = check.get("name", check_id)

        try:
            files = self._collect_files_for_check(
                check.get("file_patterns", settings.get("include_patterns", ["**/*.py"])),
                check.get("exclude_patterns", settings.get("exclude_patterns", [])))
            file_set = {str(Path(f).resolve()) for f in files}
            severity_filter = set(check.get("severity_filter", ["error"]))

            result = self.pyright_runner.check_project()
            filtered = [d for d in result.diagnostics
                        if str(Path(d.file).resolve()) in file_set and d.severity in severity_filter]

            errors = [{"file": os.path.relpath(d.file, self.project_root), "line": d.line, "column": d.column,
                       "message": d.message, "rule": d.rule, "severity": d.severity} for d in filtered[:50]]
            passed = len(filtered) == 0
            msg = f"Type check passed ({result.files_analyzed} files)" if passed else f"Found {len(filtered)} type issues"

            return CheckResult(check_id=check_id, check_name=check_name, severity=severity, errors=errors,
                               status=CheckStatus.PASSED if passed else CheckStatus.FAILED, message=msg,
                               details=f"Analyzed {len(files)} files, {result.error_count} errors, {result.warning_count} warnings")

        except Exception as e:
            msg = str(e) if isinstance(e, RuntimeError) else f"LSP query check failed: {e}"
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR, severity=severity, message=msg)

    # --- AST Check ---

    def _run_ast_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run AST-based code quality checks using Python's ast module."""
        import ast

        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        try:
            config = check.get("config", {})
            metric = config.get("metric", "")
            max_value = config.get("max_value", 10)

            include_patterns = check.get("file_patterns", settings.get("include_patterns", ["**/*.py"]))
            exclude_patterns = check.get("exclude_patterns", settings.get("exclude_patterns", []))
            files = [Path(f) for f in self._collect_files_for_check(include_patterns, exclude_patterns)]

            violations = self._collect_ast_violations(files, metric, max_value)

            errors = [{
                "file": os.path.relpath(v["file"], self.project_root),
                "line": v.get("line"), "function": v.get("function"),
                "value": v.get("value"), "max": max_value, "message": v.get("message"),
            } for v in violations[:50]]

            passed = len(violations) == 0
            message = (f"Found {len(violations)} {metric} violations (max: {max_value})"
                       if not passed else f"All {len(files)} files pass {metric} check (max: {max_value})")

            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity, message=message, errors=errors,
                details=f"Checked {len(files)} files for {metric}",
            )

        except Exception as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                               severity=severity, message=f"AST check failed: {str(e)}", details=str(e))

    def _collect_ast_violations(self, files: List[Path], metric: str, max_value: int) -> list:
        """Collect AST violations across files."""
        import ast

        violations = []
        for file_path in files:
            try:
                source = file_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source)
                violations.extend(self.ast_checker.check_metric(tree, source, metric, max_value, file_path))
            except SyntaxError:
                continue
        return violations
