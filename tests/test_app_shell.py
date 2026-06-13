from pathlib import Path


def test_authenticated_shell_has_responsive_navigation():
    content = Path("templates/layouts/app.html").read_text()

    assert 'name="viewport"' in content
    assert 'x-data="eloraShell"' in content
    assert "lg:grid-cols" in content
    assert 'id="main-content"' in content
