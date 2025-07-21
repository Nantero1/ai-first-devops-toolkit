*This scratchpad file serves as a phase-specific task tracker and implementation planner. The Mode System on Line 1 is critical and must never be deleted. It defines two core modes: Implementation Type for new feature development and Bug Fix Type for issue resolution. Each mode requires specific documentation formats, confidence tracking, and completion criteria. Use "plan" trigger for planning phase (🎯) and "agent" trigger for execution phase (⚡) after reaching 95% confidence. Follow strict phase management with clear documentation transfer process.*

`MODE SYSTEM TYPES (DO NOT DELETE!):
1. Implementation Type (New Features):
   - Trigger: User requests new implementation
   - Format: MODE: Implementation, FOCUS: New functionality
   - Requirements: Detailed planning, architecture review, documentation
   - Process: Plan mode (🎯) → 95% confidence → Agent mode (⚡)

2. Bug Fix Type (Issue Resolution):
   - Trigger: User reports bug/issue
   - Format: MODE: Bug Fix, FOCUS: Issue resolution
   - Requirements: Problem diagnosis, root cause analysis, solution verification
   - Process: Plan mode (🎯) → Chain of thought analysis → Agent mode (⚡)

Cross-reference with .cursor/memories.md and .cursor/rules/lessons-learned.mdc for context and best practices.`

# Mode: PLAN 🎯

Current Task: Add timeout resilience to existing retry mechanism (2-minute default, integrated with retry module)
Understanding: The codebase already has comprehensive retry logic. Now we need to add timeout protection with close coupling to retry functionality, potentially integrating directly into retry.py module.

## Current State Analysis

**Existing Implementation (Completed):**
✅ Tenacity retry mechanism fully implemented in `llm_ci_runner/retry.py`
✅ 6 critical API points protected with retry decorators
✅ 245/245 tests passing, 90.15% coverage  
✅ Selective exception handling (retry transient, skip permanent errors)

**Gap Identified: Timeout Protection**
❌ No explicit timeout controls on API calls (2-minute default needed)
❌ Risk of indefinite hangs during network operations
❌ No integrated timeout + retry solution

## Architecture Decision: Integrated vs Separate

**Current Functions with Retry Decorators (HIGH PRIORITY):**
1. `setup_azure_service()` - @retry_network_operation ✅
2. `setup_openai_service()` - ❌ **Missing retry decorator**
3. `_execute_semantic_kernel_with_schema()` - @retry_network_operation ✅  
4. `_execute_sdk_with_schema()` - @retry_network_operation ✅

**Functions WITHOUT Retry Decorators (but need timeout):**
5. `_create_azure_client()` - ❌ No retry, needs both timeout + retry
6. `_create_openai_client()` - ❌ No retry, needs both timeout + retry

**Analysis**: Only 3/6 critical functions currently have retry protection!

**Architecture Evaluation: Integrated Approach**

**✅ PROS of Integrating into retry.py:**
- **Single Responsibility**: One module handles all resilience (retry + timeout)
- **Atomic Operations**: Timeout and retry are applied together, no separate decorators
- **Cleaner API**: One decorator per function instead of stacking decorators
- **Unified Configuration**: Timeout + retry settings in one place
- **Better Testing**: Test timeout + retry interaction as unit
- **DRY Principle**: No duplicate error handling logic

**❌ CONS of Separate Modules:**
- **Decorator Stacking**: `@timeout @retry` creates complex nested behavior
- **Split Responsibility**: Two modules for related functionality
- **Integration Complexity**: Ensuring timeout errors are properly retriable
- **Configuration Spread**: Timeout config separate from retry config

**DECISION: Integrate timeout functionality into retry.py module** ✅

## Refined Implementation Plan

### Phase 1: Enhanced Retry Module Design

**Update `llm_ci_runner/retry.py` with timeout integration:**

```python
# New timeout configuration constants
DEFAULT_LLM_API_TIMEOUT = 120      # 2 minutes for LLM API calls
DEFAULT_CLIENT_TIMEOUT = 30        # 30 seconds for client creation  
DEFAULT_SERVICE_TIMEOUT = 45       # 45 seconds for service setup
DEFAULT_AUTH_TIMEOUT = 15          # 15 seconds for authentication

# Enhanced retry decorators with integrated timeout
@retry_with_timeout_openai_api_call(timeout=DEFAULT_LLM_API_TIMEOUT)
@retry_with_timeout_azure_api_call(timeout=DEFAULT_LLM_API_TIMEOUT)  
@retry_with_timeout_network_operation(timeout=DEFAULT_LLM_API_TIMEOUT)
```

**New Combined Decorators:**
1. `retry_with_timeout_openai_api_call` - OpenAI API calls with timeout
2. `retry_with_timeout_azure_api_call` - Azure API calls with timeout
3. `retry_with_timeout_network_operation` - General network ops with timeout
4. `retry_with_timeout_client_creation` - Client creation with timeout
5. `retry_with_timeout_service_setup` - Service setup with timeout

