# Research SmoLAgent with Council Review

A sophisticated multi-agent research system that combines a senior research agent with a council of 3 expert reviewers to produce high-quality, peer-reviewed research reports.

## Overview

This system implements a novel quality assurance approach to AI research:

1. **Researcher Agent** conducts comprehensive research using 5 specialized tools
2. **Council of 3 Reviewers** independently evaluate the research on different criteria
3. **Conditional Retry Logic** ensures quality through iterative improvement
4. **Chainlit UI** provides real-time visibility into agent thinking and handovers

## Screenshots

### Research Phase
![Research Phase](images/Screenshot%202026-01-18%2011.26.34.png)

### Council Review
![Council Review](images/Screenshot%202026-01-18%2011.26.58.png)

### Review Results
![Review Results](images/Screenshot%202026-01-18%2011.27.10.png)

### Final Report
![Final Report](images/Screenshot%202026-01-18%2011.27.24.png)

## Features

### Research Tools

The researcher agent has access to 5 powerful research tools:

- **`web_search`** - Search the web using DuckDuckGo with caching
- **`scrape_webpage`** - Extract detailed content from web pages
- **`analyze_document`** - Analyze PDFs, papers, and documents
- **`synthesize_data`** - Aggregate information from multiple sources
- **`track_citations`** - Extract and manage citations with credibility scoring

### Council Review System

Three independent expert reviewers evaluate research on different dimensions:

- **Dr. Sarah Chen (Methodology)** - Evaluates source quality, research depth, evidence-based reasoning, methodological soundness, and limitations (uses Anthropic Claude 3.7 Sonnet)
- **Prof. James Rodriguez (Comprehensiveness)** - Assesses topic coverage, perspective diversity, context, currency, and practical applicability (uses Google Gemini 2.0 Flash Thinking)
- **Dr. Emily Thompson (Clarity)** - Reviews structural organization, writing clarity, synthesis quality, audience appropriateness, and visual organization (uses OpenAI GPT-4.1 Turbo)

Each reviewer scores on a 1-5 scale across 5 criteria and provides detailed feedback.

### Quality Assurance

**Acceptance Criteria**: Research is accepted if 2 or more reviewers score it 3.0+ out of 5.0

**Revision Process**: If all 3 reviewers score below 3.0, the researcher receives synthesized feedback and conducts one revision

### Visualization

Chainlit provides real-time visibility into:

- Researcher's thinking process and tool usage
- Individual council member reviews
- Agent handovers between researcher and council
- Revision flow with feedback integration
- Iteration tracking (1/2, 2/2)

## Installation

### Prerequisites

