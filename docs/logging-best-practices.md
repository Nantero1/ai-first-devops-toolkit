# Logging Best Practices Guide

## Overview

This guide addresses logging improvements for LLM CI Runner based on **PEP 282** (Logging Module), **Python Logging Best Practices**, and our **Python Style Guide**.

---

# Rich Syntax Highlighting Issues in Azure DevOps: Causes and Solutions

## Root Cause Analysis

The issue with Rich Syntax highlighting not working in Azure DevOps, despite colors being displayed correctly, stems from several specific environmental and technical factors:

### **Primary Issue: TTY Detection**
Rich's Syntax highlighting specifically depends on **terminal detection** mechanisms that differ from basic color support. Azure DevOps pipelines run in a **non-TTY environment**, which means:

- `sys.stdout.isatty()` returns `False`
- Rich's console detection fails to identify the environment as terminal-capable
- **Pygments** (the underlying syntax highlighting library) defaults to plain text output

### **Secondary Issues**

1. **Environment Variables**: Azure DevOps may not set the necessary environment variables that Rich uses for feature detection
2. **Pygments Configuration**: The syntax highlighter requires specific formatter configurations for non-TTY environments
3. **ANSI Support**: While Azure DevOps supports ANSI escape codes for colors, syntax highlighting uses more complex sequences

## **The Solution: Multiple Approaches**

### **1. Use TTY_COMPATIBLE Environment Variable (Recommended)**

Rich 14.0+ introduced the `TTY_COMPATIBLE` environment variable specifically for CI/CD environments like Azure DevOps:

```yaml
# In your Azure DevOps pipeline
env:
  TTY_COMPATIBLE: '1'
  FORCE_COLOR: '1'
  TERM: 'xterm-256color'
  PYTHONIOENCODING: 'utf-8'
  PYTHONUNBUFFERED: '1'
```

### **2. Force Terminal Mode in Python Code**

```python
import os
from rich.console import Console
from rich.syntax import Syntax

# Configure environment for Azure DevOps
os.environ['TTY_COMPATIBLE'] = '1'
os.environ['FORCE_COLOR'] = '1'

# Create console with forced terminal support
console = Console(
    force_terminal=True,          # Override TTY detection
    color_system="256",          # Use 256-color system
    width=120,                   # Set explicit width
    legacy_windows=False,        # Modern terminal support
    no_color=False               # Explicitly enable colors
)

# Use ANSI-compatible themes
code = "def hello(): print('Hello, World!')"
syntax = Syntax(
    code, 
    "python", 
    theme="ansi_dark",           # Use ANSI theme for better compatibility
    line_numbers=True,
    background_color="default"
)

console.print(syntax)
```

### **3. Alternative Theme Selection**

For Azure DevOps environments, use these themes for better compatibility:
- `"ansi_dark"` (recommended)
- `"ansi_light"` (alternative)
- `"default"` (fallback)

Avoid complex themes like `"monokai"` or `"github-dark"` which may not render properly in CI environments.

## **Technical Explanation**

### **Why Colors Work But Syntax Highlighting Doesn't**

1. **Different Detection Mechanisms**: Basic Rich colors use simpler ANSI escape sequences that work in more environments
2. **Pygments Dependency**: Syntax highlighting specifically requires Pygments to generate complex color sequences
3. **Terminal Capability Checking**: Syntax highlighting performs more stringent terminal capability checks

### **How the Fix Works**

1. **TTY_COMPATIBLE=1**: Tells Rich to output ANSI sequences even in non-TTY environments
2. **force_terminal=True**: Bypasses Rich's internal terminal detection
3. **ANSI Themes**: Use themes that generate standard ANSI color codes rather than complex sequences

## **Implementation Steps**

### **Step 1: Update Your Pipeline**
Add the environment variables to your `azure-pipelines.yml` or GitHub Actions workflow:

```yaml
env:
  TTY_COMPATIBLE: '1'
  FORCE_COLOR: '1'
  TERM: 'xterm-256color'
```

### **Step 2: Modify Your Python Code**
Update your Rich console initialization:

```python
# Before (not working in Azure DevOps)
console = Console()
syntax = Syntax(code, "python")

# After (working in Azure DevOps)
console = Console(force_terminal=True, color_system="256")
syntax = Syntax(code, "python", theme="ansi_dark")
```

### **Step 3: Verify Dependencies**
Ensure you have the required packages:

```bash
pip install rich>=14.0.0 pygments
```

## **Diagnostic Tools**

- Use a diagnostic script to test your environment and Rich configuration.
- Example: `python scripts/debug-syntax-highlighting.py`

## **Key Takeaways**

1. **This is a known issue** with Rich in CI/CD environments, not a bug in your code
2. **The solution requires both environment variables and code changes** for reliable results
3. **Rich 14.0+ provides better CI/CD support** with the `TTY_COMPATIBLE` variable
4. **Use ANSI-compatible themes** for best results in Azure DevOps environments

