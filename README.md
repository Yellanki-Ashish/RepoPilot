# 🚀 RepoPilot

### Agentic AI System for Automated GitHub Repository Understanding and Developer Onboarding

RepoPilot is an **Agentic AI-powered developer assistant** that automatically analyzes GitHub repositories and helps developers understand unfamiliar codebases.

Instead of manually exploring hundreds of files, developers can provide a GitHub repository URL and RepoPilot analyzes the repository structure, programming languages, dependencies, architecture, code complexity, issues, and important files.

It also provides an **AI-powered repository assistant** that uses **RAG (Retrieval-Augmented Generation)** to answer questions using relevant source-code context.

The project runs locally using **Ollama and Llama 3.1**, so no paid OpenAI or Anthropic API key is required.

---

## 🎯 Problem Statement

Understanding an unfamiliar GitHub repository can take significant time, especially when the project contains many files, dependencies, and modules.

A developer joining an existing project may need to answer questions such as:

* What is the architecture of this project?
* Which files are most important?
* How are the modules connected?
* Where is authentication implemented?
* Which files have the most dependencies?
* How difficult is a particular issue?
* What should I learn first before contributing?
* Where should I make changes to implement a new feature?

RepoPilot automates much of this initial repository exploration.

---

# ✨ Features

### 🔍 GitHub Repository Analysis

Enter a public GitHub repository URL and RepoPilot automatically retrieves and analyzes the repository.

### 📊 Repository Overview

Provides information such as:

* Repository name
* Owner
* Number of files
* Programming languages
* Repository structure
* Important source files

### 🧠 Code Analysis

Analyzes source code to identify:

* Classes
* Functions
* Imports
* Symbols
* Code structure
* Complexity indicators

Python files are analyzed using Python's AST module.

JavaScript, TypeScript, JSX, TSX, and Java files use pattern-based analysis.

### 🕸️ Dependency Graph

Builds a graph representing relationships between files and modules.

This helps developers understand:

```text
Which files depend on which files?
```

### 🏗️ Architecture Analysis

Identifies architectural layers and relationships based on evidence found in the repository.

### 📈 Complexity Analysis

Provides heuristic complexity information to help identify potentially complicated files.

### 🔎 Semantic Code Search

Repository code is converted into embeddings and stored in ChromaDB.

Developers can search for code based on meaning rather than only exact keywords.

### 🤖 RAG-Based AI Assistant

The AI assistant uses Retrieval-Augmented Generation:

```text
User Question
      ↓
Query Embedding
      ↓
ChromaDB
      ↓
Relevant Code Chunks
      ↓
AI Agents
      ↓
Llama 3.1
      ↓
Repository-Specific Answer
```

### 👥 Multi-Agent Architecture

RepoPilot uses specialized agents for different tasks:

* Repository Agent
* Architecture Agent
* Dependency Agent
* Code Agent
* RAG Agent
* Issue Agent
* Onboarding Agent
* Developer Agent

An orchestrator determines which agents are relevant to a user's question.

### 🐛 GitHub Issue Analysis

Analyzes repository issues and provides a transparent difficulty estimate.

### 🗺️ Developer Onboarding Roadmap

Generates a structured onboarding roadmap to help a new developer understand the repository and start contributing.

### 💻 Local AI

Uses:

* Ollama
* Llama 3.1

The LLM runs locally instead of requiring a paid cloud AI API.

---

# 🏗️ System Architecture

```text
                    USER
                      |
                      ↓
              React + Vite
                  Frontend
                      |
                      ↓
               FastAPI Backend
                      |
          ┌───────────┼───────────┐
          ↓           ↓           ↓
      GitHub API   Analysis      RAG
          |           |           |
          ↓           ↓           ↓
     Repository    AST / Regex   Chunking
       Scanner     Analysis        |
                      |            ↓
                      |       Embeddings
                      |            |
                      |            ↓
                      |        ChromaDB
                      |            |
                      └──────┬─────┘
                             ↓
                       Agent Orchestrator
                             |
          ┌──────────────────┼──────────────────┐
          ↓                  ↓                  ↓
    Repository Agent   Architecture Agent   Code Agent
          ↓                  ↓                  ↓
    Dependency Agent     RAG Agent       Issue Agent
          ↓                  ↓                  ↓
    Onboarding Agent    Developer Agent
                             |
                             ↓
                         Ollama
                             |
                             ↓
                        Llama 3.1
                             |
                             ↓
                     Generated Answer
                             |
                             ↓
                       React Frontend
```

---

# 🔄 Complete Project Workflow

