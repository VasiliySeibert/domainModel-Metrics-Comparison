"""
Unit tests for PlantUML parser components.

Tests individual parsing functions with known inputs to ensure
correct handling of all PlantUML syntax patterns.
"""

import pytest
from TestingMetrics.dummyMetric.Parser.parser import PlantUMLParser
from TestingMetrics.dummyMetric.Parser.models import (
    ParsedModel,
    ParsedClass,
    ParsedEnum,
    ParsedRelationship,
    ParsedAttribute,
    RelationshipType,
)


class TestBasicAssociations:
    """Test parsing of basic association relationships."""

    def test_simple_association(self):
        """Test: A -- B"""
        uml = """@startuml
A -- B
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.relationships) == 1
        rel = model.relationships[0]
        assert rel.source == "A"
        assert rel.target == "B"
        assert rel.relationship_type == RelationshipType.ASSOCIATION

    def test_association_with_cardinalities(self):
        """Test: A "1" -- "*" B"""
        uml = """@startuml
A "1" -- "*" B
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.relationships) == 1
        rel = model.relationships[0]
        assert rel.source_cardinality == "1"
        assert rel.target_cardinality == "*"

    def test_association_with_label(self):
        """Test: A -- B : contains"""
        uml = """@startuml
A "1" -- "*" B : contains
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        rel = model.relationships[0]
        assert rel.label == "contains"

    def test_directed_association(self):
        """Test: A --> B"""
        uml = """@startuml
A --> B
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        rel = model.relationships[0]
        assert rel.relationship_type == RelationshipType.DIRECTED_ASSOCIATION


class TestInheritance:
    """Test parsing of inheritance relationships."""

    def test_inheritance_left(self):
        """Test: Parent <|-- Child"""
        uml = """@startuml
Parent <|-- Child
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.relationships) == 1
        rel = model.relationships[0]
        assert rel.relationship_type == RelationshipType.INHERITANCE
        assert rel.source == "Parent"
        assert rel.target == "Child"

    def test_inheritance_right(self):
        """Test: Child --|> Parent"""
        uml = """@startuml
Child --|> Parent
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        rel = model.relationships[0]
        assert rel.relationship_type == RelationshipType.INHERITANCE
        # After normalization, parent should be source
        assert rel.source == "Parent"
        assert rel.target == "Child"


class TestComposition:
    """Test parsing of composition relationships."""

    def test_composition_left(self):
        """Test: Whole *-- Part"""
        uml = """@startuml
Whole *-- Part
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        rel = model.relationships[0]
        assert rel.relationship_type == RelationshipType.COMPOSITION
        assert rel.source == "Whole"
        assert rel.target == "Part"

    def test_composition_with_cardinalities(self):
        """Test: Composite "1" *-- "*" Component"""
        uml = """@startuml
Composite "1" *-- "*" Component
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        rel = model.relationships[0]
        assert rel.source_cardinality == "1"
        assert rel.target_cardinality == "*"


class TestAggregation:
    """Test parsing of aggregation relationships."""

    def test_aggregation_left(self):
        """Test: Whole o-- Part"""
        uml = """@startuml
Whole o-- Part
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        rel = model.relationships[0]
        assert rel.relationship_type == RelationshipType.AGGREGATION

    def test_aggregation_with_label(self):
        """Test: Department o-- Employee : employs"""
        uml = """@startuml
Department "1" o-- "*" Employee : employs
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        rel = model.relationships[0]
        assert rel.label == "employs"


class TestClassDefinitions:
    """Test parsing of explicit class definitions."""

    def test_empty_class(self):
        """Test: class Person {}"""
        uml = """@startuml
class Person {}
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.classes) == 1
        cls = model.classes[0]
        assert cls.name == "Person"
        assert cls.is_abstract == False
        assert len(cls.attributes) == 0

    def test_class_with_attributes(self):
        """Test class with typed attributes."""
        uml = """@startuml
