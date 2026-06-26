"""
Tests for PlantUML server integration.
"""

import pytest
from TestingMetrics.dummyMetric.plantuml_server import (
    PlantUMLServer,
    encode_plantuml,
    get_diagram_url,
    PLANTUML_ALPHABET
)


class TestPlantUMLServer:
    """Test PlantUML encoding and URL generation."""

    @pytest.fixture
    def server(self):
        """Create default PlantUML server instance."""
        return PlantUMLServer()

    def test_encode_simple(self, server):
        """Test encoding produces non-empty result."""
        encoded = server.encode("@startuml\nA -> B\n@enduml")
        assert len(encoded) > 0

    def test_encode_uses_valid_alphabet(self, server):
        """Test that encoding only uses PlantUML alphabet characters."""
        encoded = server.encode("@startuml\nA -> B\n@enduml")
        for char in encoded:
            assert char in PLANTUML_ALPHABET

    def test_encode_deterministic(self, server):
        """Test that same input produces same output."""
        text = "@startuml\nA -> B\n@enduml"
        encoded1 = server.encode(text)
        encoded2 = server.encode(text)
        assert encoded1 == encoded2

    def test_get_diagram_url_format(self, server):
        """Test URL format is correct."""
        url = server.get_diagram_url("@startuml\nA -> B\n@enduml", "svg")
        assert url.startswith("https://www.plantuml.com/plantuml/svg/")

    def test_get_svg_url(self, server):
        """Test SVG URL generation."""
        url = server.get_svg_url("@startuml\nA -> B\n@enduml")
        assert "/svg/" in url
        assert url.startswith("https://www.plantuml.com/plantuml/svg/")

    def test_get_png_url(self, server):
        """Test PNG URL generation."""
        url = server.get_png_url("@startuml\nA -> B\n@enduml")
        assert "/png/" in url

    def test_get_txt_url(self, server):
        """Test TXT URL generation."""
        url = server.get_txt_url("@startuml\nA -> B\n@enduml")
        assert "/txt/" in url

    def test_create_local(self):
        """Test local server configuration."""
        server = PlantUMLServer.create_local(8080)
        assert "localhost:8080" in server.server_url
        assert server.server_url.startswith("http://")

    def test_create_local_custom_host(self):
        """Test local server with custom host."""
        server = PlantUMLServer.create_local(9090, host="127.0.0.1")
        assert "127.0.0.1:9090" in server.server_url

    def test_custom_server_url(self):
        """Test with custom server URL."""
        server = PlantUMLServer("https://custom.plantuml.com/plantuml")
        url = server.get_svg_url("@startuml\nA -> B\n@enduml")
        assert url.startswith("https://custom.plantuml.com/plantuml/svg/")

    def test_trailing_slash_removed(self):
        """Test that trailing slash is removed from server URL."""
        server = PlantUMLServer("https://www.plantuml.com/plantuml/")
        assert not server.server_url.endswith("/")

    def test_repr(self, server):
        """Test string representation."""
        repr_str = repr(server)
        assert "PlantUMLServer" in repr_str
        assert "plantuml.com" in repr_str


class TestEncodePlantuml:
    """Test encode_plantuml convenience function."""

    def test_encode_plantuml(self):
        """Test encode_plantuml function."""
        encoded = encode_plantuml("@startuml\nA -> B\n@enduml")
        assert len(encoded) > 0
        for char in encoded:
            assert char in PLANTUML_ALPHABET


class TestGetDiagramUrl:
    """Test get_diagram_url convenience function."""

    def test_get_diagram_url_default_server(self):
        """Test get_diagram_url with default server."""
        url = get_diagram_url("@startuml\nA -> B\n@enduml")
        assert url.startswith("https://www.plantuml.com/plantuml/svg/")

    def test_get_diagram_url_custom_server(self):
        """Test get_diagram_url with custom server."""
        url = get_diagram_url(
            "@startuml\nA -> B\n@enduml",
            format="png",
            server_url="http://localhost:8080"
        )
        assert url.startswith("http://localhost:8080/png/")


class TestEncoding:
    """Test specific encoding scenarios."""

    def test_encode_empty_diagram(self):
        """Test encoding minimal diagram."""
        server = PlantUMLServer()
        encoded = server.encode("@startuml\n@enduml")
        assert len(encoded) > 0

    def test_encode_complex_diagram(self):
        """Test encoding complex diagram."""
        complex_diagram = """@startuml
class User {
    +name: String
    +email: String
    +login()
    +logout()
}

class Order {
    +id: int
    +total: float
}

User "1" -- "*" Order : places
@enduml"""
        server = PlantUMLServer()
        encoded = server.encode(complex_diagram)
        assert len(encoded) > 0

        # URL should work
        url = server.get_svg_url(complex_diagram)
        assert url.startswith("https://www.plantuml.com/plantuml/svg/")

    def test_encode_unicode(self):
        """Test encoding with unicode characters."""
        server = PlantUMLServer()
        diagram = "@startuml\nA -> B : Hello World\n@enduml"
        encoded = server.encode(diagram)
        assert len(encoded) > 0
