"""
Framework Pattern Definitions
=============================

Framework detection patterns for various languages.
"""

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "pytest": {
        "signals": {
            "import": [r"import pytest", r"from pytest"],
            "decorator": [r"@pytest\.", r"@fixture"],
            "function_prefix": [r"^test_"],
            "file_pattern": [r"test_.*\.py$", r".*_test\.py$"],
        },
        "type": "testing",
    },
    "fastapi": {
        "signals": {
            "import": [r"from fastapi", r"import fastapi"],
            "decorator": [r"@app\.(get|post|put|delete|patch)"],
            "class_base": [r"FastAPI"],
        },
        "type": "web",
    },
    "pydantic": {
        "signals": {
            "import": [r"from pydantic", r"import pydantic"],
            "class_base": [r"BaseModel", r"BaseSettings"],
        },
        "type": "validation",
    },
    "sqlalchemy": {
        "signals": {
            "import": [r"from sqlalchemy", r"import sqlalchemy"],
            "class_base": [r"Base", r"DeclarativeBase"],
            "decorator": [r"@mapper_registry"],
        },
        "type": "orm",
    },
    "click": {
        "signals": {
            "import": [r"import click", r"from click"],
            "decorator": [r"@click\.(command|group|option|argument)"],
        },
        "type": "cli",
    },
    "typer": {
        "signals": {
            "import": [r"import typer", r"from typer"],
            "decorator": [r"@app\.command"],
        },
        "type": "cli",
    },
    # .NET Frameworks
    "mediatr": {
        "signals": {
            "import": [r"using MediatR", r"using.*MediatR"],
            "class_base": [r"IRequest<", r"IRequestHandler<", r"INotification"],
        },
        "type": "cqrs",
    },
    "fluentvalidation": {
        "signals": {
            "import": [r"using FluentValidation", r"using.*FluentValidation"],
            "class_base": [r"AbstractValidator<", r"InlineValidator<"],
        },
        "type": "validation",
    },
    "efcore": {
        "signals": {
            "import": [r"using.*EntityFrameworkCore", r"using Microsoft\.EntityFrameworkCore"],
            "class_base": [r"DbContext$", r"DbSet<"],
        },
        "type": "orm",
    },
    "aspnetcore": {
        "signals": {
            "import": [r"using Microsoft\.AspNetCore", r"using.*AspNetCore"],
            "class_base": [r"ControllerBase$", r"Controller$", r"MinimalApiEndpoint"],
            "attribute": [r"\[ApiController\]", r"\[HttpGet", r"\[HttpPost", r"\[Route\("],
        },
        "type": "web",
    },
    "automapper": {
        "signals": {
            "import": [r"using AutoMapper", r"using.*AutoMapper"],
            "class_base": [r"Profile$", r"IMapper"],
        },
        "type": "mapping",
    },
    "serilog": {
        "signals": {
            "import": [r"using Serilog", r"using.*Serilog"],
        },
        "type": "logging",
    },
    "xunit": {
        "signals": {
            "import": [r"using Xunit", r"using.*Xunit"],
            "attribute": [r"\[Fact\]", r"\[Theory\]", r"\[InlineData"],
        },
        "type": "testing",
    },
    "nunit": {
        "signals": {
            "import": [r"using NUnit", r"using.*NUnit"],
            "attribute": [r"\[Test\]", r"\[TestCase\]", r"\[SetUp\]"],
        },
        "type": "testing",
    },
    "moq": {
        "signals": {
            "import": [r"using Moq", r"using.*Moq"],
            "class_usage": [r"Mock<", r"\.Setup\(", r"\.Verify\("],
        },
        "type": "testing",
    },
}
