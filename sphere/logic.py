# logic.py
# Core Analysis Engine with Real LLM Integration
# Author: Kent Beck (Execution), Ada (Architecture)

import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from . import persona_logic
from . import audit
from . import llm_providers


def run_single_agent(
    agent: Dict,
    query: str,
    context: str = "",
    previous_insights: str = ""
) -> Tuple[bool, str]:
    """
    Run a single agent's analysis using the configured LLM.
    
    Args:
        agent: Agent configuration with role, perspective, and prompt
        query: The user's query
        context: Additional context for the analysis
        previous_insights: Accumulated insights from previous agents
    
    Returns:
        Tuple of (success, agent_response or error)
    """
    role = agent.get("role", "Analyst")
    perspective = agent.get("perspective", "")
    agent_prompt = agent.get("prompt", "")
    
    # Build the system prompt for this agent
    system_prompt = f"""You are the {role} agent in a multi-agent analysis system called Sphere.

Your Perspective: {perspective}

Your Role: {agent_prompt}

Guidelines:
- Provide analysis from your unique perspective
- Be concise but insightful (2-4 paragraphs)
- Focus on aspects others might miss
- Build upon previous insights when relevant
- End with a clear, actionable insight or observation
"""

    # Build the user message
    user_message = f"""## Query to Analyze
{query}

"""
    
    if context:
        user_message += f"""## Additional Context
{context}

"""
    
    if previous_insights:
        user_message += f"""## Previous Agent Insights
{previous_insights}

"""
    
    user_message += f"""Please provide your analysis as the {role}. Focus on your unique perspective and add value beyond what has already been said."""

    messages = [{"role": "user", "content": user_message}]
    
    success, response = llm_providers.call_llm_with_retry(
        messages=messages,
        system_prompt=system_prompt,
        max_retries=2,
        temperature=0.7
    )
    
    return success, response


def synthesize_insights(
    query: str,
    agent_insights: List[Dict],
    persona_name: str
) -> Tuple[bool, str]:
    """
    Synthesize all agent insights into a final report.
    
    Args:
        query: The original query
        agent_insights: List of dicts with 'role' and 'insight'
        persona_name: Name of the persona used
    
    Returns:
        Tuple of (success, synthesis or error)
    """
    system_prompt = """You are the Master Synthesizer in the Sphere multi-agent analysis system.

Your role is to:
1. Synthesize insights from multiple agent perspectives into a coherent analysis
2. Identify key themes, agreements, and productive tensions
3. Extract actionable recommendations
4. Present a clear, well-structured final report

Format your response as a professional analysis report with:
- Executive Summary (2-3 sentences)
- Key Insights (numbered list of the most important findings)
- Synthesis (how the perspectives connect and inform each other)
- Recommendations (concrete next steps or actions)
- Areas for Further Investigation (optional)
"""

    # Build the insights summary
    insights_text = ""
    for item in agent_insights:
        insights_text += f"""### {item['role']} Perspective
{item['insight']}

---

"""

    user_message = f"""## Original Query
{query}

## Agent Perspectives ({len(agent_insights)} agents from '{persona_name}' persona)

{insights_text}

Please synthesize these perspectives into a comprehensive analysis report. Identify the key themes, areas of agreement, productive tensions, and actionable recommendations."""

    messages = [{"role": "user", "content": user_message}]
    
    success, response = llm_providers.call_llm_with_retry(
        messages=messages,
        system_prompt=system_prompt,
        max_retries=2,
        temperature=0.5  # Lower temperature for synthesis
    )
    
    return success, response


