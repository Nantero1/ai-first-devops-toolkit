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

# Mode: AGENT ⚡

Current Task: Add Jinja2 template support to llm_ci_runner.py with .jinja and .j2 file extension detection

## 🎯 **IMPLEMENTATION PLAN** ⭐

### **✅ STRATEGY DEFINED:**
- **Template format detection**: File extension-based (.hbs = Handlebars, .jinja/.j2 = Jinja2)
- **Unified approach**: Create load_template() function that detects format and calls appropriate loader
- **Backward compatibility**: Maintain existing Handlebars support unchanged
- **Same parsing**: Both formats produce <message> blocks, so parse_rendered_template_to_chat_history() works for both

### **🔧 IMPLEMENTATION TASKS:**

#### **Task 1**: Add Jinja2PromptTemplate Import ✅ **READY**
- [ ] Add Jinja2PromptTemplate to imports
- [ ] Update import section with proper organization

#### **Task 2**: Create Template Format Detection ✅ **READY**
- [ ] Create get_template_format() function to detect by file extension
- [ ] Support .hbs (Handlebars), .jinja, .j2 (Jinja2)

#### **Task 3**: Create Jinja2 Template Loader ✅ **READY**
- [ ] Create load_jinja2_template() function similar to load_handlebars_template()
- [ ] Use template_format="jinja2" for Jinja2PromptTemplate

#### **Task 4**: Create Unified Template Loader ✅ **READY**
- [ ] Create load_template() function that detects format and calls appropriate loader
- [ ] Maintain backward compatibility with existing Handlebars support

#### **Task 5**: Update Main Execution Flow ✅ **READY**
- [ ] Update main() to use load_template() instead of load_handlebars_template()
- [ ] Update render_template() to handle both template types

#### **Task 6**: Create Jinja2 Example ✅ **READY**
- [ ] Create examples/05-templates/jinja2-example/ directory
- [ ] Add template.jinja, template-vars.yaml, schema.yaml, README.md

#### **Task 7**: Update Tests ✅ **READY**
- [ ] Add tests for Jinja2 template loading
- [ ] Add tests for template format detection
- [ ] Update existing template tests to use unified approach

#### **Task 8**: Update Documentation ✅ **READY**
- [ ] Update help text to mention Jinja2 support
- [ ] Update examples README
- [ ] Update main README

## 🚀 **READY TO IMPLEMENT**

**Confidence**: 95% - Clear implementation strategy with all requirements defined
**Backward Compatibility**: ✅ **MAINTAINED** - Existing Handlebars support unchanged
**Template Detection**: ✅ **DESIGNED** - File extension-based detection
**Unified Architecture**: ✅ **PLANNED** - Single load_template() function with format detection
