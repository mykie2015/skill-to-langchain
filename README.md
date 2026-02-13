# OpenClaw Skill to LangChain Converter

Convert OpenClaw skill files into equivalent LangChain agent Python code.

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

### Limitations (Phase 1)

- Only handles simple command-execution patterns
- No support for complex workflows or state management
- Hardcoded to first command found (no multi-tool support yet)
- No parameter extraction from command templates
- Generated agent requires OpenAI API key to run

### Phase 2: Parameter Extraction ✅

- ✅ Extract parameters from command templates (`{param}`)
- ✅ Generate parameterized LangChain tools
- ✅ Support dynamic command execution with f-strings

### Phase 3: Multi-Tool Workflow Support ✅

- ✅ Extract multiple distinct tools from a skill
- ✅ Generate multiple `@tool` decorated functions
- ✅ Coordinate multiple tools in agent workflow
- ✅ Support complex skills like GitHub CLI (issue, pr, run, api)

### Example: GitHub Multi-Tool Agent

```python
# Generated from github skill - multiple tools coordinated
@tool
def github_pr_checks() -> str:
    """Execute pr checks command."""
    # ...

@tool
def github_run_list() -> str:
    """Execute run list command."""
    # ...

# Agent can coordinate multiple tools
tools = [github_pr_checks, github_run_list, ...]
agent_executor = AgentExecutor(agent=agent, tools=tools)
```

### Next Steps (Phase 4)

- [ ] Equivalence testing - validate generated agent matches original behavior
- [ ] Integration tests with real LangChain execution
- [ ] Handle conditional logic and workflows
- [ ] Support more skill patterns (API calls, file operations)

## Files

- `converter.py` - Main conversion logic (Phase 1-3)
- `test_converter.py` - Test suite (10 tests, all passing)
- `weather_agent.py` - Example single-tool agent
- `github_agent_v3.py` - Example multi-tool agent (Phase 3)
- `README.md` - This file

## Success Criteria ✅

- [x] Converter successfully processes weather skill (Phase 1)
- [x] Parameter extraction working (Phase 2)
- [x] Multi-tool workflow support (Phase 3)
- [x] Generated LangChain agent code is syntactically valid
- [x] Clear conversion approach documented
- [x] Tests validate each conversion step (10/10 passing)

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

**Status**: Phase 3 complete. Multi-tool workflow support implemented. Ready for Phase 4 (equivalence testing).
