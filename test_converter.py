"""
Test suite for skill-to-langchain converter.

Phase 1: Test basic skill parsing and structure extraction.
"""

import unittest
import os
from pathlib import Path


class TestSkillParser(unittest.TestCase):
    """Test parsing of OpenClaw skill files."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.weather_skill_path = Path("/app/skills/weather/SKILL.md")
        
    def test_skill_file_exists(self):
        """Test that we can locate the weather skill."""
        self.assertTrue(self.weather_skill_path.exists())
        
    def test_parse_skill_metadata(self):
        """Test extraction of skill metadata from frontmatter."""
        from converter import parse_skill_metadata
        
        metadata = parse_skill_metadata(self.weather_skill_path)
        
        self.assertEqual(metadata['name'], 'weather')
        self.assertIn('description', metadata)
        self.assertIn('Get current weather', metadata['description'])
        
    def test_extract_tool_commands(self):
        """Test extraction of executable commands from skill."""
        from converter import extract_tool_commands
        
        commands = extract_tool_commands(self.weather_skill_path)
        
        # Should find curl commands for wttr.in
        self.assertGreater(len(commands), 0)
        self.assertTrue(any('wttr.in' in cmd for cmd in commands))
        
    def test_identify_skill_pattern(self):
        """Test identification of skill execution pattern."""
        from converter import identify_skill_pattern
        
        pattern = identify_skill_pattern(self.weather_skill_path)
        
        # Weather skill is a simple command execution pattern
        self.assertEqual(pattern['type'], 'command_execution')
        self.assertIn('primary_tool', pattern)
        self.assertEqual(pattern['primary_tool'], 'curl')


class TestLangChainGeneration(unittest.TestCase):
    """Test LangChain agent code generation."""
    
    def test_generate_langchain_tool(self):
        """Test generation of LangChain tool from skill command."""
        from converter import generate_langchain_tool
        
        command = 'curl -s "wttr.in/{location}?format=3"'
        tool_code = generate_langchain_tool('weather', command)
        
        # Should generate valid Python code
        self.assertIn('def ', tool_code)
        self.assertIn('location', tool_code)
        self.assertIn('subprocess', tool_code)
        
    def test_generate_agent_file(self):
        """Test generation of complete LangChain agent file."""
        from converter import generate_agent_file
        
        skill_path = Path("/app/skills/weather/SKILL.md")
        agent_code = generate_agent_file(skill_path)
        
        # Should contain LangChain imports
        self.assertIn('from langchain', agent_code)
        # Should contain tool definition
        self.assertIn('@tool', agent_code)
        # Should contain agent initialization
        self.assertIn('agent', agent_code.lower())


class TestMultiToolWorkflow(unittest.TestCase):
    """Test Phase 3: Multi-tool workflow support."""
    
    def test_extract_multiple_tools_from_skill(self):
        """Test extraction of multiple distinct tools from a skill."""
        from converter import extract_workflow_tools
        
        # GitHub skill has multiple commands (issue, pr, run, api)
        github_skill_path = Path("/app/skills/github/SKILL.md")
        if github_skill_path.exists():
            tools = extract_workflow_tools(github_skill_path)
            
            # Should identify multiple distinct tools
            self.assertGreater(len(tools), 1)
            # Each tool should have name and command
            for tool in tools:
                self.assertIn('name', tool)
                self.assertIn('command', tool)
    
    def test_generate_multiple_langchain_tools(self):
        """Test generation of multiple LangChain tools from workflow."""
        from converter import generate_workflow_tools
        
        tools_spec = [
            {'name': 'github_issue_list', 'command': 'gh issue list'},
            {'name': 'github_pr_list', 'command': 'gh pr list'}
        ]
        
        tools_code = generate_workflow_tools(tools_spec)
        
        # Should generate code for both tools
        self.assertIn('github_issue_list', tools_code)
        self.assertIn('github_pr_list', tools_code)
        self.assertIn('@tool', tools_code)
        # Should have multiple @tool decorators
        self.assertGreaterEqual(tools_code.count('@tool'), 2)
    
    def test_agent_with_multiple_tools(self):
        """Test agent generation with multiple tools in workflow."""
        from converter import generate_agent_file_v3
        
        github_skill_path = Path("/app/skills/github/SKILL.md")
        if github_skill_path.exists():
            agent_code = generate_agent_file_v3(github_skill_path)
            
            # Should contain multiple tool definitions
            self.assertGreater(agent_code.count('@tool'), 1)
            # Should have tools list with multiple items
            self.assertIn('tools = [', agent_code)
            # Should coordinate multiple tools
            self.assertIn('github', agent_code.lower())
    
    def test_workflow_coordination_logic(self):
        """Test that agent can coordinate multiple tools in sequence."""
        from converter import generate_agent_file_v3
        
        github_skill_path = Path("/app/skills/github/SKILL.md")
        if github_skill_path.exists():
            agent_code = generate_agent_file_v3(github_skill_path)
            
            # Should have agent executor that can handle multiple tools
            self.assertIn('AgentExecutor', agent_code)
            # Should have prompt that mentions multiple capabilities
            self.assertIn('tools', agent_code.lower())


if __name__ == '__main__':
    unittest.main()
