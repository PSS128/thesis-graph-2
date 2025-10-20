# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Register all routers you already have:
# extract, edges, ingest, retrieve, projects exist in your project
from .routers import extract, edges, ingest, retrieve, projects, compose, debug
from .routers import node as node_router
from .routers import edge as edge_router
from .routers import graph as graph_router

app = FastAPI(title="Thesis Graph API")

# --- CORS for local Next.js frontend ---
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # Allow backend to talk to itself
        "http://127.0.0.1:8000",  # Allow backend to talk to itself
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-LLM-Used","X-Model"],  # so the browser can read them
)


# --- Routers ---
app.include_router(extract.router)
app.include_router(edges.router)
app.include_router(ingest.router)
app.include_router(retrieve.router)
app.include_router(projects.router)
app.include_router(compose.router)  # <-- new/ensured
app.include_router(debug.router)    # <-- new
app.include_router(node_router.router)
app.include_router(edge_router.router)
app.include_router(graph_router.router)

@app.get("/")
def read_root():
    return {"message": "Backend running"}
