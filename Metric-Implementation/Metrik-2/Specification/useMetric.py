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

    # Add the metric root directory to path so Parser module can be found
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from Parser import PlantUMLParser
    from Specification.metric import metric

    parser = PlantUMLParser(strict=True)
    parsed_student = parser.parse(student_model)
    parsed_instructor = parser.parse(instructor_model)

    result = metric(parsed_instructor, parsed_student)
    print(result)
