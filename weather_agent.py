
from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import subprocess

@tool
def weather_get() -> str:
    """
    Execute weather_get command.
    
    Args:
    
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = f"curl -s "wttr.in/London?format=3""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout if result.returncode == 0 else result.stderr

# Initialize LLM
llm = ChatOpenAI(temperature=0)

# Define tools
tools = [weather_get]

# Create agent prompt
prompt = PromptTemplate.from_template("""
You are a helpful assistant that can get current weather and forecasts (no api key required)..

Available tools: {tools}
Tool names: {tool_names}

Question: {input}
Thought: {agent_scratchpad}
""")

# Create agent
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Example usage
if __name__ == "__main__":
    result = agent_executor.invoke({"input": "What's the weather in London?"})
    print(result)
