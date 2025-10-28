"""Tests for MCP configuration loading."""

import json
import os

from amplifier_module_tool_mcp.config import MCPConfig


def test_load_from_inline():
    """Test loading configuration from inline config."""
    inline_config = {
        "servers": {
            "test-server": {"command": "npx", "args": ["-y", "test-server"]},
        }
    }

    config = MCPConfig(inline_config)
    servers = config.load_servers()

    assert "test-server" in servers
    assert servers["test-server"]["command"] == "npx"


def test_load_from_project_config(temp_config_dir, sample_mcp_config, monkeypatch):
    """Test loading configuration from project .amplifier/mcp.json."""
    # Change to temp directory
    monkeypatch.chdir(temp_config_dir.parent)

    # Write config file
    config_file = temp_config_dir / "mcp.json"
    with open(config_file, "w") as f:
        json.dump(sample_mcp_config, f)

    config = MCPConfig()
    servers = config.load_servers()

    assert "test-server" in servers
    assert servers["test-server"]["command"] == "npx"


def test_load_from_env(tmp_path, sample_mcp_config, monkeypatch):
    """Test loading configuration from environment variable."""
    # Create config file
    config_file = tmp_path / "mcp.json"
    with open(config_file, "w") as f:
        json.dump(sample_mcp_config, f)

    # Set environment variable
    monkeypatch.setenv("AMPLIFIER_MCP_CONFIG", str(config_file))

    config = MCPConfig()
    servers = config.load_servers()

    assert "test-server" in servers


def test_config_priority(temp_config_dir, monkeypatch):
    """Test that inline config overrides project config."""
    # Change to temp directory
    monkeypatch.chdir(temp_config_dir.parent)

    # Create project config
    project_config = {
        "mcpServers": {
            "test-server": {"command": "project-command", "args": []},
        }
    }
    with open(temp_config_dir / "mcp.json", "w") as f:
        json.dump(project_config, f)

    # Inline config (higher priority)
    inline_config = {
        "servers": {
            "test-server": {"command": "inline-command", "args": []},
        }
    }

    config = MCPConfig(inline_config)
    servers = config.load_servers()

    # Inline should override project
    assert servers["test-server"]["command"] == "inline-command"


def test_env_var_substitution():
    """Test environment variable substitution."""
    # Set environment variable
    os.environ["TEST_VAR"] = "test-value"

    # Test ${VAR} syntax
    result = MCPConfig.substitute_env_vars("Value is ${TEST_VAR}")
    assert result == "Value is test-value"

    # Test ${VAR:-default} syntax with existing var
    result = MCPConfig.substitute_env_vars("Value is ${TEST_VAR:-default}")
    assert result == "Value is test-value"

    # Test ${VAR:-default} syntax with missing var
    result = MCPConfig.substitute_env_vars("Value is ${MISSING_VAR:-default}")
    assert result == "Value is default"

    # Clean up
    del os.environ["TEST_VAR"]


def test_empty_config(monkeypatch, tmp_path):
    """Test handling of no configuration."""
    # Change to temp directory to avoid loading project config
    monkeypatch.chdir(tmp_path)

    # Clear environment variable if set
    monkeypatch.delenv("AMPLIFIER_MCP_CONFIG", raising=False)

    config = MCPConfig()
    servers = config.load_servers()

    # Should return dict (may be empty or may have user-level config)
    # The important thing is it doesn't crash with no config
    assert isinstance(servers, dict)
