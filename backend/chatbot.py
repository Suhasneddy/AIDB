"""
AI Chatbot Module — LLM-powered assistant for AIDB
Supports Groq (gsk_ keys) and xAI/Grok (xai- keys) automatically.
Helps users with device compatibility, tool setup, and AI tool queries.
"""

import os
import uuid
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# ─── System Prompt ───────────────────────────────────────────────
SYSTEM_PROMPT = """You are AIDB Assistant, an AI-powered helper for the AIDB platform — a directory that ranks and catalogs open-source AI tools from GitHub and Hugging Face.

Your job is to help users with:
1. **Device Compatibility** — Tell users what hardware (GPU, RAM, CPU) is needed to run a specific AI tool. Use your knowledge of common AI frameworks and models. Be specific about VRAM, system RAM, and whether a tool works on CPU-only machines.
2. **Download & Setup** — Guide users step-by-step on how to clone, install dependencies, and run AI tools. Include `git clone`, `pip install`, `conda` instructions, and any environment variables needed.
3. **Tool Information** — When given context about a tool from our database, use that data (stars, forks, language, description) to give accurate answers about the tool's popularity, activity, and capabilities.
4. **Comparisons** — Compare AI tools based on their features, requirements, popularity, and use cases.

Guidelines:
- Be concise but thorough. Use bullet points and code blocks for clarity.
- If you're given TOOL CONTEXT data, always reference it in your answer.
- If you don't know the exact system requirements for a tool, give reasonable estimates based on the tool category (e.g., LLMs need more VRAM than NLP classifiers).
- Always suggest the official repository URL when available.
- Format responses in markdown for readability.
- Keep responses under 500 words unless the user asks for detailed instructions.
- If a user asks something unrelated to AI tools, politely redirect them.
"""


class ChatBot:
    """LLM-powered chatbot with session management and tool context injection.
    Supports both Groq (gsk_ keys) and xAI/Grok (xai- keys) automatically."""

    def __init__(self):
        self.client = None
        self.provider = None  # 'groq' or 'xai'
        self.model = None

        try:
            api_key = os.getenv("GROQ_API_KEY")

            if not api_key:
                print("⚠️  GROQ_API_KEY not found — chatbot will return fallback responses")
            elif api_key.startswith("xai-"):
                # xAI/Grok API — uses OpenAI-compatible endpoint
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
                    self.provider = "xai"
                    self.model = "grok-3-mini-fast"
                    print("✅ Chatbot initialized with xAI/Grok API")
                except Exception as e:
                    print(f"⚠️  Failed to initialize xAI client: {e}")
            else:
                # Groq API
                try:
                    from groq import Groq
                    self.client = Groq(api_key=api_key)
                    self.provider = "groq"
                    self.model = "llama-3.3-70b-versatile"
                    print("✅ Chatbot initialized with Groq API")
                except Exception as e:
                    print(f"⚠️  Failed to initialize Groq client: {e}")
        except Exception as e:
            print(f"⚠️  Chatbot init error (will use fallback): {e}")

        # In-memory session store: session_id -> list of messages
        self.sessions: Dict[str, List[Dict]] = {}
        self.session_timestamps: Dict[str, float] = {}
        self.max_history = 10  # Keep last 10 messages per session

    def _get_session(self, session_id: str) -> List[Dict]:
        """Get or create a chat session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.session_timestamps[session_id] = time.time()
        return self.sessions[session_id]

    def _cleanup_old_sessions(self):
        """Remove sessions older than 1 hour."""
        cutoff = time.time() - 3600
        expired = [sid for sid, ts in self.session_timestamps.items() if ts < cutoff]
        for sid in expired:
            self.sessions.pop(sid, None)
            self.session_timestamps.pop(sid, None)

    def _build_tool_context(self, query: str, tools_data: Optional[List[Dict]] = None) -> str:
        """Search cached tools and build context string for the LLM."""
        if not tools_data:
            return ""

        query_lower = query.lower()
        
        # Find relevant tools by matching query against name, description, topics
        matching_tools = []
        for tool in tools_data:
            name = str(tool.get("name", "")).lower()
            desc = str(tool.get("description") or "").lower()
            full_name = str(tool.get("full_name", "")).lower()
            topics = " ".join([str(t) for t in (tool.get("topics") or tool.get("tags") or [])])
            
            search_text = f"{name} {desc} {full_name} {topics}"
            
            # Check if any word in the query matches
            query_words = [w for w in query_lower.split() if len(w) > 2]
            if any(word in search_text for word in query_words):
                matching_tools.append(tool)

        if not matching_tools:
            return ""

        # Build context string from top 5 matches
        context_parts = ["\n--- TOOL CONTEXT FROM AIDB DATABASE ---"]
        for tool in matching_tools[:5]:
            stars = tool.get("stars", 0)
            forks = tool.get("forks", 0)
            lang = tool.get("language", "Unknown")
            url = tool.get("url") or tool.get("source_url", "")
            desc = tool.get("description", "No description")
            score = tool.get("BoostedScore", 0)
            name = tool.get("full_name") or tool.get("name", "Unknown")
            source = tool.get("source", "github")

            context_parts.append(f"""
