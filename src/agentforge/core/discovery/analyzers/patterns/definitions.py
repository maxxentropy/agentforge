"""
Pattern Definitions
===================

Code pattern definitions with detection signals.
"""

# Pattern definitions with detection signals
PATTERN_DEFINITIONS = {
    "result_type": {
        "description": "Result<T> or similar error handling pattern",
        "signals": {
            "class_name": {
                # Python and C# Result types
                "patterns": [r"^Result$", r"^Result\[", r"^Result<", r"^Either$", r"^Option$", r"^ErrorOr<"],
                "weight": 0.9,
            },
            "return_type": {
                "patterns": [r"Result\[", r"Result$", r"Result<", r"Either\[", r"Option\[", r"ErrorOr<"],
                "weight": 0.8,
            },
            "import": {
                # Python and C# imports
                "patterns": [r"from.*result.*import", r"from.*returns.*import", r"using.*Result", r"using.*ErrorOr"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.5,
    },
    "mediatr_cqrs": {
        "description": "MediatR CQRS pattern (IRequest/IRequestHandler)",
        "signals": {
            "base_class": {
                "patterns": [r"IRequest<", r"IRequest$", r"IRequestHandler<", r"INotification$", r"INotificationHandler<"],
                "weight": 1.0,
            },
            "class_suffix": {
                "patterns": [r"Command$", r"Query$", r"CommandHandler$", r"QueryHandler$"],
                "weight": 0.8,
            },
            "import": {
                "patterns": [r"using MediatR", r"using.*MediatR"],
                "weight": 0.9,
            },
            "directory": {
                "patterns": [r"Commands?", r"Queries?", r"Handlers?"],
                "weight": 0.6,
            },
        },
        "min_confidence": 0.5,
        # At least one of these signals must be present (not just naming)
        "required_signals": ["base_class", "import"],
    },
    "ddd_entity": {
        "description": "DDD Entity pattern with typed ID",
        "signals": {
            "base_class": {
                "patterns": [r"Entity<", r"Entity$", r"AggregateRoot<", r"AggregateRoot$", r"BaseEntity"],
                "weight": 0.9,
            },
            "property": {
                "patterns": [r"public.*Id\s*{", r"protected.*Id\s*{"],
                "weight": 0.6,
            },
            "directory": {
                "patterns": [r"[Ee]ntities", r"[Dd]omain", r"[Aa]ggregates"],
                "weight": 0.5,
            },
        },
        "min_confidence": 0.5,
    },
    "ddd_value_object": {
        "description": "DDD Value Object pattern (immutable, equality by value)",
        "signals": {
            "base_class": {
                "patterns": [r"ValueObject$", r"ValueObject<"],
                "weight": 0.9,
            },
            "class_suffix": {
                "patterns": [r"Id$", r"Email$", r"Address$", r"Money$", r"Name$"],
                "weight": 0.5,
            },
            "attribute": {
                "patterns": [r"record\s+struct", r"readonly\s+struct"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.5,
    },
    "interface_prefix": {
        "description": "I-prefix interface naming convention",
        "signals": {
            "class_name": {
                "patterns": [r"^I[A-Z][a-zA-Z]+$"],
                "weight": 0.9,
            },
        },
        "min_confidence": 0.7,
    },
    "cqrs": {
        "description": "Command Query Responsibility Segregation",
        "signals": {
            "class_suffix": {
                "patterns": [r"Command$", r"Query$", r"Handler$"],
                "weight": 0.8,
            },
            "directory": {
                "patterns": [r"commands?", r"queries?", r"handlers?"],
                "weight": 0.7,
            },
            "base_class": {
                "patterns": [r"ICommand", r"IQuery", r"IRequest", r"BaseCommand", r"BaseQuery"],
                "weight": 0.9,
            },
        },
        "min_confidence": 0.5,
        # Require actual CQRS base classes, not just naming conventions
        "required_signals": ["base_class"],
    },
    "repository": {
        "description": "Repository pattern for data access abstraction",
        "signals": {
            "class_suffix": {
                "patterns": [r"Repository$", r"Repo$"],
                "weight": 0.9,
            },
            "directory": {
                "patterns": [r"repositories", r"repos", r"persistence"],
                "weight": 0.7,
            },
            "method_names": {
                "patterns": [r"get_by_id", r"find_all", r"save", r"delete", r"add"],
                "weight": 0.6,
            },
            "base_class": {
                "patterns": [r"IRepository", r"BaseRepository", r"Repository"],
                "weight": 0.8,
            },
        },
        "min_confidence": 0.5,
    },
    "dependency_injection": {
        "description": "Dependency Injection pattern",
        "signals": {
            "decorator": {
                "patterns": [r"@inject", r"@Inject", r"@autowired"],
                "weight": 0.9,
            },
            "constructor_params": {
                "patterns": [r"__init__.*:.*"],
                "weight": 0.5,
            },
            "import": {
                "patterns": [r"from.*inject.*import", r"from.*dependency_injector"],
                "weight": 0.8,
            },
        },
        "min_confidence": 0.5,
    },
    "factory": {
        "description": "Factory pattern for object creation",
        "signals": {
            "class_suffix": {
                "patterns": [r"Factory$"],
                "weight": 0.9,
            },
            "method_prefix": {
                "patterns": [r"^create_", r"^build_", r"^make_"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.5,
    },
    "singleton": {
        "description": "Singleton pattern",
        "signals": {
            "method_name": {
                "patterns": [r"get_instance", r"getInstance", r"instance"],
                "weight": 0.8,
            },
            "class_variable": {
                "patterns": [r"_instance", r"__instance"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.6,
    },
    "decorator_pattern": {
        "description": "Decorator pattern (not Python decorators)",
        "signals": {
            "class_suffix": {
                "patterns": [r"Decorator$", r"Wrapper$"],
                "weight": 0.9,
            },
            "wrapped_attribute": {
                "patterns": [r"_wrapped", r"_inner", r"_component"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.6,
    },
    "strategy": {
        "description": "Strategy pattern for interchangeable algorithms",
        "signals": {
            "class_suffix": {
                "patterns": [r"Strategy$", r"Policy$"],
                "weight": 0.9,
            },
            "base_class": {
                "patterns": [r"Strategy", r"Policy", r"ABC"],
                "weight": 0.6,
            },
        },
        "min_confidence": 0.6,
    },
    "value_object": {
        "description": "Value Object pattern (immutable domain objects)",
        "signals": {
            "decorator": {
                "patterns": [r"@dataclass.*frozen.*True", r"@frozen", r"@value"],
                "weight": 0.9,
            },
            "base_class": {
                "patterns": [r"ValueObject", r"NamedTuple"],
                "weight": 0.8,
            },
            "directory": {
                "patterns": [r"value_objects?", r"domain"],
                "weight": 0.5,
            },
        },
        "min_confidence": 0.5,
    },
    "entity": {
        "description": "Domain Entity pattern (identity-based objects)",
        "signals": {
            "base_class": {
                "patterns": [r"Entity$", r"BaseEntity", r"AggregateRoot"],
                "weight": 0.9,
            },
            "attribute": {
                "patterns": [r"^id$", r"^_id$", r"entity_id"],
                "weight": 0.6,
            },
            "directory": {
                "patterns": [r"entities", r"domain", r"models"],
                "weight": 0.5,
            },
        },
        "min_confidence": 0.5,
    },
}
