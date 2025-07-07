#!/usr/bin/env python3
"""
🚨 DEPRECATED: Use acceptance tests instead

This file has been replaced with comprehensive acceptance testing.

## Testing Options

### 🚀 Fast Smoke Testing (Less LLM Calls)
```bash
uv run pytest acceptance/ --smoke-test
```
- ✅ Auto-discovers all examples
- ✅ Tests execution reliability
- ✅ Validates schema compliance
- ✅ Fast feedback loop
- ⚠️  Uses real Azure OpenAI API calls

### 🎯 Comprehensive Quality Testing (More LLM Calls)
```bash
uv run pytest acceptance/
```
- ✅ Everything from smoke testing
- ✅ LLM-as-judge quality assessment
- ✅ Rich formatted output
- ✅ Custom scenario testing
- ⚠️  Uses real Azure OpenAI API calls

## Migration Notes

- All auto-discovery logic moved to `acceptance/conftest.py`
- All test functionality preserved and enhanced
- Better Rich formatting and detailed output
- Proper separation of smoke vs quality testing
- Follows tests-guide.mdc best practices

## Examples Structure (Convention-Based)

The tests auto-discover examples following this pattern:
```
examples/
├── 01-basic/
│   ├── sentiment-analysis/
│   │   ├── input.json     # Required
│   │   └── schema.json    # Optional
│   └── simple-chat/
│       └── input.json     # Required only
├── 02-devops/
│   ├── code-review/
│   │   ├── input.json
│   │   └── schema.json
│   └── ...
└── ...
```

Add new examples following this convention for automatic test coverage.
"""

import pytest


def test_deprecated_examples():
    """This test always skips with migration guidance."""
    pytest.skip(
        "⚠️  DEPRECATED: Use acceptance tests instead\n\n"
        "Fast smoke testing:        uv run pytest acceptance/ --smoke-test\n"
        "Comprehensive testing:     uv run pytest acceptance/\n\n"
        "See docstring above for complete migration guide."
    )


if __name__ == "__main__":
    print(__doc__)
    pytest.main([__file__, "-v"])
