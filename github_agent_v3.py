
from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import subprocess

@tool
def github_pr_checks() -> str:
    """
    Execute pr checks command
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = "gh pr checks 55 --repo owner/repo"
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout if result.returncode == 0 else result.stderr


@tool
def github_run_list() -> str:
    """
    Execute run list command
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = "gh run list --repo owner/repo --limit 10"
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout if result.returncode == 0 else result.stderr


@tool
def github_run_view() -> str:
    """
    Execute run view command
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = "gh run view <run-id> --repo owner/repo"
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout if result.returncode == 0 else result.stderr


@tool
def github_api_repos/owner/repo/pulls/55() -> str:
    """
    Execute api repos/owner/repo/pulls/55 command
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = "gh api repos/owner/repo/pulls/55 --jq '.title, .state, .user.login'"
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout if result.returncode == 0 else result.stderr


@tool
def github_issue_list() -> str:
    """
    Execute issue list command
    
    Returns:
        Command output as string
    """
    import subprocess
    
    command = "gh issue list --repo owner/repo --json number,title --jq '.[] | "\(.number): \(.title)"'"
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
tools = [github_pr_checks, github_run_list, github_run_view, github_api_repos/owner/repo/pulls/55, github_issue_list]

# Create agent prompt
prompt = PromptTemplate.from_template("""
You are a helpful assistant that can "interact with github using the `gh` cli. use `gh issue`, `gh pr`, `gh run`, and `gh api` for issues, prs, ci runs, and advanced queries.".

You have access to multiple tools for different operations.

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
    # Example: List issues and PRs
    result = agent_executor.invoke({"input": "Show me the recent issues and pull requests"})
    print(result)