### Phase 2: Unified Decorator Implementation

**Pattern: Timeout + Retry in Single Decorator**

```python
def create_retry_with_timeout_decorator(
    timeout_seconds: int,
    retry_condition_func: Callable,
    max_retries: int = DEFAULT_MAX_RETRIES,
    min_wait: int = DEFAULT_MIN_WAIT,
    max_wait: int = DEFAULT_MAX_WAIT,
):
    """Create unified retry + timeout decorator."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Apply timeout wrapper
            async def timeout_wrapper():
                return await asyncio.wait_for(
                    func(*args, **kwargs), 
                    timeout=timeout_seconds
                )
            
            # Apply retry to timeout wrapper
            retry_decorator = retry(
                retry=retry_if_exception(enhanced_retry_condition),
                stop=stop_after_attempt(max_retries),
                wait=wait_random_exponential(
                    multiplier=DEFAULT_EXPONENTIAL_MULTIPLIER,
                    min=min_wait,
                    max=max_wait,
                ),
                after=after_log(LOGGER, logging.WARNING),
                reraise=True,
            )
            
            return await retry_decorator(timeout_wrapper)()
        return wrapper
    return decorator

def enhanced_retry_condition(exception: BaseException) -> bool:
    """Enhanced retry condition including timeout errors."""
    # Add timeout errors as retriable
    if isinstance(exception, (asyncio.TimeoutError, TimeoutError)):
        return True
    
    # Existing retry logic
    return retry_condition_func(exception)
```

### Phase 3: High-Priority Function Updates

**1. LLM Execution Functions (Highest Priority - 120s timeout):**
```python
# In llm_execution.py - Update LLMExecutor methods
@retry_with_timeout_network_operation(timeout=120)  # 2 minutes
async def _execute_semantic_kernel_with_schema(self, chat_history: list):

@retry_with_timeout_network_operation(timeout=120)  # 2 minutes  
async def _execute_sdk_with_schema(self, client_type: str, chat_history: list):
```

**2. Client Creation Functions (High Priority - 30s timeout):**
```python
# In llm_execution.py - Update client creation
@retry_with_timeout_client_creation(timeout=30)
async def _create_azure_client() -> AsyncAzureOpenAI:

@retry_with_timeout_client_creation(timeout=30)
async def _create_openai_client() -> AsyncOpenAI:
```

**3. Service Setup Functions (High Priority - 45s timeout):**
```python
# In llm_service.py - Update service setup
@retry_with_timeout_service_setup(timeout=45)
async def setup_azure_service():

@retry_with_timeout_service_setup(timeout=45)  # Add missing retry
async def setup_openai_service():
```

### Phase 4: Environment Variable Configuration

**Add timeout configuration support:**
```python
# In retry.py - Environment variable support
DEFAULT_LLM_API_TIMEOUT = int(os.getenv("LLM_API_TIMEOUT", "120"))
DEFAULT_CLIENT_TIMEOUT = int(os.getenv("CLIENT_TIMEOUT", "30"))  
DEFAULT_SERVICE_TIMEOUT = int(os.getenv("SERVICE_SETUP_TIMEOUT", "45"))
DEFAULT_AUTH_TIMEOUT = int(os.getenv("AUTH_TIMEOUT", "15"))

# Validation with fallback
def get_timeout_from_env(env_var: str, default: int) -> int:
    """Get timeout from environment with validation and fallback."""
    try:
        value = os.getenv(env_var)
        if value is not None:
            parsed = int(value)
            if parsed > 0:
                return parsed
            else:
                LOGGER.warning(f"Invalid {env_var} value (must be positive): {parsed}, using default: {default}")
        return default
    except (ValueError, TypeError) as e:
        LOGGER.warning(f"Invalid {env_var} value: {value}, using default: {default}s - {e}")
        return default
```

### Phase 5: Enhanced Error Handling

**Timeout-specific error messages:**
```python
def create_timeout_aware_wrapper(func, timeout_seconds: int):
    """Create wrapper with timeout-specific error messages."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
        except asyncio.TimeoutError as e:
            operation_name = func.__name__.replace('_', ' ').title()
            raise TimeoutError(
                f"{operation_name} timed out after {timeout_seconds}s. "
                f"Consider increasing timeout via environment variables."
            ) from e
    return wrapper
```

## Implementation Priority (High Priority Functions)

**PHASE 1 - Critical LLM Operations (120s timeout):**
1. `_execute_semantic_kernel_with_schema()` - Core LLM inference
2. `_execute_sdk_with_schema()` - Fallback LLM inference

**PHASE 2 - Client/Service Setup (30-45s timeout):**  
3. `_create_azure_client()` - Azure client creation
4. `_create_openai_client()` - OpenAI client creation
5. `setup_azure_service()` - Azure service setup
6. `setup_openai_service()` - OpenAI service setup (add missing retry)

