# PlantUML Parser

A robust parser for PlantUML class diagrams that converts PlantUML text into structured Python data objects. Designed specifically for parsing the UML models in the dissertation dataset.

## Overview

This parser handles all PlantUML syntax patterns found in `Dataset/combined-data.json`, including:
- Class definitions (regular and abstract)
- Enum definitions (block and inline)
- All relationship types (association, inheritance, composition, aggregation)
- Attributes with various formats
- Comments and notes

## Quick Start

```python
from TestingMetrics.dummyMetric.Parser import PlantUMLParser

parser = PlantUMLParser(strict=True)
model = parser.parse(plantuml_string)

print(f"Classes: {len(model.classes)}")
print(f"Enums: {len(model.enums)}")
print(f"Relationships: {len(model.relationships)}")
```

## Installation

The parser is part of the `TestingMetrics.dummyMetric` package. No additional dependencies required beyond the standard library.

## Supported Syntax

### Classes

| Syntax | Example |
|--------|---------|
| Empty class | `class Person {}` |
| Class with attributes | `class Person { name }` |
| Abstract class | `abstract class Entity { id }` |
| Typed attributes (UML) | `name : String` |
| Typed attributes (Java) | `String name` |
| Default values | `status : Status = Active` |
| Constants | `const Integer MAX = 100` |

### Enums

| Syntax | Example |
|--------|---------|
| Block format | `enum Status { Active, Inactive }` |
| Multi-line block | `enum Status {\n  Active\n  Inactive\n}` |
| Inline (nested) | `enum DeviceStatus { On, Off }` inside class |
| Ellipsis (truncated) | `enum Type { A, B, ... }` |

### Relationships

| Arrow | Type | Example |
|-------|------|---------|
| `--` | Association | `A -- B` |
| `-->` | Directed Association | `A --> B` |
| `<--` | Directed Association (reverse) | `A <-- B` |
| `<\|--` | Inheritance | `Parent <\|-- Child` |
| `--\|>` | Inheritance (reverse) | `Child --\|> Parent` |
| `-\|>` | Inheritance (single dash) | `Child -\|> Parent` |
| `*--` | Composition | `Whole *-- Part` |
| `--*` | Composition (reverse) | `Part --* Whole` |
| `*-->` | Directed Composition | `Whole *--> Part` |
| `o--` | Aggregation | `Whole o-- Part` |
| `--o` | Aggregation (reverse) | `Part --o Whole` |
| `..` | Dependency | `A .. B` |
| `(A, B) .. C` | Association Class | `(Student, Course) .. Enrollment` |

### Cardinalities

All standard UML cardinalities are supported:
- `"1"` - Exactly one
- `"*"` or `"0..*"` - Many
- `"0..1"` - Optional
- `"1..*"` - One or more
- `"n..m"` - Range (e.g., `"2..4"`, `"0..32"`)

### Labels

Relationship labels after colon:
```
A "1" --> "*" B : contains
```

### Comments

| Style | Example |
|-------|---------|
| Single quote | `' This is a comment` |
| Double slash | `// This is a comment` |
| Block comment | `/' Multi-line comment '/` |

### Notes

```
note right of ClassName
This is a multi-line
note about the class.
end note
```

## Output Data Model

### ParsedModel

The top-level container returned by the parser:

```python
@dataclass
class ParsedModel:
    classes: List[ParsedClass]          # Explicitly defined classes
    enums: List[ParsedEnum]             # Standalone enums
    relationships: List[ParsedRelationship]
    notes: List[ParsedNote]
    raw_source: str                     # Original PlantUML
    implicit_classes: List[str]         # Classes only mentioned in relationships
```

### ParsedClass

```python
@dataclass
class ParsedClass:
    name: str
    is_abstract: bool
    attributes: List[ParsedAttribute]
    nested_enums: List[ParsedEnum]      # Enums defined inside the class
```

### ParsedAttribute

```python
@dataclass
class ParsedAttribute:
    name: str
    type: Optional[str]                 # None if untyped
    default_value: Optional[str]
    is_constant: bool
```

### ParsedEnum

```python
@dataclass
class ParsedEnum:
    name: str
    values: List[str]
    is_inline: bool                     # True if defined inside a class
```

### ParsedRelationship

```python
@dataclass
class ParsedRelationship:
    source: str
    target: str
    relationship_type: RelationshipType
    source_cardinality: Optional[str]
    target_cardinality: Optional[str]
    label: Optional[str]
    association_members: Optional[tuple] # For association classes: (Class1, Class2)
```

### RelationshipType

```python
class RelationshipType(Enum):
    ASSOCIATION = "association"
    DIRECTED_ASSOCIATION = "directed"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    DEPENDENCY = "dependency"
    ASSOCIATION_CLASS = "association_class"
```

## API Reference

### PlantUMLParser

```python
class PlantUMLParser:
    def __init__(self, strict: bool = True):
        """
        Args:
            strict: If True, raises ValueError on unrecognized syntax.
                    If False, skips unrecognized lines with warnings.
        """

    def parse(self, uml_string: str) -> ParsedModel:
        """
        Parse a PlantUML string into a ParsedModel.

        Args:
            uml_string: Complete PlantUML with @startuml/@enduml markers.

        Returns:
            ParsedModel containing all extracted elements.

        Raises:
            ValueError: If strict=True and unrecognized syntax encountered.
        """

    @property
    def warnings(self) -> List[str]:
        """Get warnings from last parse (when strict=False)."""
```

### Convenience Properties

