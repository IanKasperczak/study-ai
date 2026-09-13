# Project Study IA

Aplicacion web/de escritorio para estudiar con ayuda de inteligencia artificial. El MVP permite cargar archivos locales de estudio, extraer texto de documentos, dividir el contenido en chunks, generar temas automaticamente y estudiar con resumenes, explicaciones simples, chat contextual y temporizador Pomodoro.

## Estado Del Proyecto

MVP base implementado:

- Frontend separado con Next.js, TypeScript, TailwindCSS y Framer Motion.
- Backend separado con FastAPI.
- Procesamiento inicial de PDF, DOCX, TXT y MD.
- Almacenamiento local temporal en `backend/storage`.
- Generacion heuristica de temas.
- RAG con busqueda semantica por embeddings (si el provider activo los soporta) y fallback automatico a busqueda lexical sobre chunks locales.
- Servicios preparados para usar OpenAI, NVIDIA NIM u Ollama segun `AI_PROVIDER`.
- Pomodoro funcional con estadisticas simples en `localStorage`.

No incluye autenticacion ni base de datos SQL.

## Stack

### Frontend

- Next.js
- TypeScript
- TailwindCSS
- Framer Motion
- lucide-react

### Backend

- Python
- FastAPI
- Uvicorn
- PyMuPDF
- python-docx
- OpenAI SDK preparado para integracion

### IA y RAG

- OpenAI API opcional mediante `OPENAI_API_KEY`
- NVIDIA NIM opcional mediante `AI_PROVIDER=nim` y `NVIDIA_API_KEY` (hosteado o self-hosted)
- Ollama local opcional mediante `AI_PROVIDER=ollama` y `OLLAMA_MODEL`
- Otros proveedores OpenAI-compatibles via `OPENAI_BASE_URL`
- RAG con embeddings por chunk (OpenAI, NVIDIA NIM u Ollama, segun el provider activo) y ranking por similitud coseno
- Si no hay embeddings disponibles, cae automaticamente a busqueda lexical (nunca rompe el chat)
- Preparado para evolucionar a un vector store dedicado (ChromaDB) si el volumen de documentos crece

## Arquitectura

```text
project-study-ia/
|-- frontend/
|   |-- app/
|   |-- components/
|   |-- lib/
|   |-- package.json
|   `-- tailwind.config.ts
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- models/
|   |   |-- processors/
|   |   `-- services/
|   |-- requirements.txt
|   `-- .env.example
|-- docs/
|   `-- screenshots/
|-- README.md
`-- .gitignore
```

### Decisiones Importantes

- El frontend no accede directamente al sistema de archivos. Usa inputs de archivo/carpeta del navegador y envia los documentos al backend.
- El backend guarda datos temporales localmente en `backend/storage`, que esta excluido de Git.
- El RAG inicial es lexical para mantener el MVP simple y ejecutable sin depender de embeddings.
- La capa `ai_service.py` centraliza OpenAI. Si no hay API key, devuelve respuestas extractivas basadas en el contexto.
- Los procesadores de documentos estan separados por formato para que sea facil sumar PPTX, video, Whisper y ffmpeg despues.

## Features Del MVP

- Subida de multiples archivos.
- Subida de carpeta desde navegador compatible.
- Extraccion de texto desde PDF.
- Extraccion de texto desde DOCX.
- Extraccion de texto desde TXT/MD.
- Chunking de contenido.
- Generacion automatica de temas.
- Sidebar con temas seleccionables.
- Accion para generar resumen.
- Accion para generar explicacion simple.
- Chat contextual basado en documentos cargados.
- Pomodoro flotante, movible y redimensionable, con minimizar, modo foco/pausa, multiples tecnicas de estudio (Pomodoro, Foco profundo, Flow, Sprint, Micro) y sonido opcional.

## Roadmap

### Fase 1: MVP Base

- [x] Crear monorepo frontend/backend.
- [x] Implementar UI principal oscura.
- [x] Implementar carga de archivos.
- [x] Procesar PDF, DOCX y texto.
- [x] Crear chunking y temas automaticos.
- [x] Crear resumen, explicacion simple y chat contextual.
- [x] Agregar Pomodoro.

### Fase 2: RAG Real

- [x] Agregar embeddings (por chunk, al subir el documento).
- [x] Mejorar ranking semantico (similitud coseno, con fallback lexical).
- [ ] Integrar ChromaDB (hoy la similitud se calcula en memoria; migrar cuando el volumen de chunks lo justifique).
- [ ] Agregar citas mas precisas por documento y pagina.

### Fase 3: Mas Formatos

- [ ] Procesar PPTX.
- [ ] Procesar MP4/video.
- [ ] Extraer audio con ffmpeg.
- [ ] Transcribir con Whisper o equivalente.

### Fase 4: Experiencia De Estudio

- [ ] Flashcards.
- [ ] Preguntas tipo examen.
- [ ] Mini quiz.
- [ ] Explicacion paso a paso.
- [ ] Historial de sesiones.
- [ ] Estadisticas mas completas.

## Screenshots

Placeholders para futuras capturas:

| Vista | Archivo |
| --- | --- |
| Dashboard principal | `docs/screenshots/dashboard.png` |
| Panel de temas | `docs/screenshots/topics-panel.png` |
| Chat contextual | `docs/screenshots/context-chat.png` |
| Pomodoro flotante | `docs/screenshots/pomodoro.png` |

## Instalacion Local

### Requisitos

- Node.js 20+
- Python 3.11+
- Git

### Backend

```bash
cd backend
python -m venv .venv
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