class Person {
    name : String
    age : Integer
}
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        cls = model.classes[0]
        assert len(cls.attributes) == 2
        assert cls.attributes[0].name == "name"
        assert cls.attributes[0].type == "String"
        assert cls.attributes[1].name == "age"
        assert cls.attributes[1].type == "Integer"

    def test_abstract_class(self):
        """Test: abstract class Person {}"""
        uml = """@startuml
abstract class Person {
    id
}
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        cls = model.classes[0]
        assert cls.is_abstract == True

    def test_class_with_default_value(self):
        """Test attribute with default value."""
        uml = """@startuml
class Config {
    maxRetries : Integer = 3
}
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        attr = model.classes[0].attributes[0]
        assert attr.name == "maxRetries"
        assert attr.type == "Integer"
        assert attr.default_value == "3"


class TestEnumDefinitions:
    """Test parsing of enum definitions."""

    def test_multiline_enum(self):
        """Test multi-line enum definition."""
        uml = """@startuml
enum Status {
    Active
    Inactive
    Pending
}
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.enums) == 1
        enum = model.enums[0]
        assert enum.name == "Status"
        assert len(enum.values) == 3
        assert "Active" in enum.values
        assert "Inactive" in enum.values
        assert "Pending" in enum.values

    def test_inline_enum(self):
        """Test inline enum definition."""
        uml = """@startuml
enum Color { Red, Green, Blue }
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        enum = model.enums[0]
        assert enum.name == "Color"
        assert len(enum.values) == 3
        assert enum.is_inline == True


class TestStandaloneAttributes:
    """Test the old-style standalone attribute syntax."""

    def test_standalone_attribute(self):
        """Test: ClassName : attributeName"""
        uml = """@startuml
Person : name
Person : age
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        # Should create/update a Person class with attributes
        assert len(model.classes) == 1
        cls = model.classes[0]
        assert cls.name == "Person"
        assert len(cls.attributes) == 2


class TestImplicitClasses:
    """Test tracking of implicitly defined classes."""

    def test_implicit_classes_from_relationship(self):
        """Classes mentioned in relationships but not explicitly defined."""
        uml = """@startuml
A -- B
B -- C
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        # All classes are implicit (no explicit definitions)
        assert len(model.classes) == 0
        assert set(model.implicit_classes) == {"A", "B", "C"}

    def test_mixed_explicit_and_implicit(self):
        """Some classes explicit, some implicit."""
        uml = """@startuml
class A {}
A -- B
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.classes) == 1
        assert model.classes[0].name == "A"
        assert model.implicit_classes == ["B"]


class TestComplexScenarios:
    """Test more complex parsing scenarios."""

    def test_multiple_relationships_same_classes(self):
        """Multiple relationships between the same classes."""
        uml = """@startuml
Person "1" -- "*" Order : places
Person "1" -- "*" Address : livesAt
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.relationships) == 2

    def test_class_with_relationship(self):
        """Class definition and relationship together."""
        uml = """@startuml
class Person {
    name : String
}
Person "1" -- "*" Order
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.classes) == 1
        assert len(model.relationships) == 1
        assert "Order" in model.implicit_classes


class TestAssociationClass:
    """Test parsing of association class pattern."""

    def test_association_class(self):
        """Test: (A, B) .. C"""
        uml = """@startuml
(Student, Course) .. Enrollment
@enduml"""
        parser = PlantUMLParser(strict=True)
        model = parser.parse(uml)

        assert len(model.relationships) == 1
        rel = model.relationships[0]
        assert rel.relationship_type == RelationshipType.ASSOCIATION_CLASS
        assert rel.association_members == ("Student", "Course")
        assert rel.target == "Enrollment"


class TestErrorHandling:
    """Test error handling in strict mode."""

    def test_strict_mode_unrecognized_line(self):
        """Strict mode should raise on unrecognized syntax."""
        uml = """@startuml
this is not valid PlantUML syntax!!!!
@enduml"""
        parser = PlantUMLParser(strict=True)

        with pytest.raises(ValueError) as exc_info:
            parser.parse(uml)

        assert "Unrecognized line" in str(exc_info.value)

    def test_non_strict_mode(self):
        """Non-strict mode should skip unrecognized lines."""
        uml = """@startuml
A -- B
this is not valid
C -- D
@enduml"""
        parser = PlantUMLParser(strict=False)
        model = parser.parse(uml)

        # Should have parsed the valid relationships
        assert len(model.relationships) == 2
        assert len(parser.warnings) > 0
