import sys
import types
import importlib
from unittest.mock import MagicMock
import pytest

def test_beartype_called_on_import(monkeypatch):
    """
    Test that reloading the agent package triggers a call to beartype_this_package.
    This ensures that the package-level initialization code in agent/__init__.py is executed upon reload.
    """
    if "beartype.claw" not in sys.modules:
        fake_claw = types.ModuleType("beartype.claw")
        fake_claw.beartype_this_package = MagicMock(name="beartype_this_package")
        monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    else:
        sys.modules["beartype.claw"].beartype_this_package = MagicMock(name="beartype_this_package")
    
    # Import the agent package. Its __init__.py calls beartype_this_package on import.
    import agent
    
    # Reset the mock's call history so that the upcoming reload is the only call counted.
    sys.modules["beartype.claw"].beartype_this_package.reset_mock()
    
    # Reload the agent package to trigger execution of __init__.py again.
    importlib.reload(agent)
    
    # Verify that beartype_this_package was called exactly once during the reload.
    sys.modules["beartype.claw"].beartype_this_package.assert_called_once()
def test_beartype_called_on_initial_import(monkeypatch):
    """
    Test that on an initial import (after removing the package from sys.modules),
    the agent package's __init__.py calls beartype_this_package exactly once.
    This verifies that the package-level initialization code is correctly executed during a fresh import.
    """
    if "beartype.claw" not in sys.modules:
        fake_claw = types.ModuleType("beartype.claw")
        fake_claw.beartype_this_package = MagicMock(name="beartype_this_package")
        monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    else:
        sys.modules["beartype.claw"].beartype_this_package = MagicMock(name="beartype_this_package")
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    importlib.import_module("agent")
    
    sys.modules["beartype.claw"].beartype_this_package.assert_called_once()
def test_import_failure_if_beartype_not_callable(monkeypatch):
    """
    Test that importing the agent package fails if beartype_this_package is not callable.
    This ensures that the package initialization behaves as expected and raises a TypeError.
    """
    fake_claw = types.ModuleType("beartype.claw")
    fake_claw.beartype_this_package = 42  # Non-callable value
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    with pytest.raises(TypeError):
        importlib.import_module("agent")
def test_import_failure_if_beartype_raises_exception(monkeypatch):
    """
    Test that importing the agent package fails if beartype_this_package, though callable,
    raises an exception. This verifies that exceptions raised in the package initialization
    are correctly propagated.
    """
    fake_claw = types.ModuleType("beartype.claw")
    def fake_beartype():
        raise ValueError("Test exception")
    fake_claw.beartype_this_package = fake_beartype
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    with pytest.raises(ValueError, match="Test exception"):
        importlib.import_module("agent")
def test_multiple_reloads_calls_beartype(monkeypatch):
    """
    Test that multiple reloads of the agent package each trigger a call to beartype_this_package,
    so that the total call count equals the sum of one initial import plus one call per reload.
    """
    fake_claw = types.ModuleType("beartype.claw")
    fake_claw.beartype_this_package = MagicMock(name="beartype_this_package")
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    import agent
    
    importlib.reload(agent)
    importlib.reload(agent)
    
    assert sys.modules["beartype.claw"].beartype_this_package.call_count == 3
def test_import_failure_if_beartype_missing(monkeypatch):
    """
    Test that importing the agent package fails if the beartype.claw module does not
    define beartype_this_package. This verifies that the missing required attribute
    causes an ImportError during package initialization.
    """
    fake_claw = types.ModuleType("beartype.claw")
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    with pytest.raises(ImportError) as exc_info:
        importlib.import_module("agent")
    
    assert "beartype_this_package" in str(exc_info.value)
def test_no_extra_call_on_standard_import(monkeypatch):
    """
    Test that multiple standard imports of the agent package do not trigger additional calls
    to beartype_this_package. This verifies that after the initial import, re-importing the
    module without a reload does not re-run the initialization logic.
    """
    fake_claw = types.ModuleType("beartype.claw")
    fake_claw.beartype_this_package = MagicMock(name="beartype_this_package")
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    importlib.import_module("agent")
    initial_count = fake_claw.beartype_this_package.call_count
    
    importlib.import_module("agent")
    assert fake_claw.beartype_this_package.call_count == initial_count
def test_import_failure_when_beartype_claw_missing(monkeypatch):
    """
    Test that importing the agent package fails with ModuleNotFoundError 
    if the beartype.claw module is completely missing. Since the import in the 
    agent package is "from beartype.claw import beartype_this_package", Python
    will report that 'beartype' is missing.
    """
    monkeypatch.delitem(sys.modules, "beartype.claw", raising=False)
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    with pytest.raises(ModuleNotFoundError, match="No module named 'beartype'"):
        importlib.import_module("agent")
