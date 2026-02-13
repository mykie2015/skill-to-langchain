"""
OpenClaw Skill to LangChain Agent Converter

Converts OpenClaw skill files (SKILL.md) into equivalent LangChain agent Python code.

Phase 1: Basic parsing and structure extraction.
"""

import re
from pathlib import Path
from typing import Dict, List, Any


def parse_skill_metadata(skill_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from skill file frontmatter.
    
    Args:
        skill_path: Path to SKILL.md file
        
    Returns:
        Dictionary containing skill metadata
    """
    content = skill_path.read_text()
    
    # Extract YAML frontmatter
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
    
    metadata = {}
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        
        # Parse simple key: value pairs
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
    
    return metadata


def extract_tool_commands(skill_path: Path) -> List[str]:
    """
    Extract executable commands from skill documentation.
    
    Args:
        skill_path: Path to SKILL.md file
        
    Returns:
        List of command strings found in code blocks
    """
    content = skill_path.read_text()
    commands = []
    
    # Find bash code blocks
    code_blocks = re.findall(r'```bash\n(.*?)\n```', content, re.DOTALL)
    
    for block in code_blocks:
        # Extract actual commands (skip comments and output examples)
        for line in block.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                commands.append(line)
    
    return commands


def identify_skill_pattern(skill_path: Path) -> Dict[str, Any]:
    """
    Identify the execution pattern of a skill.
    
    Args:
        skill_path: Path to SKILL.md file
        
    Returns:
        Dictionary describing the skill pattern
    """
    commands = extract_tool_commands(skill_path)
    
    # Analyze commands to determine pattern
    pattern = {
        'type': 'command_execution',
        'primary_tool': None,
        'requires_input': False,
        'output_format': 'text'
    }
    
    if commands:
        first_command = commands[0]
        
        # Identify primary tool
        if first_command.startswith('curl'):
            pattern['primary_tool'] = 'curl'
        elif first_command.startswith('gh'):
            pattern['primary_tool'] = 'gh'
        
        # Check for input parameters
        if '{' in first_command or '$' in first_command:
            pattern['requires_input'] = True
    
    return pattern


def generate_langchain_tool(tool_name: str, command_template: str) -> str:
    """
    Generate LangChain tool code from a command template.
    
    Args:
        tool_name: Name of the tool
        command_template: Command string with {param} placeholders
        
    Returns:
        Python code string for LangChain tool
    """
    # Extract parameters from template
    params = re.findall(r'\{(\w+)\}', command_template)
    
    # Generate function signature
    param_list = ', '.join(f'{p}: str' for p in params)
    
    # Generate docstring
    param_docs = '\n    '.join(f'{p}: Parameter for the command' for p in params)
    
    # Generate command execution
    command_str = command_template
    for param in params:
        command_str = command_str.replace(f'{{{param}}}', f'{{{param}}}')
    
    tool_code = f'''
@tool
def {tool_name}({param_list}) -> str:
    """
    Execute {tool_name} command.
    
    Args:
    {param_docs}
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = f"{command_str}"
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout if result.returncode == 0 else result.stderr
'''
    
    return tool_code


def generate_agent_file(skill_path: Path) -> str:
    """
    Generate complete LangChain agent file from skill.
    
    Args:
        skill_path: Path to SKILL.md file
        
    Returns:
        Complete Python code for LangChain agent
    """
    metadata = parse_skill_metadata(skill_path)
    commands = extract_tool_commands(skill_path)
    pattern = identify_skill_pattern(skill_path)
    
    skill_name = metadata.get('name', 'unknown')
    description = metadata.get('description', 'No description')
    
    # Generate imports
    imports = '''
from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import subprocess
'''
    
    # Generate tools
    tools_code = []
    for i, cmd in enumerate(commands[:3]):  # Limit to first 3 commands for MVP
        if 'wttr.in' in cmd:
            tool_code = generate_langchain_tool(f'{skill_name}_get', cmd)
            tools_code.append(tool_code)
            break
    
    # Generate agent setup
    agent_setup = f'''
# Initialize LLM
llm = ChatOpenAI(temperature=0)

# Define tools
tools = [{skill_name}_get]

# Create agent prompt
prompt = PromptTemplate.from_template("""
You are a helpful assistant that can {description.lower()}.

Available tools: {{tools}}
Tool names: {{tool_names}}

Question: {{input}}
Thought: {{agent_scratchpad}}
""")

# Create agent
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Example usage
if __name__ == "__main__":
    result = agent_executor.invoke({{"input": "What's the weather in London?"}})
    print(result)
'''
    
    return imports + '\n'.join(tools_code) + agent_setup


def extract_workflow_tools(skill_path: Path) -> List[Dict[str, str]]:
    """
    Extract multiple distinct tools from a skill workflow.
    
    Phase 3: Identify different command patterns and group them into tools.
    
    Args:
        skill_path: Path to SKILL.md file
        
    Returns:
        List of tool specifications with name and command template
    """
    commands = extract_tool_commands(skill_path)
    metadata = parse_skill_metadata(skill_path)
    skill_name = metadata.get('name', 'unknown')
    
    tools = []
    seen_patterns = set()
    
    for cmd in commands:
        # Identify the primary command (first word)
        parts = cmd.split()
        if not parts:
            continue
            
        primary_cmd = parts[0]
        
        # For gh CLI, identify subcommands
        if primary_cmd == 'gh' and len(parts) > 1:
            subcommand = parts[1]
            action = parts[2] if len(parts) > 2 else 'default'
            
            # Create unique tool name
            tool_pattern = f"{primary_cmd}_{subcommand}_{action}"
            
            if tool_pattern not in seen_patterns:
                tools.append({
                    'name': f"{skill_name}_{subcommand}_{action}",
                    'command': cmd,
                    'description': f"Execute {subcommand} {action} command"
                })
                seen_patterns.add(tool_pattern)
        
        # For other commands, use primary command as pattern
        elif primary_cmd not in seen_patterns:
            tools.append({
                'name': f"{skill_name}_{primary_cmd}",
                'command': cmd,
                'description': f"Execute {primary_cmd} command"
            })
            seen_patterns.add(primary_cmd)
    
    return tools


def generate_workflow_tools(tools_spec: List[Dict[str, str]]) -> str:
    """
    Generate LangChain tool code for multiple tools in a workflow.
    
    Phase 3: Create multiple @tool decorated functions.
    
    Args:
        tools_spec: List of tool specifications with name, command, description
        
    Returns:
        Python code string with multiple tool definitions
    """
    tools_code = []
    
    for tool in tools_spec:
        name = tool['name']
        command = tool['command']
        description = tool.get('description', f"Execute {name}")
        
        # Extract parameters from command
        params = re.findall(r'<(\w+)>|\{(\w+)\}', command)
        # Flatten tuples from regex groups
        params = [p for group in params for p in group if p]
        
        # Generate function signature
        if params:
            param_list = ', '.join(f'{p}: str' for p in params)
            param_docs = '\n    '.join(f'{p}: Parameter for the command' for p in params)
            
            # Replace placeholders in command
            command_str = command
            for param in params:
                command_str = command_str.replace(f'<{param}>', f'{{{param}}}')
                command_str = command_str.replace(f'{{{param}}}', f'{{{param}}}')
            
            tool_code = f'''
@tool
def {name}({param_list}) -> str:
    """
    {description}
    
    Args:
    {param_docs}
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = f"{command_str}"
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout if result.returncode == 0 else result.stderr
'''
        else:
            # No parameters
            tool_code = f'''
@tool
def {name}() -> str:
    """
    {description}
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = "{command}"
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout if result.returncode == 0 else result.stderr
'''
        
        tools_code.append(tool_code)
    
    return '\n'.join(tools_code)


def generate_agent_file_v3(skill_path: Path) -> str:
    """
    Generate complete LangChain agent file with multi-tool workflow support.
    
    Phase 3: Handle skills with multiple commands and coordinate them.
    
    Args:
        skill_path: Path to SKILL.md file
        
    Returns:
        Complete Python code for LangChain agent with multiple tools
    """
    metadata = parse_skill_metadata(skill_path)
    tools_spec = extract_workflow_tools(skill_path)
    
    skill_name = metadata.get('name', 'unknown')
    description = metadata.get('description', 'No description')
    
    # Generate imports
    imports = '''
from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import subprocess
'''
    
    # Generate all tools
    tools_code = generate_workflow_tools(tools_spec)
    
    # Generate tool names list
    tool_names = [tool['name'] for tool in tools_spec]
    tools_list = ', '.join(tool_names)
    
    # Generate agent setup
    agent_setup = f'''
# Initialize LLM
llm = ChatOpenAI(temperature=0)

# Define tools
tools = [{tools_list}]

# Create agent prompt
prompt = PromptTemplate.from_template("""
You are a helpful assistant that can {description.lower()}.

You have access to multiple tools for different operations.

Available tools: {{tools}}
Tool names: {{tool_names}}

Question: {{input}}
Thought: {{agent_scratchpad}}
""")

# Create agent
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Example usage
if __name__ == "__main__":
    # Example: List issues and PRs
    result = agent_executor.invoke({{"input": "Show me the recent issues and pull requests"}})
    print(result)
'''
    
    return imports + tools_code + agent_setup


if __name__ == '__main__':
    # Example: Convert weather skill
    weather_skill = Path('/app/skills/weather/SKILL.md')
    
    if weather_skill.exists():
        print("Parsing weather skill...")
        metadata = parse_skill_metadata(weather_skill)
        print(f"Metadata: {metadata}")
        
        commands = extract_tool_commands(weather_skill)
        print(f"\nFound {len(commands)} commands")
        
        pattern = identify_skill_pattern(weather_skill)
        print(f"\nPattern: {pattern}")
        
        print("\nGenerating LangChain agent...")
        agent_code = generate_agent_file(weather_skill)
        
        output_path = Path('weather_agent.py')
        output_path.write_text(agent_code)
        print(f"Generated: {output_path}")
