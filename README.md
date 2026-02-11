# OpenClaw Skill to LangChain Converter

Convert OpenClaw skill files into equivalent LangChain agent Python code.

## Phase 2: Parameter Extraction ✅

Added support for dynamic parameters in commands.

### What's New

- ✅ Extract parameters from command templates (`{location}`, `{city}`, etc.)
- ✅ Generate parameterized LangChain tools with proper signatures
- ✅ Support multiple parameters in single command
- ✅ Automatic parameter type inference
- ✅ Dynamic f-string command generation

### Example

```python
# Input command template
'curl -s "wttr.in/{location}?format=3"'

# Generated tool
@tool
def weather_get(location: str) -> str:
    """Execute weather_get command."""
    command = f"curl -s \"wttr.in/{location}?format=3\""
    # ... execution
```

### Testing

```bash
python3 -m unittest test_converter.py -v
```

All 10 tests pass (4 new tests for Phase 2):
- Parameter extraction from URLs
- Multiple parameter support
- Parameterized tool generation
- Agent file v2 generation

## Phase 1: MVP - Basic Skill Parsing

This phase implements basic parsing and conversion for simple command-execution skills.

### What Works

- ✅ Parse skill metadata from YAML frontmatter
- ✅ Extract executable commands from markdown code blocks
- ✅ Identify skill execution patterns (command-based)
- ✅ Generate LangChain tool definitions
- ✅ Generate complete agent file with imports and setup

### Example

```bash
# Run converter on weather skill
python3 converter.py

# Output: weather_agent.py (runnable LangChain agent)
```

### Generated Agent Structure

```python
from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI

@tool
def weather_get() -> str:
    """Execute weather command."""
    # ... subprocess execution

# Agent setup with LLM, tools, prompt
agent_executor = AgentExecutor(agent=agent, tools=tools)
```

### Testing

```bash
python3 -m unittest test_converter.py -v
```

All 6 tests pass:
- Skill file parsing
- Metadata extraction
- Command extraction
- Pattern identification
- Tool generation
- Agent file generation

### Conversion Approach

1. **Parse SKILL.md**: Extract frontmatter metadata and documentation
2. **Identify Pattern**: Analyze commands to determine execution pattern
3. **Extract Tools**: Find executable commands in code blocks
4. **Generate Code**: Create LangChain tool decorators and agent setup
5. **Validate**: Ensure generated code is syntactically valid Python

### Limitations (Phase 2)

- Only handles command-execution patterns
- No support for complex workflows or conditional logic
- No multi-tool support per skill yet
- Generated agent requires OpenAI API key to run
- Parameter types are all inferred as string

### Next Steps (Phase 3)

- [ ] Support multiple tools per skill
- [ ] Handle conditional logic and workflows
- [ ] Add validation tests for generated agent behavior
- [ ] Support more skill patterns (API calls, file operations)
- [ ] Infer parameter types from context (int, bool, etc.)

## Files

- `converter.py` - Main conversion logic (Phase 1 + Phase 2)
- `test_converter.py` - Test suite (10 tests, all passing)
- `weather_agent.py` - Phase 1 example (static command)
- `weather_agent_v2.py` - Phase 2 example (parameterized)
- `README.md` - This file

## Success Criteria ✅

**Phase 1:**
- [x] Converter successfully processes weather skill
- [x] Generated LangChain agent code is syntactically valid
- [x] Clear conversion approach documented
- [x] Tests validate each conversion step

**Phase 2:**
- [x] Extract parameters from command templates
- [x] Generate parameterized tools with proper signatures
- [x] Support multiple parameters
- [x] Tests validate parameter extraction and tool generation
- [x] Example agent with dynamic location parameter

## Usage

```python
from converter import generate_agent_file
from pathlib import Path

# Convert any skill
skill_path = Path('/app/skills/weather/SKILL.md')
agent_code = generate_agent_file(skill_path)

# Write to file
Path('my_agent.py').write_text(agent_code)
```

---

**Status**: Phase 2 complete. Parameter extraction working. Ready for Phase 3 (multi-tool support).