def test_import_recovery_after_failed_import(monkeypatch):
    """
    Test that after a failed import of the agent package (due to beartype_this_package raising an exception),
    if the beartype.claw module is corrected, a subsequent import succeeds and calls beartype_this_package exactly once.
    """
    fake_claw_fail = types.ModuleType("beartype.claw")
    def failing_beartype():
        raise ValueError("Initial failure")
    fake_claw_fail.beartype_this_package = failing_beartype
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw_fail)
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    with pytest.raises(ValueError, match="Initial failure"):
        importlib.import_module("agent")
    
    valid_claw = types.ModuleType("beartype.claw")
    valid_claw.beartype_this_package = MagicMock(name="beartype_this_package")
    monkeypatch.setitem(sys.modules, "beartype.claw", valid_claw)
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    importlib.import_module("agent")
    
    valid_claw.beartype_this_package.assert_called_once()
def test_import_with_non_none_return(monkeypatch):
    """
    Test that importing the agent package succeeds when the beartype_this_package
    callable returns a non-None value. This verifies that the return value is ignored
    and does not affect the package initialization.
    """
    if "beartype.claw" not in sys.modules:
        fake_claw = types.ModuleType("beartype.claw")
        monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    else:
        fake_claw = sys.modules["beartype.claw"]
    
    mock_beartype = MagicMock(name="beartype_this_package", return_value=100)
    fake_claw.beartype_this_package = mock_beartype
    
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    importlib.import_module("agent")
    
    mock_beartype.assert_called_once()
def test_agent_exports_beartype_this_package(monkeypatch):
    """
    Test that after importing the agent package, the agent module exports the
    'beartype_this_package' attribute exactly as imported from the beartype.claw module.
    This ensures that the package initialization does not remove or alter the imported attribute.
    """
    # Create a fake beartype.claw module and set its beartype_this_package to a MagicMock.
    fake_claw = types.ModuleType("beartype.claw")
    fake_func = MagicMock(name="beartype_this_package", return_value=None)
    fake_claw.beartype_this_package = fake_func
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    # Remove the agent module from sys.modules to force a fresh import.
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    # Import the agent package. Its __init__.py calls beartype_this_package during import.
    import agent
    
    # Verify that the agent module has the attribute 'beartype_this_package'
    assert hasattr(agent, "beartype_this_package"), "agent should export beartype_this_package"
    
    # Verify that the exported attribute is the same as the one from beartype.claw
    assert agent.beartype_this_package is fake_func, (
        "The beartype_this_package attribute in agent should be the imported function from beartype.claw"
    )
    
    # Also ensure that the function was called once during the import as expected.
    fake_func.assert_called_once()
def test_reload_with_updated_beartype(monkeypatch):
    """
    Test that after initially importing the agent package with a given
    beartype_this_package callable, updating the beartype.claw module with
    a new callable and reloading the agent package causes the new callable
    to be used and called, without re-calling the original callable.
    """
    # Create an initial fake beartype.claw module with an initial MagicMock.
    initial_claw = types.ModuleType("beartype.claw")
    initial_func = MagicMock(name="initial_beartype_this_package")
    initial_claw.beartype_this_package = initial_func
    monkeypatch.setitem(sys.modules, "beartype.claw", initial_claw)
    
    # Ensure the agent package is not cached.
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    # Import the agent package. This should call the initial callable.
    import agent
    initial_func.assert_called_once()
    
    # Create a new fake beartype.claw module with a new callable.
    new_claw = types.ModuleType("beartype.claw")
    new_func = MagicMock(name="new_beartype_this_package")
    new_claw.beartype_this_package = new_func
    # Replace the old beartype.claw in sys.modules with the new one.
    monkeypatch.setitem(sys.modules, "beartype.claw", new_claw)
    
    # Reload the agent package to pick up the new callable.
    importlib.reload(agent)
    
    # Verify that the initial callable was not called again.
    initial_func.assert_called_once()
    # And the new callable was called once during the reload.
    new_func.assert_called_once()
    # Also verify that the agent package now exports the new callable.
    assert agent.beartype_this_package is new_func, (
        "agent should export the updated beartype_this_package callable after reload"
    )
def test_side_effect_callable(monkeypatch):
    """
    Test that if the beartype_this_package callable has a side effect that sets an attribute
    on the agent module, the side effect is correctly observed after importing the agent package.
    """
    # Ensure the agent module is not cached
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    # Create a fake beartype.claw module with a side-effect function.
    fake_claw = types.ModuleType("beartype.claw")
    
    def side_effect():
        # Access the agent module from sys.modules and add a side-effect attribute.
        agent_module = sys.modules["agent"]
        setattr(agent_module, "side_effect_attr", True)
    fake_claw.beartype_this_package = side_effect
    
    # Insert the fake beartype.claw into sys.modules.
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    # Import the agent package; this will execute __init__.py which calls side_effect.
    import agent
    
    # Verify that the side effect occurred as expected.
    assert hasattr(agent, "side_effect_attr"), "agent module should have the side_effect_attr attribute"
    assert agent.side_effect_attr is True, "side_effect_attr should be True after import"