```text
1. User enters GitHub repository URL
                  ↓
2. FastAPI receives the request
                  ↓
3. GitHub API retrieves repository information
                  ↓
4. Repository scanner collects source files
                  ↓
5. Binary and oversized files are filtered
                  ↓
6. Source code is analyzed
                  ↓
7. Dependencies are identified
                  ↓
8. Dependency graph is generated
                  ↓
9. Architecture and complexity are analyzed
                  ↓
10. Source code is divided into chunks
                  ↓
11. Chunks are converted into embeddings
                  ↓
12. Embeddings are stored in ChromaDB
                  ↓
13. User asks a question
                  ↓
14. Question is converted into an embedding
                  ↓
15. ChromaDB retrieves relevant code chunks
                  ↓
16. Relevant context is passed to the AI agents
                  ↓
17. Developer Agent sends context to Llama
                  ↓
18. Ollama generates the response
                  ↓
19. FastAPI returns the response
                  ↓
20. React displays the answer
```

---

# 🛠️ Technology Stack

| Technology            | Purpose                             |
| --------------------- | ----------------------------------- |
| Python                | Backend and AI/RAG development      |
| FastAPI               | REST API backend                    |
| Pydantic              | Request and response validation     |
| Uvicorn               | FastAPI application server          |
| React                 | Frontend UI                         |
| Vite                  | Frontend development and build tool |
| Axios                 | Frontend API communication          |
| Ollama                | Local LLM execution                 |
| Llama 3.1             | AI response generation              |
| Sentence Transformers | Text/code embeddings                |
| all-MiniLM-L6-v2      | Embedding model                     |
| ChromaDB              | Vector database                     |
| NetworkX              | Dependency graph generation         |
| Python AST            | Python code structure analysis      |
| GitHub REST API       | Repository data retrieval           |
| Docker                | Containerization                    |
| Pytest                | Backend testing                     |
| Git/GitHub            | Version control                     |

---

# 📁 Project Structure

```text
RepoPilot/
│
├── backend/
│   │
│   ├── app/
│   │   ├── agents/
│   │   │   ├── architecture_agent.py
│   │   │   ├── code_agent.py
│   │   │   ├── dependency_agent.py
│   │   │   ├── developer_agent.py
│   │   │   ├── issue_agent.py
│   │   │   ├── onboarding_agent.py
│   │   │   ├── rag_agent.py
│   │   │   ├── repository_agent.py
│   │   │   └── orchestrator.py
│   │   │
│   │   ├── analysis/
│   │   │   ├── architecture.py
│   │   │   ├── code_analyzer.py
│   │   │   ├── complexity.py
│   │   │   └── dependency_graph.py
│   │   │
│   │   ├── api/
│   │   │   ├── assistant_routes.py
│   │   │   ├── repository_routes.py
│   │   │   ├── onboarding_routes.py
│   │   │   └── issue_routes.py
│   │   │
│   │   ├── ingestion/
│   │   │   ├── github_client.py
│   │   │   └── scanner.py
│   │   │
│   │   ├── llm/
│   │   │   └── ollama_client.py
│   │   │
│   │   ├── rag/
│   │   │   ├── chunker.py
│   │   │   ├── embeddings.py
│   │   │   ├── retriever.py
│   │   │   ├── vector_store.py
│   │   │   └── context_builder.py
│   │   │
│   │   ├── schemas/
│   │   ├── main.py
│   │   ├── pipeline.py
│   │   ├── config.py
│   │   └── storage.py
│   │
│   ├── tests/
│   ├── data/
│   │   ├── chroma/
│   │   └── repos/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── styles/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   └── Dockerfile
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

# 💻 Prerequisites

Before running RepoPilot, install:

### Python

Python:

```text
3.10 - 3.12
```

Recommended:

```text
Python 3.11
```

Check:

```powershell
python --version
```

or:

```powershell
py -3.11 --version
```

### Node.js

Node.js 18 or newer is required.

Recommended:

```text
Node.js 20+
```

Check:

```powershell
node --version
npm --version
```

### Ollama

Install Ollama from:

https://ollama.com/download

Check:

```powershell
ollama --version
```

### Git

Check:

```powershell
git --version
```

---

# 🚀 Local Installation

## Step 1: Clone the repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd RepoPilot
```

---

# Step 2: Install and start Ollama

Download the required Llama model:

```powershell
ollama pull llama3.1:8b
```

Start Ollama:

```powershell
ollama serve
```

If Ollama is already running in the Windows system tray, you can skip `ollama serve`.

Verify:

```powershell
ollama list
```

You should see:

```text
llama3.1:8b
```

---

# Step 3: Setup Backend

