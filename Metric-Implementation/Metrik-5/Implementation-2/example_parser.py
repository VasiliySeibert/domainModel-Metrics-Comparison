instructor_model = """
@startuml

class PISystem

class Person {
    String name
    String address
}

class Role

class Victim

class PoliceStation {
    String address
}

class PoliceOfficer {
    int badgeNumber
}

class Case {
    Date startDate
    Date endDate
}

Role <|-- Victim
Role <|-- PoliceOfficer

Person "1" -- "1..2" Role : roles
PISystem "1" -- "0..*" Person : persons

PISystem *-- "0..*" Victim
Victim "0..*" -- "1..*" Case

PISystem "1" *-- "0..*" Case
PISystem "1" *-- "0..*" PoliceStation 
PoliceStation "1" -- "0..*" PoliceOfficer : workLocation
PoliceOfficer "0..*" -- "0..*" Case : worksOnCases
PISystem "1" *-- "0..*" PoliceOfficer

@enduml
"""

student_model = """
@startuml

class PISystem

class Person {
  String name
  String address
}

class Victim
class PoliceOfficer {
  String badgeNumber
}

class PoliceStation {
  String address
}

class Cases {
  String objective
  Date startDate
}

' Inheritance
Person <|-- Victim
Person <|-- PoliceOfficer

PISystem "1" *-- "0..*" Person : persons
PISystem "1" *-- "0..*" PoliceStation : policeStations
PISystem "1" *-- "0..*" Cases : cases

PoliceStation "1" *-- "0..*" PoliceOfficer
Victim "0..*" -- "1..*" Cases : victims
PoliceOfficer "1" -- "0..*" Cases : assignedOfficer

@enduml
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add Developing-DISS-Metric directory to path so Parser module can be found
    sys.path.insert(0, str(Path(__file__).resolve().parent / "Developing-DISS-Metric"))

    from Parser import PlantUMLParser

    parser = PlantUMLParser(strict=True)
    parsed_student = parser.parse(student_model)
    parsed_instructor = parser.parse(instructor_model)

    ### your code here, fix this
    # Class names
    classes = [c.name for c in parsed_student.classes]
    print("Classes:", classes)

    # Attributes per class
    for c in parsed_student.classes:
        if c.attributes:
            print(f"{c.name} attributes: {[str(a) for a in c.attributes]}")

    # Relationships
    for r in parsed_student.relationships:
        print(f"{r.source} -- {r.target} [{r.relationship_type.value}]")
    # All class names (including implicit ones mentioned only in relationships)
    print("All names:", parsed_student.all_class_names)
