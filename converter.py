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


def extract_parameters(command: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract parameters from command template.
    
    Args:
        command: Command string with {param} placeholders
        
    Returns:
        Dictionary mapping parameter names to their metadata
    """
    params = {}
    
    # Find all {param} patterns
    param_names = re.findall(r'\{(\w+)\}', command)
    
    for param in param_names:
        params[param] = {
            'type': 'string',
            'required': True,
            'description': f'Parameter: {param}'
        }
    
    return params


def generate_langchain_tool_v2(tool_name: str, command_template: str) -> str:
    """
    Generate LangChain tool code with proper parameter handling.
    
    Args:
        tool_name: Name of the tool
        command_template: Command string with {param} placeholders
        
    Returns:
        Python code string for LangChain tool
    """
    params = extract_parameters(command_template)
    
    if not params:
        # No parameters, use simple version
        return generate_langchain_tool(tool_name, command_template)
    
    # Generate function signature
    param_list = ', '.join(f'{p}: str' for p in params.keys())
    
    # Generate docstring
    param_docs = '\n    '.join(
        f'{p}: {meta["description"]}'
        for p, meta in params.items()
    )
    
    # Convert template to f-string format
    command_str = command_template
    
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


def generate_agent_file_v2(skill_path: Path) -> str:
    """
    Generate complete LangChain agent file with parameter support.
    
    Args:
        skill_path: Path to SKILL.md file
        
    Returns:
        Complete Python code for LangChain agent
    """
    metadata = parse_skill_metadata(skill_path)
    commands = extract_tool_commands(skill_path)
    
    skill_name = metadata.get('name', 'unknown')
    description = metadata.get('description', 'No description')
    
    # Generate imports
    imports = '''
from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import subprocess
'''
    
    # Generate tools with parameter support
    tools_code = []
    tool_names = []
    
    for i, cmd in enumerate(commands[:3]):
        if 'wttr.in' in cmd and '{' not in cmd:
            # Add location parameter to static command
            cmd_with_param = cmd.replace('London', '{location}')
            tool_code = generate_langchain_tool_v2(f'{skill_name}_get', cmd_with_param)
            tools_code.append(tool_code)
            tool_names.append(f'{skill_name}_get')
            break
        elif '{' in cmd:
            # Already has parameters
            tool_code = generate_langchain_tool_v2(f'{skill_name}_get', cmd)
            tools_code.append(tool_code)
            tool_names.append(f'{skill_name}_get')
            break
    
    # Generate agent setup
    tools_list = ', '.join(tool_names)
    agent_setup = f'''
# Initialize LLM
llm = ChatOpenAI(temperature=0)

# Define tools
tools = [{tools_list}]

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
    result = agent_executor.invoke({{"input": "What's the weather in Tokyo?"}})
    print(result)
'''
    
    return imports + '\n'.join(tools_code) + agent_setup


if __name__ == '__main__':
    # Example: Convert weather skill with Phase 2 features
    weather_skill = Path('/app/skills/weather/SKILL.md')
    
    if weather_skill.exists():
        print("Phase 2: Generating agent with parameter support...")
        
        agent_code = generate_agent_file_v2(weather_skill)
        
        output_path = Path('weather_agent_v2.py')
        output_path.write_text(agent_code)
        print(f"Generated: {output_path}")
        
        # Show parameter extraction example
        example_cmd = 'curl -s "wttr.in/{location}?format=3"'
        params = extract_parameters(example_cmd)
        print(f"\nExtracted parameters from '{example_cmd}':")
        print(f"  {params}")