En macOS/Linux:

```bash
source .venv/bin/activate
```

Instalar dependencias y correr API:

```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

La API queda disponible en:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

La app queda disponible en:

```text
http://localhost:3000
```

## Variables De Entorno

### Backend

```env
PROJECT_NAME=Project Study IA
API_PREFIX=/api
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
STORAGE_DIR=./storage
UPLOAD_DIR=./storage/uploads
PROJECTS_DIR=./storage/projects
AI_PROVIDER=
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
NVIDIA_API_KEY=
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_MODEL=meta/llama-3.1-8b-instruct
NIM_EMBED_MODEL=nvidia/nv-embedqa-e5-v5
OPENAI_EMBED_MODEL=text-embedding-3-small
OLLAMA_EMBED_MODEL=nomic-embed-text
```

`AI_PROVIDER` acepta `openai`, `nim`, `ollama` o vacio (auto-deteccion: OpenAI, despues NIM, despues Ollama, segun que variables esten seteadas). Ollama expone una API OpenAI-compatible, asi que tambien funciona con cualquier motor que sirva `/v1`. Con `OPENAI_BASE_URL` se puede apuntar a otros proveedores compatibles (Groq, OpenRouter, etc.).

Para usar **NVIDIA NIM** en vez de Ollama local: seteá `AI_PROVIDER=nim` y `NVIDIA_API_KEY` con una key generada en [build.nvidia.com](https://build.nvidia.com); `NIM_MODEL` acepta cualquier modelo del catalogo NIM (ej. `meta/llama-3.1-8b-instruct`, `mistralai/mixtral-8x7b-instruct-v0.1`). Si corres tu propio NIM self-hosted (container Docker de NVIDIA), apunta `NIM_BASE_URL` a ese endpoint y dejá `NVIDIA_API_KEY` vacio. Sin ningun proveedor configurado o activo, el backend responde en modo extractivo.

El mismo provider activo (`openai`, `nim` u `ollama`) se usa tambien para generar embeddings de cada chunk al subir un documento (`NIM_EMBED_MODEL`, `OPENAI_EMBED_MODEL`, `OLLAMA_EMBED_MODEL` segun corresponda). El chat y las acciones de estudio buscan primero por similitud semantica sobre esos embeddings; si un proyecto no los tiene (por ejemplo, se subio sin proveedor configurado) o la llamada de embeddings falla, el RAG cae automaticamente a busqueda lexical sin romper nada.

### Frontend

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Endpoints Principales

- `POST /api/uploads`: sube archivos y crea un proyecto temporal.
- `GET /api/study/{project_id}/topics`: lista temas detectados.
- `POST /api/study/summary`: genera resumen.
- `POST /api/study/simple-explanation`: genera explicacion simple.
- `POST /api/chat`: pregunta al chat contextual.

## Estrategia De Ramas

### `main`

Rama estable. Debe representar una version que funciona y se puede mostrar.

### `develop`

Rama de integracion. Aca se juntan features terminadas antes de pasar a `main`.

### `feature/*`

Ramas cortas para funcionalidades concretas.

Ejemplos:

```text
feature/file-upload
feature/document-processing
feature/rag-chat
feature/pomodoro-timer
feature/dark-ui
```

Flujo simple:

```bash
git checkout develop
git checkout -b feature/nombre-de-la-feature

# trabajar y commitear

git checkout develop
git merge feature/nombre-de-la-feature
git branch -d feature/nombre-de-la-feature
```

Cuando `develop` este estable:

```bash
git checkout main
git merge develop
```

## Principios

- Codigo modular y legible.
- MVP funcional antes de optimizaciones.
- Separacion clara entre UI, API, procesamiento, IA y RAG.
- Datos locales fuera de Git.
- Respuestas del chat basadas solamente en documentos cargados.
