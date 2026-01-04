# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: fix-workflow-validation

"""
Validation Mixin
================

Python file validation methods for the fix workflow.
Validates syntax and imports before accepting modifications.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any


class ValidationMixin:
    """
    Python validation methods for fix workflow.

    Provides fast validation of Python files before expensive test verification.
    """

    # Type hints for mixin - provided by main class
    project_path: Path

    def _validate_python_file(self, file_path: Path) -> str | None:
        """
        Validate a Python file for syntax and import errors.

        Returns None if valid, or an error message if invalid.
        This catches:
        1. Syntax errors (ast.parse)
        2. Undefined names at module level (import check)

        This is a FAST check that runs before the slower test verification.
        """
        import ast

        if file_path.suffix != '.py':
            return None  # Only validate Python files

        if not file_path.exists():
            return f"File does not exist: {file_path}"

        try:
            source = file_path.read_text()
        except Exception as e:
            return f"Cannot read file: {e}"

        # Step 1: Check syntax with ast.parse
        try:
            ast.parse(source)
        except SyntaxError as e:
            return f"Syntax error at line {e.lineno}: {e.msg}"

        # Step 2: Try to compile and import to catch undefined names
        module_path = str(file_path.resolve())

        check_script = f'''
import sys
import importlib.util
try:
    spec = importlib.util.spec_from_file_location("_check_module", {repr(module_path)})
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("OK")
except AttributeError as e:
    print(f"AttributeError: {{e}}")
    sys.exit(1)
except NameError as e:
    print(f"NameError: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"{{type(e).__name__}}: {{e}}")
    sys.exit(1)
'''

        try:
            result = subprocess.run(
                [sys.executable, "-c", check_script],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.project_path),
                env={**subprocess.os.environ, "PYTHONPATH": str(self.project_path)}
            )

            if result.returncode != 0:
                error_msg = result.stdout.strip() or result.stderr.strip()
                return f"Import validation failed: {error_msg}"

        except subprocess.TimeoutExpired:
            return "Import validation timed out"
        except Exception:
            # If subprocess fails, fall back to just syntax check (already passed)
            pass

        return None  # All validations passed

    def _validate_extraction_suggestions(
        self,
        suggestions: list[dict[str, Any]],
        file_path: Path,
    ) -> list[dict[str, Any]]:
        """
        Validate extraction suggestions using the refactoring provider.

        Returns only suggestions that pass validation.
        """
        from ....refactoring.registry import get_refactoring_provider

        if not suggestions:
            return []

        provider = get_refactoring_provider(file_path)
        if not provider:
            return suggestions  # Can't validate, return all

        validated = []
        for suggestion in suggestions:
            if suggestion.get("type") != "extract_function":
                validated.append(suggestion)
                continue

            # Validate extraction coordinates
            start_line = suggestion.get("start_line", 0)
            end_line = suggestion.get("end_line", 0)

            if start_line and end_line:
                is_valid = provider.validate_extract_function(
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                )
                if is_valid:
                    validated.append(suggestion)

        return validated
