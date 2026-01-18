"""
Chainlit application for multi-agent research system.

Provides real-time visualization of:
- Researcher agent thinking and tool usage
- Council review process with individual reviewers
- Agent handovers between researcher and council
- Revision flow if research needs improvement
"""

import chainlit as cl
import asyncio
from agents.researcher import create_researcher_agent
from agents.council import create_council_agents, get_reviewer_names
from orchestration.workflow import ResearchOrchestrator
from config import get_all_model_info


@cl.on_chat_start
async def start():
    """
    Initialize the multi-agent research system when chat starts.

    Creates researcher agent, council agents, and orchestrator.
    Displays welcome message with system information.
    """
    # Welcome message
    welcome_message = """# Multi-Agent Research Assistant with Council Review

Welcome! I'm a research system that combines a senior researcher with a council of 3 expert reviewers to ensure high-quality research reports.

## How it works:

1. **Research Phase**: The researcher conducts comprehensive research using multiple tools:
   - Web search across authoritative sources
   - Webpage scraping for detailed content
   - Document analysis (PDFs, papers)
   - Data synthesis from multiple sources
   - Citation tracking and attribution

2. **Council Review**: Your research is independently reviewed by 3 experts:
   - **Dr. Sarah Chen** - Methodological Rigor (source quality, evidence, methodology)
   - **Prof. James Rodriguez** - Comprehensiveness (coverage, perspectives, currency)
   - **Dr. Emily Thompson** - Clarity & Communication (structure, writing, synthesis)

3. **Decision**: Research is accepted if 2 or more reviewers score it 3.0+ out of 5.0

4. **Revision** (if needed): If all reviewers score below 3.0, the researcher revises with feedback

## Ask me to research any topic!

Example queries:
- "Research the current state of quantum computing"
- "Investigate the impact of AI on healthcare"
- "Analyze the causes and effects of climate change"
"""

    await cl.Message(content=welcome_message).send()

    # Display model information
    model_info = get_all_model_info()
    model_msg = "## Models in Use:\n\n"
    for role, info in model_info.items():
        role_name = role.replace('_', ' ').title()
        model_msg += f"**{role_name}**: {info['model_id']}\n"
        model_msg += f"  *{info['description']}*\n\n"

    await cl.Message(content=model_msg).send()

    # Initialize agents
    try:
        researcher = create_researcher_agent()
        council = create_council_agents()
        orchestrator = ResearchOrchestrator(researcher, council)

        # Store in session
        cl.user_session.set("orchestrator", orchestrator)
        cl.user_session.set("iteration_count", 0)

        await cl.Message(content="System initialized and ready! Ask your research question.").send()

    except Exception as e:
        await cl.Message(content=f"Error initializing system: {str(e)}\n\nPlease check your .env file has OPENROUTER_API_KEY set.").send()


