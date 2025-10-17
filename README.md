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

✍️ Contributing

We welcome improvements—UX polish, retrieval quality, prompt design, tests, and docs.

Quick dev

backend
uvicorn app.main:app --reload --port 8000

frontend
npm run dev

Open a focused PR with a brief before/after note or GIF. Be kind and constructive in reviews.

🌟 Spread the word

⭐ Star the repo

Share a short demo GIF

Post a thread and tag #ThesisGraph

Your support helps prioritize citations, compose-from-graph, and save/load projects.

⚠️ License

Released under the MIT License.

Your support helps us prioritize features like citations, compose-from-graph, and save/load projects.

⚠️ License

This project is open-source under the MIT License. (Consider attributing screenshots/demos if you reuse visuals.)