Tool: {name}
Source: {source}
Description: {desc}
Language: {lang}
Stars: {stars:,} | Forks: {forks:,}
AIDB Score: {(score * 10):.1f}/10
URL: {url}
""")

        context_parts.append("--- END TOOL CONTEXT ---\n")
        return "\n".join(context_parts)

    def chat(self, message: str, session_id: str, tools_data: Optional[List[Dict]] = None) -> str:
        """
        Process a chat message and return the AI response.
        
        Args:
            message: User's message
            session_id: Unique session identifier
            tools_data: Cached tools data from the main app for context injection
        
        Returns:
            AI-generated response string
        """
        # Cleanup old sessions periodically
        self._cleanup_old_sessions()

        # If no Groq client, return a helpful fallback
        if not self.client:
            return self._fallback_response(message)

        # Get session history
        history = self._get_session(session_id)

        # Build tool context
        tool_context = self._build_tool_context(message, tools_data)

        # Construct the user message with context
        user_message = message
        if tool_context:
            user_message = f"{message}\n\n{tool_context}"

        # Add user message to history
        history.append({"role": "user", "content": user_message})

        # Trim history to max length
        if len(history) > self.max_history:
            history = history[-self.max_history:]
            self.sessions[session_id] = history

        # Build messages for API call
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=0.9,
            )

            reply = response.choices[0].message.content

            # Add assistant response to history
            history.append({"role": "assistant", "content": reply})

            return reply

        except Exception as e:
            print(f"❌ Groq API error: {e}")
            return f"I'm having trouble connecting to my AI backend right now. Please try again in a moment.\n\n*Error: {str(e)}*"

    def _fallback_response(self, message: str) -> str:
        """Provide a helpful response when the Groq API key is not configured."""
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ["install", "setup", "download", "clone"]):
            return (
                "## General Setup Instructions\n\n"
                "For most AI tools on AIDB, the setup process is:\n\n"
                "```bash\n"
                "# 1. Clone the repository\n"
                "git clone <repo-url>\n"
                "cd <repo-name>\n\n"
                "# 2. Create a virtual environment\n"
                "python -m venv venv\n"
                "source venv/bin/activate  # Linux/Mac\n"
                "venv\\Scripts\\activate     # Windows\n\n"
                "# 3. Install dependencies\n"
                "pip install -r requirements.txt\n"
                "```\n\n"
                "💡 *For specific tool instructions, please set up the GROQ_API_KEY in the backend.*"
            )

        if any(word in msg_lower for word in ["gpu", "ram", "cpu", "compatible", "requirements", "run"]):
            return (
                "## General Device Compatibility\n\n"
                "| Tool Type | Min RAM | GPU | Notes |\n"
                "|-----------|---------|-----|-------|\n"
                "| Small NLP models | 4 GB | Not required | CPU is fine |\n"
                "| Image classifiers | 8 GB | Optional | GPU speeds up inference |\n"
                "| Stable Diffusion | 16 GB | 6+ GB VRAM | NVIDIA recommended |\n"
                "| Large LLMs (7B) | 16 GB | 8+ GB VRAM | Or use quantized versions |\n"
                "| Large LLMs (70B) | 64 GB | 24+ GB VRAM | Multiple GPUs recommended |\n\n"
                "💡 *For specific tool requirements, please set up the GROQ_API_KEY in the backend.*"
            )

        return (
            "👋 Hi! I'm the AIDB Assistant. I can help you with:\n\n"
            "- **Device compatibility** — What hardware you need for AI tools\n"
            "- **Setup instructions** — How to install and run tools\n"
            "- **Tool comparisons** — Comparing AI tools side by side\n"
            "- **General questions** — About any AI tool on AIDB\n\n"
            "💡 *For full AI-powered responses, set up the GROQ_API_KEY in the backend `.env` file.*"
        )

    def get_suggestions(self) -> List[str]:
        """Return suggested starter questions."""
        return [
            "What GPU do I need to run Stable Diffusion?",
            "How do I install and set up LangChain?",
            "Can I run LLaMA on a laptop with 8GB RAM?",
            "What are the top trending AI tools right now?",
            "Compare PyTorch vs TensorFlow for beginners",
            "How to set up Whisper for speech recognition?",
        ]


# Global chatbot instance
chatbot = ChatBot()