@cl.on_message
async def main(message: cl.Message):
    """
    Handle research queries with full agent visualization.

    Args:
        message: User's research query
    """
    orchestrator = cl.user_session.get("orchestrator")

    if not orchestrator:
        await cl.Message(content="Error: System not initialized. Please refresh the page.").send()
        return

    query = message.content
    iteration = 0

    # Full research workflow with visualization
    async with cl.Step(name="Research Workflow", type="tool") as workflow_step:
        workflow_step.input = query

        research_report = None
        all_reviews = []

        while iteration < 2:  # Max 2 iterations
            # Phase 1: Research
            if iteration == 0:
                async with cl.Step(name="Initial Research", type="llm", parent_id=workflow_step.id) as research_step:
                    research_step.input = query

                    await cl.Message(content=f"**Phase 1: Conducting Research** (Iteration {iteration + 1}/2)\n\nThe researcher is gathering information...").send()

                    try:
                        research_report = await asyncio.to_thread(orchestrator.researcher.run, query)
                        research_step.output = research_report[:500] + "..." if len(research_report) > 500 else research_report

                    except Exception as e:
                        research_step.output = f"Error: {str(e)}"
                        await cl.Message(content=f"Research failed: {str(e)}").send()
                        return

            else:
                # Revision phase
                async with cl.Step(name="Research Revision", type="llm", parent_id=workflow_step.id) as revision_step:
                    feedback = orchestrator._synthesize_feedback(all_reviews[-1])
                    revision_prompt = orchestrator._create_revision_prompt(query, research_report, feedback)
                    revision_step.input = "Revising research with council feedback..."

                    await cl.Message(content=f"**Phase 1 (Revision): Improving Research** (Iteration {iteration + 1}/2)\n\nThe researcher is addressing council feedback...").send()

                    try:
                        research_report = await asyncio.to_thread(orchestrator.researcher.run, revision_prompt)
                        revision_step.output = research_report[:500] + "..." if len(research_report) > 500 else research_report

                    except Exception as e:
                        revision_step.output = f"Error: {str(e)}"
                        await cl.Message(content=f"Revision failed: {str(e)}").send()
                        return

            # Display research report
            await cl.Message(content=f"## Research Complete\n\n{research_report}").send()

            # Phase 2: Council Review
            async with cl.Step(name="Council Review", type="tool", parent_id=workflow_step.id) as council_step:
                council_step.input = "Reviewing research quality..."

                await cl.Message(content=f"**Phase 2: Council Review** (Iteration {iteration + 1}/2)\n\n3 expert reviewers are independently assessing the research...").send()

                reviewer_names = get_reviewer_names()
                reviews = []

                # Visualize each reviewer
                for i, name in enumerate(reviewer_names):
                    async with cl.Step(name=f"{name} Review", type="llm", parent_id=council_step.id) as review_step:
                        review_step.input = f"Evaluating based on {name.split('(')[1].replace(')', '')}..."

                        try:
                            review_text = await asyncio.to_thread(orchestrator.council[i].run, research_report)
                            score = orchestrator._extract_score(review_text)
                            recommendation = orchestrator._extract_recommendation(review_text)

                            reviews.append({
                                'reviewer': name,
                                'review_text': review_text,
                                'score': score,
                                'recommendation': recommendation
                            })

                            # Color code based on score
                            if score >= 4.0:
                                score_emoji = "✅"
                            elif score >= 3.0:
                                score_emoji = "✓"
                            else:
                                score_emoji = "⚠️"

                            review_step.output = f"{score_emoji} Score: {score:.1f}/5.0 - {recommendation}"

                        except Exception as e:
                            reviews.append({
                                'reviewer': name,
                                'review_text': f"Error: {str(e)}",
                                'score': 0.0,
                                'recommendation': 'ERROR'
                            })
                            review_step.output = f"Error: {str(e)}"

                scores = [r['score'] for r in reviews]
                council_step.output = f"All reviews complete. Scores: {[f'{s:.1f}' for s in scores]}"

                all_reviews.append({
                    'iteration': iteration + 1,
                    'reviews': reviews,
                    'scores': scores
                })

            # Phase 3: Decision
            passing = sum(1 for score in scores if score >= 3.0)
            accept = passing >= 2

            # Display council reviews
            reviews_msg = f"## Council Review Results (Iteration {iteration + 1})\n\n"
            for review in reviews:
                score_indicator = "🟢" if review['score'] >= 3.0 else "🔴"
                reviews_msg += f"### {score_indicator} {review['reviewer']}\n"
                reviews_msg += f"**Score**: {review['score']:.1f}/5.0 | **Recommendation**: {review['recommendation']}\n\n"
                reviews_msg += f"{review['review_text']}\n\n---\n\n"

            await cl.Message(content=reviews_msg).send()

            # Decision message
            if accept:
                decision_msg = f"""## ✅ Research Accepted!

**Final Scores**: {', '.join([f'{s:.1f}' for s in scores])}
**Passing Reviews**: {passing}/3

The research has met the quality standards ({passing} reviewers scored 3.0 or higher).

**Total Iterations**: {iteration + 1}
"""
                await cl.Message(content=decision_msg).send()
                workflow_step.output = "Research accepted"
                return

            elif iteration < 1:
                # Needs revision
                revision_msg = f"""## 🔄 Revision Requested

**Current Scores**: {', '.join([f'{s:.1f}' for s in scores])}
**Passing Reviews**: {passing}/3

All reviewers scored below 3.0. The researcher will now revise the research based on council feedback.

**Iteration**: {iteration + 1}/2 (moving to revision...)
"""
                await cl.Message(content=revision_msg).send()
                iteration += 1
                continue

            else:
                # Max iterations reached
                final_msg = f"""## ⏭️ Maximum Iterations Reached

**Final Scores**: {', '.join([f'{s:.1f}' for s in scores])}
**Passing Reviews**: {passing}/3

The research has been through {iteration + 1} iterations. While it didn't fully meet the acceptance criteria, this is the final version.

Consider the council feedback for future research improvements.
"""
                await cl.Message(content=final_msg).send()
                workflow_step.output = "Completed maximum iterations"
                return


if __name__ == "__main__":
    cl.run()
