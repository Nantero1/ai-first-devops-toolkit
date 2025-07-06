#!/usr/bin/env python3
"""
Test Runner - Simple validation script for llm_runner.py

This script validates that all dependencies are installed correctly and
the basic functionality works as expected.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_uv_installation():
    """Test that UV is installed and working."""
    print("🔍 Testing UV installation...")

    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✅ UV installed: {version}")
            return True
        else:
            print("  ❌ UV not found or not working")
            print("  💡 Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False

    except subprocess.TimeoutExpired:
        print("  ❌ UV command timed out")
        return False
    except Exception as e:
        print(f"  ❌ UV test error: {e}")
        print("  💡 Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False


def test_imports():
    """Test that all required imports work correctly."""
    print("🔍 Testing imports...")

    try:
        # Test Rich imports
        from rich.console import Console
        from rich.logging import RichHandler

        print("  ✅ Rich imports successful")

        # Test Semantic Kernel imports
        from semantic_kernel import Kernel
        from semantic_kernel.contents import ChatHistory, ChatMessageContent
        from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
            AzureChatCompletion,
        )

        print("  ✅ Semantic Kernel imports successful")

        # Test Azure imports
        from azure.identity.aio import DefaultAzureCredential
        from azure.core.exceptions import ClientAuthenticationError

        print("  ✅ Azure Identity imports successful")

        return True

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        print("  💡 Run: uv sync")
        return False


def test_script_help():
    """Test that the script shows help correctly."""
    print("\n🔍 Testing script help...")

    try:
        result = subprocess.run(
            ["uv", "run", "llm_runner.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and "LLM Runner" in result.stdout:
            print("  ✅ Script help works correctly")
            return True
        else:
            print(f"  ❌ Script help failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("  ❌ Script help timed out")
        return False
    except Exception as e:
        print(f"  ❌ Script help error: {e}")
        return False


def test_input_validation():
    """Test input validation with invalid files."""
    print("\n🔍 Testing input validation...")

    try:
        # Test with non-existent file
        result = subprocess.run(
            [
                "uv",
                "run",
                "llm_runner.py",
                "--input-file",
                "nonexistent.json",
                "--output-file",
                "test-output.json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0 and "not found" in result.stderr:
            print("  ✅ Non-existent file validation works")
        else:
            print("  ⚠️  Non-existent file validation unexpected behavior")

        # Test with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            invalid_json_file = f.name

        result = subprocess.run(
            [
                "uv",
                "run",
                "llm_runner.py",
                "--input-file",
                invalid_json_file,
                "--output-file",
                "test-output.json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0 and "JSON" in result.stderr:
            print("  ✅ Invalid JSON validation works")
        else:
            print("  ⚠️  Invalid JSON validation unexpected behavior")

        # Cleanup
        Path(invalid_json_file).unlink(missing_ok=True)

        return True

    except Exception as e:
        print(f"  ❌ Input validation test error: {e}")
        return False


def test_environment_check():
    """Test environment variable checking."""
    print("\n🔍 Testing environment variables...")

    import os

    required_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_MODEL"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"  ⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("  💡 Set these variables to test full functionality:")
        for var in missing_vars:
            print(f"     export {var}='your-value'")
        return False
    else:
        print("  ✅ All required environment variables are set")
        return True


def test_example_files():
    """Test that example files are valid JSON."""
    print("\n🔍 Testing example files...")

    example_files = [
        "examples/simple-example.json",
        "examples/pr-review-example.json",
        "examples/minimal-example.json",
    ]

    all_valid = True

    for file_path in example_files:
        try:
            if Path(file_path).exists():
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Validate required structure
                if "messages" in data and isinstance(data["messages"], list):
                    print(f"  ✅ {file_path} is valid")
                else:
                    print(f"  ❌ {file_path} missing required 'messages' field")
                    all_valid = False
            else:
                print(f"  ⚠️  {file_path} not found")
                all_valid = False

        except json.JSONDecodeError as e:
            print(f"  ❌ {file_path} has invalid JSON: {e}")
            all_valid = False
        except Exception as e:
            print(f"  ❌ {file_path} error: {e}")
            all_valid = False

    return all_valid


def main():
    """Run all tests."""
    print("🧪 LLM Runner Test Suite")
    print("=" * 40)

    tests = [
        ("UV Installation", test_uv_installation),
        ("Import Dependencies", test_imports),
        ("Script Help", test_script_help),
        ("Input Validation", test_input_validation),
        ("Environment Variables", test_environment_check),
        ("Example Files", test_example_files),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  💥 {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results:")

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1

    print(f"\nPassed: {passed}/{len(results)} tests")

    if passed == len(results):
        print("\n🎉 All tests passed! LLM Runner is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