---

## Logging Level Guidelines (PEP 282 Compliant)

| Level        | When to Use                                         | Examples                                                         |
| ------------ | --------------------------------------------------- | ---------------------------------------------------------------- |
| **DEBUG**    | Detailed diagnostic info for developers             | `LOGGER.debug("🔐 Attempting Azure SDK with schema enforcement")` |
| **INFO**     | Important business events users should know         | `LOGGER.info("🚀 Starting LLM execution")`                        |
| **WARNING**  | Something unexpected that doesn't prevent operation | `LOGGER.warning("⚠️ Azure SDK failed: {e}")`                      |
| **ERROR**    | A serious problem that prevented operation          | `LOGGER.error("❌ LLM Runner error: {e}")`                        |
| **CRITICAL** | System cannot continue operation                    | `LOGGER.critical("❌ Fatal system error")`                        |

## Improved Logging Patterns

### 1. **Business Event Logging (INFO Level)**
Use INFO for events that matter to end users:

```python
# ✅ CORRECT: User-facing business events (log once only)
LOGGER.info("🚀 Starting LLM execution")
LOGGER.info("📝 Writing output") 
LOGGER.info("🔐 Setting up LLM service")
```

### 2. **Diagnostic Logging (DEBUG Level)**
Use DEBUG for technical details developers need:

```python
# ✅ CORRECT: Technical diagnostic information
LOGGER.debug("🔐 Attempting Semantic Kernel with schema enforcement")
LOGGER.debug("✅ Semantic Kernel execution successful")
LOGGER.debug(f"📋 Schema loaded - model: {type(schema_model)}")
LOGGER.debug("🔄 Falling back to OpenAI SDK")  # Note: 🔄 not ⚠️ for DEBUG
```

### 3. **Context-Dependent Error Handling**

```python
# ✅ CORRECT: Context determines severity
def _process_structured_response(response: str, schema_model: type | None):
    if schema_model:
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # ERROR: Schema enforcement failed - broken promise to user
            LOGGER.error(f"❌ Schema enforcement failed: LLM returned non-JSON: {e}")
            LOGGER.error(f"   Expected: Valid JSON matching schema")
            LOGGER.info("🔄 Falling back to text output (schema enforcement disabled)")
    else:
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # DEBUG: Expected fallback behavior - no promise broken
            LOGGER.debug(f"📄 Response is not JSON, using text mode: {e}")
```

### 4. **Preserve User-Facing Rich Output**

```python
# ✅ CORRECT: Keep Rich console output separate from logging
def _process_text_response(response: str) -> dict[str, Any]:
    LOGGER.info("✅ LLM task completed with text output")
    CONSOLE.print("\n[bold green]🤖 LLM Response (Text)[/bold green]")
    CONSOLE.print(Panel(response, title="📝 Text Output", style="green"))
    return {"output": response.strip(), "type": "text"}
```

### 5. **Error Handling with Proper Exception Chaining**

```python
try:
    result = external_service.process(data)
    LOGGER.debug("Data processed successfully", extra={"data_size": len(data)})
    return result
except ValidationError as e:
    LOGGER.error("Validation failed", extra={"error": str(e), "data": data})
    raise LLMExecutionError(f"Invalid data format: {e}") from e
except ExternalServiceError as e:
    LOGGER.error("External service failed", extra={"service": "processor", "error": str(e)})
    raise LLMExecutionError("Service temporarily unavailable. Please try again.") from e
```

### 6. **Structured Logging with Context**

```python
from llm_ci_runner.logging_config import get_structured_logger_extras

LOGGER.info(
    "Processing template file", 
    extra=get_structured_logger_extras(
        file_path=str(template_file),
        variables_count=len(template_vars),
        template_type="handlebars"
    )
)

LOGGER.error(
    "Schema validation failed",
    extra=get_structured_logger_extras(
        schema_file=str(schema_file),
        error_type=type(e).__name__,
        field_count=len(schema_dict) if schema_dict else 0
    )
)
```

## Module-Specific Improvements

### core.py ✅ Fixed
- **Keep**: Business events at INFO level (`"🚀 Starting LLM execution"`)
- **Fixed**: Moved operational details to DEBUG level
- **Fixed**: User interruption now uses WARNING level

### llm_execution.py ✅ Fixed
- **Fixed**: Execution attempts and successes moved to DEBUG
- **Keep**: Final completion messages at INFO for user feedback
- **Fixed**: Fallback logic uses DEBUG, only real errors use WARNING

### templates.py (Already Good)
- **Good**: Template loading success uses INFO (user-visible)
- **Good**: Detailed parsing info uses DEBUG appropriately

### llm_service.py (Already Good)
- **Good**: Service setup messages at INFO level
- **Good**: Configuration details at DEBUG level

## Implementation Checklist