**PHASE 3 - Testing & Validation:**
7. Comprehensive timeout + retry interaction tests
8. Environment variable configuration tests
9. Error message validation tests

## Testing Strategy

**Enhanced Unit Tests (Building on 37 existing retry tests):**

```python
class TestTimeoutWithRetry:
    """Tests for integrated timeout + retry functionality."""
    
    @pytest.mark.asyncio
    async def test_timeout_then_retry_success(self):
        """Test timeout on first attempt, success on retry."""
        # given
        call_count = 0
        async def slow_then_fast_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(2)  # Will timeout with 1s limit
            return "success"
        
        decorated = retry_with_timeout_network_operation(timeout=1)(slow_then_fast_operation)
        
        # when
        result = await decorated()
        
        # then
        assert result == "success"
        assert call_count == 2  # First timeout, second success
    
    @pytest.mark.asyncio
    async def test_timeout_configuration_from_env(self):
        """Test timeout configuration from environment variables."""
        # given
        with patch.dict("os.environ", {"LLM_API_TIMEOUT": "5"}):
            # when
            timeout_value = get_timeout_from_env("LLM_API_TIMEOUT", 120)
            
            # then
            assert timeout_value == 5
```

## Risk Analysis

**Technical Risks:**

1. **Total Execution Time**: timeout × retry_attempts = potential 6-minute total
   - **Mitigation**: Conservative 2-minute default with 3 retries = reasonable 6-minute max
   
2. **Decorator Complexity**: Nested async decorators can be complex
   - **Mitigation**: Use established tenacity patterns, comprehensive testing

3. **Backward Compatibility**: Changes to existing retry decorators
   - **Mitigation**: Keep existing decorator names, just enhance functionality

**Implementation Risks:**

1. **Testing Complexity**: Timeout + retry testing requires careful timing
   - **Mitigation**: Use fast timeouts in tests, proper async mocking

2. **Error Message Clarity**: Users need clear timeout vs other error types
   - **Mitigation**: Specific timeout error messages with suggestions

## Success Criteria

**Functional Requirements:**
✅ All high-priority API functions protected with 2-minute timeout
✅ Integrated timeout + retry decorators (single decorator per function)
✅ Environment variable configuration for all timeout values
✅ Clear timeout error messages with suggestions
✅ Zero breaking changes to existing functionality

**Technical Requirements:**
✅ <10% performance overhead (timeout checking minimal)
✅ All existing 245 tests continue to pass
✅ New timeout tests achieve >90% coverage
✅ Clean integration in single retry.py module

## Questions for Implementation

1. **Environment Variables**: Should timeout env vars be documented in CLI help?

2. **Error Logging**: Should timeout events be logged at WARNING level like retries?

3. **Fallback Values**: Should invalid timeout env vars use defaults or raise errors?

4. **Decorator Naming**: Keep existing names (`@retry_network_operation`) or rename (`@retry_with_timeout_network_operation`)?

## Confidence Assessment

**Current Confidence: 98%** 🎯 **READY FOR AGENT MODE**

**Knowns:**
✅ Integrated approach is architecturally superior (single responsibility)
✅ High-priority functions precisely identified (6 functions, only 3 have retry currently)
✅ 2-minute default timeout is reasonable for LLM operations
✅ Gap analysis complete: 3 functions need timeout+retry integration
✅ Existing retry test patterns can be extended for timeout testing
✅ Environment variable configuration pattern established
✅ Error handling patterns established in existing retry.py

**Critical Discovery: Incomplete Retry Coverage**
❌ `_create_azure_client()` and `_create_openai_client()` have NO retry protection  
❌ `setup_openai_service()` missing retry decorator
✅ Only 3/6 critical functions currently protected

**Unknowns (2%):**
❓ Minor: Decorator naming preferences (enhance existing vs create new)

**Key Technical Insights:**
1. **Architecture Decision**: Integrated approach eliminates decorator stacking complexity
2. **Priority Correction**: 6 functions need timeout protection, 3 need retry+timeout
3. **Conservative Defaults**: 2-minute timeout for LLM calls, 30s for client creation
4. **Zero Risk Integration**: Enhancing existing decorators maintains compatibility
5. **Bonus Discovery**: Will fix incomplete retry coverage while adding timeouts

**Implementation Strategy Validated:**
- ✅ Enhance existing retry.py with timeout functionality
- ✅ Add missing retry decorators to 3 unprotected functions  
- ✅ Create unified timeout + retry decorators for all 6 functions
- ✅ Apply operation-specific timeouts (120s LLM, 30s client, 45s service)
- ✅ Follow established retry testing patterns

**Ready for Agent Mode Implementation** - will deliver both timeout resilience AND complete retry coverage.