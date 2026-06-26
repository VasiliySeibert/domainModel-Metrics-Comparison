import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "Developing-DISS-Metric"))

from Parser import PlantUMLParser
from metric import metric
from metric_interface import validate_metric_result

instructor_model_str = """
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

student_model_str = """
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

parser = PlantUMLParser(strict=True)
parsed_instructor = parser.parse(instructor_model_str)
parsed_student = parser.parse(student_model_str)

result = metric(parsed_instructor, parsed_student)

print("Result:", result)

assert validate_metric_result(result), "validate_metric_result failed"
assert all(0.0 <= v <= 1.0 for v in result.values()), "Scores out of bounds"

print(f"class_score:       {result['class_score']:.4f}")
print(f"attribute_score:   {result['attribute_score']:.4f}")
print(f"association_score: {result['association_score']:.4f}")
print("All assertions passed.")