```python
model = parser.parse(uml_string)

# Get all class names (explicit + implicit)
model.all_class_names  # -> List[str]

# Get all enum names (standalone + nested)
model.all_enum_names   # -> List[str]

# Find a specific class
model.get_class("Person")  # -> ParsedClass or None

# Find a specific enum
model.get_enum("Status")   # -> ParsedEnum or None

# Summary string
model.summary()  # -> "ParsedModel: 12 classes, 3 enums, 12 relationships, 0 implicit classes"
```

## Test Runner

The parser includes an iterative test runner for development and validation.

### Command Line Usage

```bash
# Test all PlantUML strings in dataset
python -m TestingMetrics.dummyMetric.Parser.test_runner

# Test only reference models (faster)
python -m TestingMetrics.dummyMetric.Parser.test_runner --references-only

# Continue past failures (don't stop on first error)
python -m TestingMetrics.dummyMetric.Parser.test_runner --no-stop

# Test a specific model
python -m TestingMetrics.dummyMetric.Parser.test_runner --model LabTracker --setting reference

# Save report to JSON
python -m TestingMetrics.dummyMetric.Parser.test_runner --save-report report.json

# List all available models
python -m TestingMetrics.dummyMetric.Parser.test_runner --model LabTracker --setting 0shot
```

### Programmatic Usage

```python
from TestingMetrics.dummyMetric.Parser import PlantUMLParser, ParserTestRunner

parser = PlantUMLParser(strict=True)
runner = ParserTestRunner(parser)

# Run all tests
report = runner.run_all(stop_on_failure=True)
report.print_summary()

# Run specific model
result = runner.run_specific("LabTracker", "reference")
print(result.detailed_report())

# Get available models
models = runner.get_model_keys()  # ['LabTracker', 'CelO', 'TSS', ...]
```

## Qualitative Testing

For manual inspection of parsing results:

```bash
# List all available indices
python TestingMetrics/dummyMetric/Parser/qualitative_test.py --list

# Test specific index (shows original + parsed side by side)
python TestingMetrics/dummyMetric/Parser/qualitative_test.py 0

# Negative indices work (Python-style)
python TestingMetrics/dummyMetric/Parser/qualitative_test.py -1  # Last item
```

## File Structure

```
Parser/
├── __init__.py           # Package exports
├── models.py             # Data classes (ParsedModel, ParsedClass, etc.)
├── tokenizer.py          # Comment removal, block grouping
├── parser.py             # Main PlantUMLParser class
├── test_report.py        # TestResult and TestReport classes
├── test_runner.py        # Iterative test harness
├── qualitative_test.py   # Manual inspection tool
├── example.py            # Legacy example (reference only)
├── specification.txt     # Original requirements
├── README.md             # This file
└── tests/
    ├── __init__.py
    ├── test_parser_unit.py      # 24 unit tests
    └── test_parser_dataset.py   # 18 integration tests
```

## Running Tests

```bash
# All parser tests
pytest TestingMetrics/dummyMetric/Parser/tests/ -v

# Unit tests only
pytest TestingMetrics/dummyMetric/Parser/tests/test_parser_unit.py -v

# Dataset integration tests
pytest TestingMetrics/dummyMetric/Parser/tests/test_parser_dataset.py -v
```

## Examples

### Basic Parsing

```python
from TestingMetrics.dummyMetric.Parser import PlantUMLParser

uml = """
@startuml

class Person {
    name : String
    age : Integer
}

class Address {
    street
    city
}

Person "1" -- "*" Address : livesAt

@enduml
"""

parser = PlantUMLParser(strict=True)
model = parser.parse(uml)

# Access classes
for cls in model.classes:
    print(f"Class: {cls.name}")
    for attr in cls.attributes:
        print(f"  - {attr.name}: {attr.type}")

# Access relationships
for rel in model.relationships:
    print(f"{rel.source} -> {rel.target} ({rel.relationship_type.value})")
```

### Parsing Dataset Models

```python
import json
from TestingMetrics.dummyMetric.Parser import PlantUMLParser

# Load dataset
with open("Dataset/combined-data.json") as f:
    data = json.load(f)

parser = PlantUMLParser(strict=True)

# Parse a reference model
uml = data["models"]["LabTracker"]["reference_plantuml"]
model = parser.parse(uml)
print(model.summary())

# Parse a generated model
uml = data["models"]["LabTracker"]["generated_plantuml"]["0shot"]
model = parser.parse(uml)
print(model.summary())
```

### Non-Strict Mode

```python
parser = PlantUMLParser(strict=False)
model = parser.parse(uml_with_unknown_syntax)

# Check for warnings
if parser.warnings:
    print("Warnings during parsing:")
    for warning in parser.warnings:
        print(f"  - {warning}")
```

## Direction Normalization

The parser normalizes relationship directions for consistency:

| Original | Normalized |
|----------|------------|
| `A <-- B` | `B --> A` (B is source) |
| `Child --\|> Parent` | `Parent <\|-- Child` (Parent is source) |
| `Part --* Whole` | `Whole *-- Part` (Whole is source) |
| `Part --o Whole` | `Whole o-- Part` (Whole is source) |

This ensures:
- **Inheritance**: Parent class is always the source
- **Composition/Aggregation**: Composite/Whole is always the source
- **Directed Association**: Arrow points from source to target

## Known Limitations

1. **Single UML block**: Only parses the first `@startuml...@enduml` block if multiple exist
2. **No method support**: Class methods are not parsed (only attributes)
3. **No stereotype support**: Stereotypes like `<<interface>>` are not parsed
4. **No package support**: Package declarations are ignored
5. **Limited note support**: Notes are captured but position parsing is basic

## Test Coverage

- **47/47** PlantUML strings from dataset parse successfully (100%)
- **24** unit tests covering individual syntax patterns
- **18** integration tests against actual dataset

## Version History

- **1.0.0** - Initial release with full dataset support
