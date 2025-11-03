Thesis-Graph

LLM-assisted canvas for building, visualizing, and refining arguments.
Paste sources → extract claims → suggest links → grow an interactive reasoning graph.

Next.js FastAPI React Flow License PRs welcome

🧐 Project philosophy
Thesis-Graph is not a chatbot. It’s a visual workspace that helps you turn text into claims (nodes), propose links (edges), and see your reasoning evolve in real time. Start with an optional thesis, drop in articles or notes, and curate an argument map you can manipulate, interrogate, and (soon) convert into prose.

👨‍💻 Tech stack

Frontend: Next.js (TypeScript) + React Flow for interactive graphs
Backend: FastAPI (Python) with CORS (Uvicorn for local dev)
MVP endpoints: GET / (health) · POST /extract/nodes (claims + optional THESIS) · POST /edges/suggest (naive links)
Planned: SQLModel/SQLite for projects, FAISS + sentence-transformers for retrieval/citations, and LLM-backed extraction/rationales (OpenAI or local Llama via HF)
Frontend reads the API base from frontend/.env.local → NEXT_PUBLIC_API_URL=http://localhost:8000


  Running Tests

  cd backend
  pytest
  pytest -v tests/test_citations.py  # Specific test file

  Database Migrations

  cd backend
  python migrations/add_llm_metrics.py  # Run migrations

  ---
  📖 Documentation

  - docs/user-guide.md - How to use Thesis-Graph (TODO)
  - docs/api.md - Full endpoint documentation (TODO)
  - backend/app/prompts/README.md - How prompts work
  - CONTRIBUTING.md - Development workflow (TODO)

  ---
  🗺️ Roadmap

  Current Features ✅

  - Node extraction (THESIS, CLAIM, EVIDENCE, VARIABLE)
  - Edge suggestions with causal rationale
  - Essay composition from graph
  - Interactive graph canvas
  - User authentication
  - Project persistence (SQLite)
  - LLM metrics & monitoring
  - Prompt versioning system
  - Intelligent caching

  Planned Features 🚧

  - Citation linking - Map claims back to source documents
  - FAISS retrieval - Semantic search for evidence
  - Graph critique - Detect cycles, colliders, confounding paths
  - Export formats - LaTeX, Markdown, PDF
  - Collaborative editing - Multi-user projects
  - Mobile-friendly UI - Responsive canvas
  - Self-hosted LLMs - Llama via Hugging Face
  - Study design suggestions - RCT, IV, DiD recommendations

Open a focused PR with a brief before/after note or GIF. Be kind and constructive in reviews.

Your support helps prioritize citations, compose-from-graph, and save/load projects.

⚠️ License

Released under the MIT License.

Your support helps us prioritize features like citations, compose-from-graph, and save/load projects.

⚠️ License

This project is open-source under the MIT License. (Consider attributing screenshots/demos if you reuse visuals.)

