# Logging Best Practices Guide

## Overview

This guide addresses logging improvements for LLM CI Runner based on **PEP 282** (Logging Module), **Python Logging Best Practices**, and our **Python Style Guide**.

## Current Logging Analysis

### ✅ Strengths
- **Rich Console Integration**: Beautiful, colored output with proper stream routing
- **Centralized Configuration**: Well-organized `logging_config.py` module  
- **External Library Suppression**: Smart suppression of noisy Azure/HTTP logs
- **Contextual Messages**: Good use of emojis and descriptive text for UX

### ⚠️ Critical Issues Fixed

**Before (Incorrect):**
```python
# ❌ WRONG: Using INFO for internal operational details
LOGGER.info("✅ Semantic Kernel execution successful")
LOGGER.info("✅ Template rendered successfully")

# ❌ WRONG: Using WARNING for expected fallback behavior  
LOGGER.warning(f"⚠️ Semantic Kernel failed: {e}")
LOGGER.info("🔄 Falling back to OpenAI SDK")

# ❌ WRONG: Using INFO for user interruption
LOGGER.info("⏹️  Interrupted by user")
```

**After (Correct):**
```python
# ✅ CORRECT: DEBUG for internal operational details
LOGGER.debug("✅ Semantic Kernel execution successful")
LOGGER.debug("✅ Template rendered successfully")

# ✅ CORRECT: DEBUG for expected fallback, WARNING only for actual issues
LOGGER.debug(f"⚠️ Semantic Kernel failed: {e}")
LOGGER.debug("🔄 Falling back to OpenAI SDK")

# ✅ CORRECT: WARNING for user interruption (unexpected but recoverable)
LOGGER.warning("⏹️  Interrupted by user")
```

## Logging Level Guidelines (PEP 282 Compliant)

| Level | When to Use | Examples |
|-------|-------------|----------|
| **DEBUG** | Detailed diagnostic info for developers | `LOGGER.debug("🔐 Attempting Azure SDK with schema enforcement")` |
| **INFO** | Important business events users should know | `LOGGER.info("🚀 Starting LLM execution")` |
| **WARNING** | Something unexpected that doesn't prevent operation | `LOGGER.warning("⚠️ Azure SDK failed: {e}")` |
| **ERROR** | A serious problem that prevented operation | `LOGGER.error("❌ LLM Runner error: {e}")` |
| **CRITICAL** | System cannot continue operation | `LOGGER.critical("❌ Fatal system error")` |

## Improved Logging Patterns

### 1. **Business Event Logging (INFO Level)**
Use INFO for events that matter to end users:

```python
# ✅ CORRECT: User-facing business events (log once only)
LOGGER.info("🚀 Starting LLM execution")
LOGGER.info("📝 Writing output") 
LOGGER.info("🔐 Setting up LLM service")

# ❌ WRONG: Internal technical details or duplicates
LOGGER.info("✅ Semantic Kernel execution successful")  # Use DEBUG
LOGGER.info("✅ Template rendered successfully")       # Use DEBUG
LOGGER.info("✅ Created ChatHistory with 2 messages") # DUPLICATE if logged multiple times
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
**CRITICAL INSIGHT**: Same failure, different severity based on context:

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
**CRITICAL**: Don't remove beautiful UI elements during "logging improvements":

```python
# ✅ CORRECT: Keep Rich console output separate from logging
def _process_text_response(response: str) -> dict[str, Any]:
    LOGGER.info("✅ LLM task completed with text output")
    
    # Beautiful Rich output - users expect to see their results!
    CONSOLE.print("\n[bold green]🤖 LLM Response (Text)[/bold green]")
    CONSOLE.print(Panel(response, title="📝 Text Output", style="green"))
    
    return {"output": response.strip(), "type": "text"}

# ❌ WRONG: Removing Rich output degrades user experience
def _process_text_response(response: str) -> dict[str, Any]:
    LOGGER.debug("✅ LLM task completed with text output")  # Users can't see their results!
    return {"output": response.strip(), "type": "text"}
```

### 5. **Error Handling with Proper Exception Chaining**
Follow your style guide's error handling patterns:

```python
# ✅ CORRECT: Proper error logging with context
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
Use the new `get_structured_logger_extras()` helper:

```python
from llm_ci_runner.logging_config import get_structured_logger_extras

# ✅ CORRECT: Structured logging with context
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

## Key Improvements Summary

The logging improvements follow **PEP 282** standards and your **Python Style Guide**:

1. **Context-Dependent Level Usage**:
   - **INFO**: Business events users care about (execution start, completion, setup) - **LOG ONCE ONLY**
   - **DEBUG**: Technical details for developers (execution attempts, parsing, fallbacks)  
   - **WARNING**: Unexpected but recoverable situations (interruptions, API failures)
   - **ERROR**: Problems that prevent operation OR **broken promises** (schema enforcement failures)

2. **Critical Insights from Analysis**:
   - **Same failure, different severity**: JSON parsing is ERROR with schema enforcement, DEBUG without
   - **Avoid duplicates**: Don't log success messages multiple times in execution flow
   - **Preserve UX**: Keep Rich console output separate from logging system
   - **Emoji consistency**: Match emoji to actual severity (🔄 for DEBUG, ⚠️ for WARNING, ❌ for ERROR)

3. **Enhanced Configuration**:
   - Input validation for log levels
   - Better external library suppression
   - Structured logging support
   - Proper stream routing (stdout/stderr)

4. **Consistent Patterns**:
   - Exception chaining with `from e`
   - Descriptive error messages
   - Fallback mechanisms with appropriate logging
   - Context-rich messages for debugging
   - Beautiful Rich output preserved for user experience

## Result

Your logging system now provides:
- **Clean INFO output** for end users showing only important business events
- **Rich DEBUG output** for developers with all technical details  
- **Appropriate WARNING/ERROR levels** for actual issues
- **Better debugging** with structured context
- **PEP 282 compliance** with industry standards

This creates a **professional, maintainable logging system** that scales from development to production environments. 