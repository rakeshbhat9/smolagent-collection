"""
Multi-agent orchestration workflow.

Coordinates the researcher agent and council review agents with conditional retry logic.

Workflow:
1. Researcher conducts research
2. Council reviews in parallel (3 independent reviewers)
3. Decision: Accept if 2+ reviewers score >= 3, else retry once
4. If retry: Researcher revises with aggregated feedback
5. Return final result with all reviews
"""

import re
import asyncio
from typing import Dict, List


class ResearchOrchestrator:
    """
    Orchestrates the multi-agent research workflow.

    Manages interaction between researcher agent and council review agents,
    implementing the conditional retry logic based on council scores.
    """

    def __init__(self, researcher_agent, council_agents: List):
        """
        Initialize the orchestrator.

        Args:
            researcher_agent: The main researcher agent
            council_agents: List of 3 council review agents
        """
        self.researcher = researcher_agent
        self.council = council_agents
        self.max_iterations = 2  # Initial research + 1 revision max

    async def execute_research(self, query: str) -> Dict:
        """
        Execute the full research workflow with council review.

        Args:
            query (str): The research query/question

        Returns:
            dict: {
                'status': 'accepted' or 'completed_max_iterations',
                'research_report': str (final research report),
                'all_reviews': list (all review rounds),
                'iterations': int (number of iterations completed),
                'final_scores': list (final round scores)
            }
        """
        iteration = 0
        research_report = None
        all_reviews = []

        while iteration < self.max_iterations:
            # Phase 1: Research (or revision)
            if iteration == 0:
                # Initial research
                research_report = await self._conduct_research(query)
            else:
                # Revision with feedback
                feedback = self._synthesize_feedback(all_reviews[-1])
                research_report = await self._revise_research(query, research_report, feedback)

            # Phase 2: Council review (parallel)
            reviews = await self._parallel_council_review(research_report)
            scores = [review['score'] for review in reviews]
            all_reviews.append({
                'iteration': iteration + 1,
                'reviews': reviews,
                'scores': scores
            })

            # Phase 3: Decision (2+ with 3+ = accept, all <3 = retry)
            accept = self._evaluate_acceptance(scores)

            if accept or iteration == self.max_iterations - 1:
                return {
                    'status': 'accepted' if accept else 'completed_max_iterations',
                    'research_report': research_report,
                    'all_reviews': all_reviews,
                    'iterations': iteration + 1,
                    'final_scores': scores
                }

            iteration += 1

        # Should not reach here, but return the last state
        return {
            'status': 'completed_max_iterations',
            'research_report': research_report,
            'all_reviews': all_reviews,
            'iterations': iteration,
            'final_scores': scores
        }

    async def _conduct_research(self, query: str) -> str:
        """
        Execute initial research using the researcher agent.

        Args:
            query (str): Research query

        Returns:
            str: Research report
        """
        try:
            report = await asyncio.to_thread(self.researcher.run, query)
            return report
        except Exception as e:
            return f"Error conducting research: {str(e)}"

    async def _revise_research(self, query: str, original_report: str, feedback: Dict) -> str:
        """
        Execute research revision with council feedback.

        Args:
            query (str): Original research query
            original_report (str): The original research report
            feedback (dict): Synthesized feedback from council

        Returns:
            str: Revised research report
        """
        revision_prompt = self._create_revision_prompt(query, original_report, feedback)

        try:
            revised_report = await asyncio.to_thread(self.researcher.run, revision_prompt)
            return revised_report
        except Exception as e:
            return f"Error revising research: {str(e)}"

    async def _parallel_council_review(self, research_report: str) -> List[Dict]:
        """
        Execute parallel council reviews.

        Args:
            research_report (str): The research report to review

        Returns:
            list: List of review dictionaries with scores and feedback
        """
        # Execute all 3 reviews in parallel
        review_tasks = [
            asyncio.to_thread(agent.run, research_report)
            for agent in self.council
        ]

        try:
            review_texts = await asyncio.gather(*review_tasks)

            # Parse reviews to extract scores and key information
            reviews = []
            reviewer_names = [
                "Dr. Sarah Chen (Methodology)",
                "Prof. James Rodriguez (Comprehensiveness)",
                "Dr. Emily Thompson (Clarity)"
            ]

            for i, review_text in enumerate(review_texts):
                score = self._extract_score(review_text)
                recommendation = self._extract_recommendation(review_text)

                reviews.append({
                    'reviewer': reviewer_names[i],
                    'review_text': review_text,
                    'score': score,
                    'recommendation': recommendation
                })

            return reviews

        except Exception as e:
            # Return default reviews on error
            return [
                {
                    'reviewer': f'Reviewer {i+1}',
                    'review_text': f'Error: {str(e)}',
                    'score': 0.0,
                    'recommendation': 'ERROR'
                }
                for i in range(3)
            ]

    def _extract_score(self, review_text: str) -> float:
        """
        Extract the overall score from a review.

        Args:
            review_text (str): The full review text

        Returns:
            float: Overall score (0.0 if not found)
        """
        # Look for "Overall Score: X.X / 5" or "Overall Score: X/5"
        patterns = [
            r'Overall Score:\s*(\d+\.?\d*)\s*/\s*5',
            r'Overall Score:\s*(\d+\.?\d*)',
            r'Score:\s*(\d+\.?\d*)\s*/\s*5'
        ]

        for pattern in patterns:
            match = re.search(pattern, review_text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    return min(score, 5.0)  # Cap at 5.0
                except ValueError:
                    continue

        # If no score found, return 0.0
        return 0.0

    def _extract_recommendation(self, review_text: str) -> str:
        """
        Extract the recommendation (ACCEPT/REVISE) from a review.

        Args:
            review_text (str): The full review text

        Returns:
            str: 'ACCEPT', 'REVISE', or 'UNKNOWN'
        """
        if re.search(r'Recommendation:\s*ACCEPT', review_text, re.IGNORECASE):
            return 'ACCEPT'
        elif re.search(r'Recommendation:\s*REVISE', review_text, re.IGNORECASE):
            return 'REVISE'
        else:
            return 'UNKNOWN'

    def _evaluate_acceptance(self, scores: List[float]) -> bool:
        """
        Determine if research is accepted based on council scores.

        Conditional retry logic:
        - If 2 or more reviewers scored >= 3: ACCEPT
        - If all 3 reviewers scored < 3: REVISE (retry once)

        Args:
            scores (list): List of 3 scores from council members

        Returns:
            bool: True if accepted, False if revision needed
        """
        passing_scores = sum(1 for score in scores if score >= 3.0)
        return passing_scores >= 2

    def _synthesize_feedback(self, review_round: Dict) -> Dict:
        """
        Synthesize feedback from all council members into actionable guidance.

        Args:
            review_round (dict): Dictionary containing all reviews from one round

        Returns:
            dict: Synthesized feedback with priorities
        """
        reviews = review_round['reviews']
        scores = review_round['scores']

        # Collect all feedback points
        methodology_feedback = []
        comprehensiveness_feedback = []
        clarity_feedback = []
        priorities = []

        for review in reviews:
            reviewer_name = review['reviewer']
            review_text = review['review_text']
            score = review['score']

            # Extract "Areas for Improvement" section
            improvements = self._extract_section(review_text, "Areas for Improvement")

            if "Methodology" in reviewer_name:
                methodology_feedback.append(improvements)
                if score < 3:
                    priorities.append(f"CRITICAL: Address methodology issues")
            elif "Comprehensiveness" in reviewer_name:
                comprehensiveness_feedback.append(improvements)
                if score < 3:
                    priorities.append(f"CRITICAL: Expand topic coverage")
            elif "Clarity" in reviewer_name:
                clarity_feedback.append(improvements)
                if score < 3:
                    priorities.append(f"CRITICAL: Improve clarity and organization")

        return {
            'scores': scores,
            'methodology_feedback': methodology_feedback,
            'comprehensiveness_feedback': comprehensiveness_feedback,
            'clarity_feedback': clarity_feedback,
            'priorities': priorities
        }

    def _extract_section(self, text: str, section_name: str) -> str:
        """
        Extract a specific section from review text.

        Args:
            text (str): Full review text
            section_name (str): Section header to extract

        Returns:
            str: Extracted section content
        """
        pattern = rf'##?\s*{re.escape(section_name)}:?\s*(.*?)(?=##|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _create_revision_prompt(self, query: str, original_report: str, feedback: Dict) -> str:
        """
        Create a revision prompt for the researcher based on council feedback.

        Args:
            query (str): Original research query
            original_report (str): Original research report
            feedback (dict): Synthesized feedback

        Returns:
            str: Revision prompt for researcher
        """
        priorities_text = "\n".join(f"- {p}" for p in feedback['priorities'])

        methodology_text = "\n".join(feedback['methodology_feedback']) if feedback['methodology_feedback'] else "None"
        comprehensiveness_text = "\n".join(feedback['comprehensiveness_feedback']) if feedback['comprehensiveness_feedback'] else "None"
        clarity_text = "\n".join(feedback['clarity_feedback']) if feedback['clarity_feedback'] else "None"

        revision_prompt = f"""
REVISION REQUEST - Your research has been reviewed by the council and needs improvement.

Original Research Query: {query}

Council Review Scores: {feedback['scores']}

TOP PRIORITIES FOR REVISION:
{priorities_text}

DETAILED FEEDBACK FROM COUNCIL:

METHODOLOGY FEEDBACK (Dr. Sarah Chen):
{methodology_text}

COMPREHENSIVENESS FEEDBACK (Prof. James Rodriguez):
{comprehensiveness_text}

CLARITY & COMMUNICATION FEEDBACK (Dr. Emily Thompson):
{clarity_text}

INSTRUCTIONS FOR REVISION:
1. Address ALL critical priority items listed above
2. Use additional research tools to gather more sources if needed
3. Improve source quality by prioritizing authoritative sources (.edu, .gov, peer-reviewed)
4. Expand coverage of gaps identified by the comprehensiveness reviewer
5. Improve clarity, organization, and structure as noted by the clarity reviewer
6. Maintain the strengths of your original research while addressing weaknesses

Your revised research will be reviewed again by the same council. Aim to score 3.0 or higher with at least 2 reviewers.

Conduct your revision now, using all available research tools as needed.
"""

        return revision_prompt