- [x] **Updated logging_config.py** with PEP guidelines and validation
- [x] **Added structured logging helper** `get_structured_logger_extras()`
- [x] **Fixed core.py logging levels** following PEP standards
- [x] **Fixed llm_execution.py logging levels** with proper DEBUG/INFO/WARNING usage
- [x] **Enhanced external library suppression** with additional common loggers
- [x] **Added validation** for invalid log levels
- [x] **Created comprehensive logging guide** (this document)
- [ ] **Update tests** to verify new logging behavior (if needed)

## Testing Logging Levels

```bash
# Test different logging levels to see the difference
uv run llm-ci-runner --log-level DEBUG --input-file test.json --output-file out.json
uv run llm-ci-runner --log-level INFO --input-file test.json --output-file out.json  
uv run llm-ci-runner --log-level WARNING --input-file test.json --output-file out.json
```

**Expected Output Differences:**
- **DEBUG**: Shows all technical details, execution attempts, parsing info
- **INFO**: Shows only business events (setup, execution start, completion)
- **WARNING**: Shows only warnings, errors, and final results

## Performance Considerations

1. **Avoid expensive operations in log messages:**
```python
# ❌ WRONG: Expensive operation always executed
LOGGER.debug(f"Processing data: {expensive_operation()}")

# ✅ CORRECT: Only execute if DEBUG logging enabled
if LOGGER.isEnabledFor(logging.DEBUG):
    LOGGER.debug(f"Processing data: {expensive_operation()}")
```

2. **Use lazy formatting:**
```python
# ✅ CORRECT: Let logging handle string formatting
LOGGER.debug("Processing %d items with %s", len(items), processor_name)
```

## CI/CD Environment Configuration (Rich Syntax Highlighting)

### Rich Console in Azure DevOps and CI/CD

**Problem**: Syntax highlighting and Rich formatting may not work in Azure DevOps environments due to terminal detection issues.

**Root Cause**: 
- Azure DevOps pipelines run in non-interactive environments
- `TERM` environment variable is often not set or set to `dumb`
- `sys.stdout.isatty()` returns `False`
- Rich defaults to `color_system=None` (no colors) in non-terminal environments
- Syntax highlighting and panels are disabled unless overridden

**Solutions**:

#### 1. Environment Variables (Recommended)

Add these environment variables to your Azure DevOps or CI/CD pipeline:

```yaml
env:
  TTY_COMPATIBLE: '1'
  FORCE_COLOR: '1'
  TERM: 'xterm-256color'
  PYTHONIOENCODING: 'utf-8'
  PYTHONUNBUFFERED: '1'
```

#### 2. Force Terminal Mode in Python Code

```python
import os
from rich.console import Console
from rich.syntax import Syntax

os.environ['TTY_COMPATIBLE'] = '1'
os.environ['FORCE_COLOR'] = '1'

console = Console(force_terminal=True, color_system="256", width=120)
syntax = Syntax(code, "python", theme="ansi_dark")
console.print(syntax)
```

#### 3. Theme Selection

Use `"ansi_dark"`, `"ansi_light"`, or `"default"` for best compatibility in CI/CD environments.

#### 4. Dependency Check

Ensure you have the required packages:

```bash
pip install rich>=14.0.0 pygments
```

#### 5. Diagnostic Script

Use `python scripts/debug-syntax-highlighting.py` to verify your environment and configuration.

### Verification

To verify Rich console is working in CI/CD:

```bash
echo "FORCE_COLOR: $FORCE_COLOR"
echo "TTY_COMPATIBLE: $TTY_COMPATIBLE"
echo "TERM: $TERM"
```

Test Rich output:

```python
from rich.console import Console
from rich.syntax import Syntax
c = Console(force_terminal=True, color_system="256")
c.print(Syntax('{"test": "value"}', 'json', theme="ansi_dark"))
```
```

### Troubleshooting

**No Colors or Syntax Highlighting in CI/CD**:
- Ensure `FORCE_COLOR=1` and `TTY_COMPATIBLE=1` are set
- Set `TERM=xterm-256color`
- Use `force_terminal=True` in your Console
- Use `ansi_dark` or `ansi_light` theme for Syntax
- Check that Rich version is >= 14.0.0 and Pygments is installed

**Colors work but syntax highlighting doesn't**:
- This is usually a TTY detection issue; set `TTY_COMPATIBLE=1` and use `force_terminal=True`
- Use ANSI-compatible themes

**Diagnostic script fails**:
- Check environment variables and dependencies
- Try running locally with the same settings as your CI/CD environment

---

This comprehensive guide shows how to implement robust logging and beautiful Rich output in both local and CI/CD environments, with special attention to Azure DevOps and other non-TTY pipelines. Always use `FORCE_COLOR=1` and `TTY_COMPATIBLE=1` for best results with Rich syntax highlighting in CI/CD. 