Open a new terminal.

```powershell
cd RepoPilot\backend
```

Create a Python virtual environment:

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# Step 4: Configure Backend Environment

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

The default configuration is:

```env
GITHUB_TOKEN=

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT=300
OLLAMA_NUM_CTX=8192

EMBEDDING_MODEL=all-MiniLM-L6-v2

CHROMA_DIR=./data/chroma
REPOS_DIR=./data/repos

MAX_FILE_SIZE_KB=500
MAX_FILES_TO_ANALYZE=100

TOP_K_RESULTS=5
MAX_CONTEXT_CHARACTERS=12000

FRONTEND_URL=http://localhost:5173
```

### GitHub Token

A GitHub token is optional.

Public repositories work without a token, but unauthenticated GitHub API access has a lower rate limit.

If you use a token:

```env
GITHUB_TOKEN=your_github_token
```

Never commit your real token to GitHub.

---

# Step 5: Start Backend

Make sure the virtual environment is active:

```text
(.venv)
```

Run:

```powershell
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Swagger API documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

---

# Step 6: Setup Frontend

Open another terminal.

```powershell
cd RepoPilot\frontend
```

Install dependencies:

```powershell
npm install
```

Create frontend environment file:

```powershell
Copy-Item .env.example .env
```

The `.env` file should contain:

```env
VITE_API_URL=http://localhost:8000
```

---

# Step 7: Start Frontend

Run:

```powershell
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

Open it in your browser.

---

# 🎯 Running the Complete Application

You need three services running.

### Terminal 1: Ollama

```powershell
ollama serve
```

### Terminal 2: Backend

```powershell
cd RepoPilot\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Terminal 3: Frontend

```powershell
cd RepoPilot\frontend
npm run dev
```

Then open:

```text
http://localhost:5173
```

---

# 🐳 Docker Installation

RepoPilot also supports Docker Compose.

Make sure Docker Desktop is installed and running.

From the project root:

```powershell
cd RepoPilot
```

Build and start all services:

```powershell
docker compose up --build
```

The services include:

```text
Ollama
   ↓
Backend
   ↓
Frontend
```

Download the Llama model inside the Ollama container:

```powershell
docker compose exec ollama ollama pull llama3.1:8b
```

Access:

```text
Frontend:
http://localhost:5173

Backend:
http://localhost:8000

Swagger:
http://localhost:8000/docs
```

Stop the application:

```powershell
docker compose down
```

---

# 🔎 Example Repository

After starting the application, enter a public GitHub repository URL such as:

```text
https://github.com/psf/requests
```

RepoPilot will analyze the repository and generate:

* Repository overview
* Language statistics
* Architecture
* Dependency graph
* Complexity information
* File explorer
* Code information
* GitHub issues
* Onboarding roadmap
* AI assistant responses

---

# 🧠 How RAG Works

RepoPilot uses Retrieval-Augmented Generation to provide repository-specific answers.

### 1. Code Chunking

Repository files are divided into smaller code chunks.

```text
Large Source File
       ↓
Code Chunks
       ↓
~80 lines per chunk
```

Chunks use overlap to preserve context between sections.

### 2. Embeddings

Each chunk is converted into a vector using:

```text
all-MiniLM-L6-v2
```

Conceptually:

```text
Source Code
     ↓
Embedding Model
     ↓
Vector
```

### 3. Vector Storage

The embeddings are stored in:

```text
ChromaDB
```

Each repository has its own collection.

### 4. Question Retrieval

When a developer asks:

```text
"Where is authentication implemented?"
```

the question is converted into an embedding.

ChromaDB searches for semantically similar code chunks.

### 5. LLM Generation

The retrieved code is provided as context to the Llama model through Ollama.

```text
Question
   +
Relevant Code
   ↓
Llama 3.1
   ↓