def test_reload_failure_when_beartype_claw_removed(monkeypatch):
    """
    Test that reloading the agent package after the beartype.claw module has been removed
    from sys.modules results in a ModuleNotFoundError.
    """
    # Set up a valid fake beartype.claw module.
    fake_claw = types.ModuleType("beartype.claw")
    fake_claw.beartype_this_package = MagicMock(name="beartype_this_package")
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    # Ensure the agent package is imported successfully.
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    import agent
    
    # Remove the beartype.claw module to simulate its absence at reload time.
    monkeypatch.delitem(sys.modules, "beartype.claw", raising=False)
    
    # On reload, the agent package will try to import from beartype.claw and
    # should raise a ModuleNotFoundError since it is missing.
    with pytest.raises(ModuleNotFoundError, match="No module named 'beartype'"):
        importlib.reload(agent)
def test_reload_recovers_missing_exported_attribute(monkeypatch):
    """
    Test that if the agent module's beartype_this_package attribute is deleted after import,
    reloading the agent module will restore it by re-importing the function from beartype.claw,
    and that the callable is invoked once during the reload.
    """
    # Create a fake beartype.claw module with a MagicMock as beartype_this_package.
    fake_claw = types.ModuleType("beartype.claw")
    fake_beartype = MagicMock(name="beartype_this_package")
    fake_claw.beartype_this_package = fake_beartype
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    # Remove the agent package from sys.modules to force a fresh import.
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    import agent  # Initial import; __init__.py will execute and import beartype_this_package.
    # Now simulate that the exported attribute is deleted.
    del agent.beartype_this_package
    # Reset the call count on fake_beartype so that only reload calls are counted.
    fake_beartype.reset_mock()
    # Reload the agent package, which should re-import beartype_this_package and call it.
    importlib.reload(agent)
    # Verify that agent now exports beartype_this_package restored from beartype.claw.
    assert hasattr(agent, "beartype_this_package"), "agent should have beartype_this_package after reload"
    assert agent.beartype_this_package is fake_beartype, (
        "agent.beartype_this_package should be restored to the callable from beartype.claw"
    )
    # Verify that the callable was called exactly once during the reload.
    fake_beartype.assert_called_once()
def test_agent_module_attributes(monkeypatch):
    """
    Test that the agent module's __name__ and __package__ attributes remain correct
    after the initial import and after reloading the module.
    This ensures that reloading agent doesn't alter its fundamental module identity.
    """
    # Create a fake beartype.claw module with a valid beartype_this_package callable.
    fake_claw = types.ModuleType("beartype.claw")
    fake_claw.beartype_this_package = MagicMock(name="beartype_this_package")
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    # Remove agent from sys.modules to force a fresh import.
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    # Import the agent package, which will call beartype_this_package.
    import agent
    # Verify the module identity attributes.
    assert agent.__name__ == "agent", "The module __name__ should be 'agent'"
    assert agent.__package__ == "agent", "The module __package__ should be 'agent'"
    
    # Reload the agent package and verify that the attributes remain the same.
    importlib.reload(agent)
    assert agent.__name__ == "agent", "After reload, the module __name__ should remain 'agent'"
    assert agent.__package__ == "agent", "After reload, the module __package__ should remain 'agent'"
def test_failed_import_not_cached(monkeypatch):
    """
    Test that if the agent package fails to import because beartype_this_package is non-callable,
    the agent module is not left cached in sys.modules.
    This ensures that a failed import does not pollute the module cache.
    """
    # Create a fake beartype.claw module with a non-callable beartype_this_package to trigger a TypeError.
    fake_claw = types.ModuleType("beartype.claw")
    fake_claw.beartype_this_package = 42  # Non-callable, should cause a TypeError on import.
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    # Ensure 'agent' is removed from sys.modules to force a full re-import.
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    with pytest.raises(TypeError):
        importlib.import_module("agent")
    # After the failed import, the 'agent' module should not be cached in sys.modules.
    assert "agent" not in sys.modules, (
        "agent module should not be cached in sys.modules after a failed import"
    )
def test_standard_import_does_not_override_modified_attribute(monkeypatch):
    """
    Test that if the agent package's exported beartype_this_package attribute is modified after the initial import,
    subsequent standard imports (without reload) do not override the modified attribute.
    This verifies that the module caching behavior prevents re-execution of the __init__.py code.
    """
    # Set up a fake beartype.claw module with a MagicMock.
    fake_claw = types.ModuleType("beartype.claw")
    original_func = MagicMock(name="beartype_this_package")
    fake_claw.beartype_this_package = original_func
    monkeypatch.setitem(sys.modules, "beartype.claw", fake_claw)
    
    # Remove agent from sys.modules to force a fresh import.
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    
    # Import the agent package; this will call original_func once.
    import agent
    original_func.assert_called_once()
    
    # Modify the exported attribute on the agent module.
    agent.beartype_this_package = "modified"
    
    # Re-import agent using a standard import; __init__.py should NOT re-run.
    reimported_agent = importlib.import_module("agent")
    
    # Verify that the modified attribute remains unchanged.
    assert reimported_agent.beartype_this_package == "modified", (
        "Standard import should not override a modified attribute in the cached module"
    )