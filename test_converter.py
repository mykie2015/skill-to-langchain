"""
Test suite for skill-to-langchain converter.

Phase 2: Parameter extraction and dynamic command generation.
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


class TestParameterExtraction(unittest.TestCase):
    """Test parameter extraction from commands (Phase 2)."""
    
    def test_extract_url_parameters(self):
        """Test extraction of parameters from URL templates."""
        from converter import extract_parameters
        
        command = 'curl -s "wttr.in/{location}?format=3"'
        params = extract_parameters(command)
        
        self.assertEqual(len(params), 1)
        self.assertIn('location', params)
        self.assertEqual(params['location']['type'], 'string')
        
    def test_extract_multiple_parameters(self):
        """Test extraction of multiple parameters."""
        from converter import extract_parameters
        
        command = 'curl -s "api.example.com/{city}/{country}?units={unit}"'
        params = extract_parameters(command)
        
        self.assertEqual(len(params), 3)
        self.assertIn('city', params)
        self.assertIn('country', params)
        self.assertIn('unit', params)
        
    def test_generate_tool_with_parameters(self):
        """Test generation of LangChain tool with parameters."""
        from converter import generate_langchain_tool_v2
        
        command = 'curl -s "wttr.in/{location}?format=3"'
        tool_code = generate_langchain_tool_v2('get_weather', command)
        
        # Should have location parameter in signature
        self.assertIn('location: str', tool_code)
        # Should use f-string for dynamic command
        self.assertIn('f"', tool_code)
        # Should have proper docstring
        self.assertIn('location:', tool_code)


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
        
    def test_generate_agent_file_v2(self):
        """Test generation of agent file with parameter support."""
        from converter import generate_agent_file_v2
        
        skill_path = Path("/app/skills/weather/SKILL.md")
        agent_code = generate_agent_file_v2(skill_path)
        
        # Should have parameterized tool
        self.assertIn('location: str', agent_code)
        # Should use f-string
        self.assertIn('f"', agent_code)


if __name__ == '__main__':
    unittest.main()
