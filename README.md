# Project Study IA

Aplicacion web/de escritorio para estudiar con ayuda de inteligencia artificial. El MVP permite cargar archivos locales de estudio, extraer texto de documentos, dividir el contenido en chunks, generar temas automaticamente y estudiar con resumenes, explicaciones simples, chat contextual y temporizador Pomodoro.

## Estado Del Proyecto

MVP base implementado:

- Frontend separado con Next.js, TypeScript, TailwindCSS y Framer Motion.
- Backend separado con FastAPI.
- Procesamiento inicial de PDF, DOCX, TXT y MD.
- Almacenamiento local temporal en `backend/storage`.
- Generacion heuristica de temas.
- RAG basico con busqueda lexical sobre chunks locales.
- Servicios preparados para usar OpenAI si se configura `OPENAI_API_KEY`.
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
- RAG MVP con chunks locales y busqueda lexical
- Preparado para evolucionar a embeddings + ChromaDB

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
- Pomodoro flotante con modo foco/pausa y sonido opcional.

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

- [ ] Agregar embeddings.
- [ ] Integrar ChromaDB.
- [ ] Mejorar ranking semantico.
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
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4o-mini
```

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