Grounded Answer
```

---

# 🤖 Multi-Agent System

RepoPilot uses specialized agents.

### Repository Agent

Provides general repository information and important files.

### Architecture Agent

Analyzes project architecture and layers.

### Dependency Agent

Analyzes dependencies and relationships between files.

### Code Agent

Analyzes specific code and implementation details.

### RAG Agent

Retrieves relevant source-code context.

### Issue Agent

Analyzes GitHub issues.

### Onboarding Agent

Creates a developer onboarding roadmap.

### Developer Agent

Combines retrieved information and agent results to generate the final developer-facing response.

### Orchestrator

The orchestrator determines which agents should participate in answering a question.

---

# 🔌 API Endpoints

| Method | Endpoint                            | Purpose                         |
| ------ | ----------------------------------- | ------------------------------- |
| POST   | `/api/repository/analyze`           | Analyze and index a repository  |
| GET    | `/api/progress/{id}`                | Check analysis progress         |
| GET    | `/api/repositories`                 | List saved repositories         |
| GET    | `/api/repository/{id}`              | Get repository analysis         |
| GET    | `/api/repository/{id}/graph`        | Get dependency graph            |
| GET    | `/api/repository/{id}/complexity`   | Get complexity information      |
| GET    | `/api/repository/{id}/architecture` | Get architecture analysis       |
| GET    | `/api/repository/{id}/file`         | Get source file information     |
| POST   | `/api/repository/search`            | Perform semantic code search    |
| DELETE | `/api/repository/{id}`              | Delete repository data          |
| POST   | `/api/assistant/ask`                | Ask the AI assistant            |
| POST   | `/api/onboarding/roadmap`           | Generate onboarding roadmap     |
| GET    | `/api/issues/{id}`                  | Get repository issues           |
| POST   | `/api/issues/analyze`               | Analyze issues                  |
| GET    | `/health`                           | Check backend and Ollama status |

---

# 🧪 Testing

Run backend tests:

```powershell
cd RepoPilot\backend
.\.venv\Scripts\Activate.ps1
pytest
```

---

# ⚙️ Important Configuration

| Variable                 | Purpose                             |
| ------------------------ | ----------------------------------- |
| `GITHUB_TOKEN`           | Optional GitHub API authentication  |
| `OLLAMA_BASE_URL`        | Ollama server address               |
| `OLLAMA_MODEL`           | LLM used by the application         |
| `OLLAMA_TIMEOUT`         | Maximum LLM request time            |
| `OLLAMA_NUM_CTX`         | LLM context size                    |
| `EMBEDDING_MODEL`        | Embedding model                     |
| `CHROMA_DIR`             | ChromaDB storage location           |
| `REPOS_DIR`              | Repository storage location         |
| `MAX_FILE_SIZE_KB`       | Maximum file size for analysis      |
| `MAX_FILES_TO_ANALYZE`   | Maximum number of analyzed files    |
| `TOP_K_RESULTS`          | Number of relevant chunks retrieved |
| `MAX_CONTEXT_CHARACTERS` | Maximum context sent to the LLM     |
| `FRONTEND_URL`           | Frontend URL used for CORS          |
| `VITE_API_URL`           | Backend URL used by the frontend    |

---

# 🔐 Security

RepoPilot is designed to safely analyze repository source code.

* Repository source code is read as text.
* Repository code is not executed.
* Binary files are skipped.
* Oversized files are skipped.
* File paths are sanitized.
* GitHub tokens remain on the backend.
* API errors do not expose backend stack traces.
* Environment files containing secrets should never be committed.

---

# ⚠️ Limitations

* Currently designed primarily for public GitHub repositories.
* Unauthenticated GitHub API access has rate limits.
* Python uses AST-based analysis.
* JavaScript, TypeScript, JSX, TSX, and Java analysis is pattern-based.
* Complexity measurements are heuristic.
* Architecture detection is based on repository evidence.
* Large repositories are limited by configurable analysis limits.
* AI response quality depends on the local Ollama model.
* Progress information is stored in memory and resets when the backend restarts.

---

# 🔮 Future Improvements

Possible future enhancements include:

* Tree-sitter based multi-language parsing
* Support for additional programming languages
* Private repository support using OAuth
* Incremental repository indexing
* Hybrid BM25 + vector retrieval
* Streaming AI responses
* Persistent conversation history
* Improved dependency analysis
* Cloud deployment
* Repository change tracking
* Automated pull-request analysis

---

# 📚 Key Concepts Demonstrated

This project demonstrates practical experience with:

```text
Python
FastAPI
REST APIs
React
Vite
GitHub API
Static Code Analysis
AST
Dependency Graphs
NetworkX
Embeddings
Vector Databases
ChromaDB
RAG
Multi-Agent AI
LLMs
Ollama
Llama
Docker
Git
GitHub
```

---

# 💼 Project Summary

**RepoPilot is an Agentic AI system that automatically analyzes GitHub repositories and helps developers understand unfamiliar codebases. It combines static code analysis, dependency graph generation, vector embeddings, ChromaDB-based retrieval, multi-agent orchestration, and a locally hosted Llama model through Ollama to provide repository-specific insights and developer assistance.**

---

# 👨‍💻 Author

**Yellanki Ashish**

GitHub:

https://github.com/Yellanki-Ashish

---

# ⭐ If you find this project useful

Give the repository a ⭐ on GitHub.