- Python 3.8+
- OpenRouter API key (get one at https://openrouter.ai/keys)

### Setup

1. **Navigate to the directory**:
   ```bash
   cd researcher-smolagent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.template .env
   ```

4. **Add your OpenRouter API key** to `.env`:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

## Usage

### Running the Application

Start the Chainlit interface:

```bash
chainlit run chainlit_app.py
```

The application will open in your browser at http://localhost:8000

### Example Research Queries

Try these example queries:

- "Research the current state of quantum computing and its potential impact on cryptography"
- "Investigate the effects of climate change on global agriculture"
- "Analyze the impact of AI on healthcare diagnostics"
- "Research the causes and solutions for antibiotic resistance"
- "Examine the role of renewable energy in reducing carbon emissions"

### Research Workflow

1. **Enter your research query** in the chat interface

2. **Watch the research phase**: The researcher agent will:
   - Search the web for relevant sources
   - Scrape detailed content from promising URLs
   - Analyze documents if applicable
   - Synthesize information across sources
   - Track citations and source credibility

3. **View council reviews**: Each reviewer independently assesses the research:
   - Dr. Sarah Chen evaluates methodology
   - Prof. James Rodriguez evaluates comprehensiveness
   - Dr. Emily Thompson evaluates clarity

4. **See the decision**:
   - ✅ **Accepted**: 2+ reviewers scored 3.0 or higher
   - 🔄 **Revision**: All reviewers scored below 3.0 → researcher revises with feedback
   - ⏭️ **Max Iterations**: After 2 iterations, final version is presented

5. **Read the final research report** with all council reviews

## Architecture

### Directory Structure

```
researcher-smolagent/
├── agents/
│   ├── researcher.py              # Researcher agent creation
│   └── council.py                 # Council agents creation
├── orchestration/
│   └── workflow.py                # Multi-agent orchestration logic
├── prompts/
│   ├── researcher_prompts.py      # Researcher system prompts
│   └── council_prompts.py         # Council reviewer prompts
├── data/
│   └── research_cache/            # Cached web searches and scraped pages
├── config.py                      # Model configurations
├── tools.py                       # Research tools
├── chainlit_app.py                # Chainlit UI application
├── requirements.txt               # Python dependencies
├── .env.template                  # Environment template
└── README.md                      # This file
```

### Models Used

Different OpenRouter models are used for each agent to provide diversity in reasoning:

- **Researcher**: `google/gemini-2.0-flash-thinking-exp-01-21` - Strong reasoning, cost-effective
- **Dr. Sarah Chen**: `anthropic/claude-3.7-sonnet` - Excellent analytical assessment
- **Prof. James Rodriguez**: `google/gemini-2.0-flash-thinking-exp-01-21` - Good holistic coverage
- **Dr. Emily Thompson**: `openai/gpt-4.1-turbo` - Strong communication assessment

### Workflow Logic

```
1. Initial Research
   ↓
2. Council Review (Parallel)
   ├─ Dr. Sarah Chen (Methodology)
   ├─ Prof. James Rodriguez (Comprehensiveness)
   └─ Dr. Emily Thompson (Clarity)
   ↓
3. Decision
   ├─ If 2+ score >= 3.0: ACCEPT ✅
   └─ If all score < 3.0: REVISE 🔄
      ↓
4. Revision (if needed)
   ├─ Synthesize feedback
   ├─ Researcher revises
   └─ Return to step 2 (max 2 total iterations)
   ↓
5. Final Output
   └─ Research report + all reviews
```

## Customization

### Adjusting Models

Edit `config.py` to change which models are used for each agent. Any OpenRouter-supported model can be used.

### Modifying Prompts

- **Researcher behavior**: Edit `prompts/researcher_prompts.py`
- **Council criteria**: Edit `prompts/council_prompts.py`

### Changing Acceptance Criteria

Edit `orchestration/workflow.py`, method `_evaluate_acceptance()` to adjust the conditional retry logic.

### Adding More Tools

1. Define new tool in `tools.py` using `@tool` decorator
2. Add tool to researcher agent in `agents/researcher.py`
3. Update researcher prompt to explain when to use the new tool

## Caching

The system caches:
- **Web searches**: 24 hours
- **Scraped webpages**: 7 days

Cached data is stored in `data/research_cache/` as JSON files.

To clear cache:
```bash
rm -rf data/research_cache/*
```

## Troubleshooting

### "OPENROUTER_API_KEY not found"
- Make sure you've created a `.env` file from `.env.template`
- Add your OpenRouter API key to the `.env` file
- The key should start with `sk-or-...`

### Models not working
- Check OpenRouter service status
- Verify your API key has credits
- Try a different model in `config.py`

### Import errors
- Make sure you're in the `researcher-smolagent/` directory
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version is 3.8+

### Slow performance
- The system uses 4 different models (1 researcher + 3 reviewers)
- First iteration is slower due to web searches and scraping
- Subsequent searches use cached results

## Development

### Testing Individual Components

Test a single tool:
```python
from tools import web_search
result = web_search("quantum computing", max_results=5)
print(result)
```

Test the researcher agent:
```python
from agents.researcher import create_researcher_agent
researcher = create_researcher_agent()
report = researcher.run("Research topic here")
print(report)
```

Test a council member:
```python
from agents.council import create_council_agents
council = create_council_agents()
review = council[0].run("Sample research report here")
print(review)
```

## License

Part of the smolagent-collection repository.

## Acknowledgments

- Built with [smolagents](https://github.com/huggingface/smolagents) framework by Hugging Face
- UI powered by [Chainlit](https://github.com/Chainlit/chainlit)
- Models provided by [OpenRouter](https://openrouter.ai/)