def full_pmpe_analysis(
    query: str,
    context: str = "",
    max_agents: Optional[int] = None,
    progress_callback=None
) -> Tuple[str, str]:
    """
    Run the full PolyMath Perspective Engine (PMPE) analysis workflow.
    
    This runs each agent sequentially, accumulating insights, then synthesizes
    all perspectives into a final report.
    
    Args:
        query: The user's query to analyze
        context: Additional context for the analysis
        max_agents: Optional limit on number of agents to run
        progress_callback: Optional callback function for progress updates
    
    Returns:
        Tuple of (synthesis_report, audit_trail)
    """
    audit_trail = []
    start_time = time.time()
    
    audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] ANALYSIS_STARTED - Query: '{query[:100]}...'")
    
    # Check if LLM is configured
    llm_status = llm_providers.get_llm_status()
    if not llm_status["configured"]:
        error_msg = "No LLM configured. Run: sphere llm setup --provider <provider>"
        audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] ERROR - {error_msg}")
        return f"## Error\n\n{error_msg}", "\n".join(audit_trail)
    
    audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] LLM_PROVIDER - {llm_status['provider']} ({llm_status['model']})")
    
    # Get active persona and agents
    active_persona = persona_logic.get_active_persona()
    agents = active_persona.get("agents", [])
    persona_name = active_persona.get("name", "unknown")
    
    if not agents:
        error_msg = "No agents found in active persona."
        audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] ERROR - {error_msg}")
        return f"## Error\n\n{error_msg}", "\n".join(audit_trail)
    
    # Limit agents if specified
    if max_agents:
        agents = agents[:max_agents]
    
    audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] PERSONA_LOADED - '{persona_name}' with {len(agents)} agents")
    
    # Run each agent
    agent_insights = []
    accumulated_insights = ""
    
    for i, agent in enumerate(agents):
        role = agent.get("role", f"Agent{i+1}")
        
        if progress_callback:
            progress_callback(f"Running {role}... ({i+1}/{len(agents)})")
        
        audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] AGENT_START - {role}")
        
        success, response = run_single_agent(
            agent=agent,
            query=query,
            context=context,
            previous_insights=accumulated_insights if i > 0 else ""
        )
        
        if success:
            agent_insights.append({
                "role": role,
                "insight": response
            })
            accumulated_insights += f"\n### {role}\n{response}\n"
            audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] AGENT_COMPLETE - {role} (success)")
        else:
            audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] AGENT_FAILED - {role}: {response}")
            # Continue with other agents even if one fails
    
    if not agent_insights:
        error_msg = "All agents failed. Check your LLM configuration."
        audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] ERROR - {error_msg}")
        return f"## Error\n\n{error_msg}", "\n".join(audit_trail)
    
    # Synthesize all insights
    if progress_callback:
        progress_callback("Synthesizing insights...")
    
    audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] SYNTHESIS_START - Combining {len(agent_insights)} perspectives")
    
    success, synthesis = synthesize_insights(
        query=query,
        agent_insights=agent_insights,
        persona_name=persona_name
    )
    
    if not success:
        # Fall back to a simple concatenation if synthesis fails
        audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] SYNTHESIS_FALLBACK - Using raw insights")
        synthesis = f"""## Analysis Report

**Query:** {query}
**Persona:** {persona_name}
**Agents:** {len(agent_insights)}

---

{accumulated_insights}

---

*Note: Automated synthesis failed. Raw agent insights shown above.*
"""
    else:
        audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] SYNTHESIS_COMPLETE")
    
    # Add metadata to the report
    elapsed_time = time.time() - start_time
    
    final_report = f"""# Sphere Analysis Report

**Query:** {query}
**Persona:** {persona_name}
**Agents:** {len(agent_insights)}
**LLM:** {llm_status['provider']} ({llm_status['model']})
**Generated:** {datetime.utcnow().isoformat()}Z
**Processing Time:** {elapsed_time:.1f}s

---

{synthesis}

---

## Individual Agent Perspectives

{accumulated_insights}
"""
    
    audit_trail.append(f"[{datetime.utcnow().isoformat()}Z] ANALYSIS_COMPLETE - {elapsed_time:.1f}s elapsed")
    
    return final_report, "\n".join(audit_trail)


def quick_analysis(query: str, num_agents: int = 3) -> Tuple[str, str]:
    """
    Run a quick analysis with a limited number of agents.
    
    Args:
        query: The query to analyze
        num_agents: Number of agents to use (default: 3)
    
    Returns:
        Tuple of (synthesis, audit_trail)
    """
    return full_pmpe_analysis(query, max_agents=num_agents)


def single_perspective(query: str, agent_role: str) -> Tuple[bool, str]:
    """
    Get a single agent's perspective on a query.
    
    Args:
        query: The query to analyze
        agent_role: The role of the agent to use
    
    Returns:
        Tuple of (success, response)
    """
    active_persona = persona_logic.get_active_persona()
    agents = active_persona.get("agents", [])
    
    # Find the requested agent
    agent = None
    for a in agents:
        if a.get("role", "").lower() == agent_role.lower():
            agent = a
            break
    
    if not agent:
        return False, f"Agent '{agent_role}' not found in active persona."
    
    return run_single_agent(agent, query)
