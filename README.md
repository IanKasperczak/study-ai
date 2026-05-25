# Project Study IA

Aplicacion de escritorio/web para estudiar con ayuda de inteligencia artificial. El objetivo es permitir que una persona seleccione una carpeta local con materiales de estudio, procese automaticamente documentos y videos, organice el contenido por temas y use herramientas de IA para aprender mejor.

> Estado actual: proyecto en etapa inicial. Este README define la vision, la arquitectura esperada y la estrategia de desarrollo del MVP.

## Descripcion

Project Study IA busca transformar archivos de estudio dispersos en una experiencia guiada de aprendizaje. La aplicacion analizara PDFs, documentos Word, presentaciones, archivos de texto y videos para extraer contenido, detectar temas importantes y construir un sistema de consulta contextual basado en los documentos cargados.

La experiencia estara enfocada en:

- Importar materiales de estudio desde archivos o carpetas locales.
- Extraer texto y transcripciones de distintos formatos.
- Dividir el contenido automaticamente en temas.
- Generar resumenes, explicaciones, preguntas, flashcards y quizzes.
- Responder preguntas usando solamente el contenido cargado.
- Acompanhar sesiones de estudio con un temporizador Pomodoro.

## Stack Tecnologico

### Frontend

- Next.js
- TypeScript
- TailwindCSS
- Framer Motion
- UI moderna en modo oscuro

### Backend

- Python
- FastAPI
- Servicios modulares para procesamiento, IA y RAG

### Inteligencia Artificial

- OpenAI API
- Whisper o equivalente para transcripcion de audio/video
- Embeddings para busqueda semantica

### Vector DB

- ChromaDB

### Procesamiento de archivos

- PyMuPDF para PDF
- python-docx para DOCX
- python-pptx para PPTX
- ffmpeg para extraccion de audio desde video
- Procesamiento de TXT nativo

## Arquitectura Planeada

```text
project-study-ia/
|-- frontend/              # Aplicacion Next.js
|-- backend/               # API FastAPI
|   |-- app/
|   |   |-- api/           # Rutas HTTP
|   |   |-- core/          # Configuracion general
|   |   |-- services/      # OpenAI, Whisper, RAG
|   |   |-- processors/    # PDF, DOCX, PPTX, TXT, video
|   |   |-- models/        # Schemas y modelos internos
|   |   `-- utils/         # Helpers compartidos
|   `-- tests/
|-- docs/
|   `-- screenshots/       # Capturas futuras
`-- README.md
```

## Features Planeadas

- Seleccion de archivos o carpeta local.
- Soporte para PDF, DOCX, PPTX, TXT y MP4.
- Extraccion automatica de texto.
- Extraccion de audio y transcripcion de videos.
- Deteccion de titulos, subtitulos y conceptos importantes.
- Agrupacion automatica por temas.
- Panel de temas seleccionables.
- Herramientas de estudio por tema:
  - resumen;
  - explicacion simple;
  - preguntas tipo examen;
  - flashcards;
  - mini quiz;
  - explicacion paso a paso.
- Chat contextual con RAG.
- Busqueda vectorial con ChromaDB.
- Respuestas basadas solamente en documentos cargados.
- Temporizador Pomodoro flotante.
- Estadisticas simples de tiempo estudiado.
- Interfaz oscura inspirada en cielo nocturno, Notion, Obsidian y Linear.

## Roadmap

### Fase 1: MVP Funcional

- Crear estructura base del monorepo.
- Implementar API FastAPI.
- Implementar interfaz Next.js.
- Permitir carga de archivos.
- Extraer texto de PDF, DOCX, PPTX y TXT.
- Generar temas iniciales con IA.
- Crear panel de temas.
- Agregar herramientas basicas de estudio.
- Implementar chat contextual con RAG local.

### Fase 2: Videos y Transcripcion

- Integrar ffmpeg para extraer audio.
- Integrar Whisper o servicio equivalente.
- Guardar transcripciones junto al material procesado.
- Incluir transcripciones en el sistema RAG.

### Fase 3: Experiencia de Estudio

- Mejorar seleccion y combinacion de temas.
- Agregar flashcards interactivas.
- Agregar mini quizzes con correccion.
- Agregar historial de sesiones.
- Agregar estadisticas de Pomodoro.

### Fase 4: Calidad y Producto

- Persistencia de proyectos de estudio.
- Mejor manejo de errores.
- Tests unitarios e integracion.
- Optimizacion de embeddings.
- Empaquetado como aplicacion de escritorio si se decide usar Electron o Tauri.

## Screenshots

> Capturas pendientes. Estos placeholders se reemplazaran cuando exista el MVP visual.

| Vista | Placeholder |
| --- | --- |
| Dashboard principal | `docs/screenshots/dashboard.png` |
| Panel de temas | `docs/screenshots/topics-panel.png` |
| Chat contextual | `docs/screenshots/context-chat.png` |
| Pomodoro flotante | `docs/screenshots/pomodoro.png` |

## Estrategia de Ramas

La estrategia sera simple y pensada para desarrollo individual.

### `main`

Rama estable del proyecto. Debe representar una version que funciona o que esta lista para mostrar.

Usos recomendados:

- guardar versiones estables;
- crear releases;
- mantener una base limpia del proyecto.

No se trabaja directamente sobre `main`, salvo cambios muy pequenos de documentacion o configuracion.

### `develop`

Rama principal de desarrollo. Aca se integran las funcionalidades antes de pasarlas a `main`.

Usos recomendados:

- probar el MVP completo;
- integrar features terminadas;
- detectar conflictos antes de publicar una version estable.

Cuando `develop` esta estable, se mergea hacia `main`.

### `feature/*`

Ramas cortas para trabajar una funcionalidad concreta.

Ejemplos:

```text
feature/file-upload
feature/document-processing
feature/rag-chat
feature/pomodoro-timer
feature/dark-ui
```

Flujo recomendado:

1. Crear la rama desde `develop`.
2. Implementar una funcionalidad pequena y clara.
3. Probar que funciona.
4. Mergear a `develop`.
5. Borrar la rama cuando ya no se necesite.

Comandos habituales:

```bash
git checkout develop
git pull
git checkout -b feature/nombre-de-la-feature

# trabajar, commitear y probar

git checkout develop
git merge feature/nombre-de-la-feature
git branch -d feature/nombre-de-la-feature
```

Para publicar una version estable:

```bash
git checkout main
git merge develop
git tag v0.1.0
```

## Instalacion Futura

> Los comandos definitivos pueden cambiar cuando se implemente la estructura real del proyecto.

### Requisitos esperados

- Node.js 20+
- Python 3.11+
- ffmpeg instalado en el sistema
- Cuenta y API key de OpenAI

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Variables de entorno

Crear archivos `.env` a partir de los ejemplos futuros:

```bash
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

Variables esperadas:

```env
OPENAI_API_KEY=your_openai_api_key
CHROMA_DB_PATH=./storage/chroma
UPLOAD_DIR=./storage/uploads
```

## Principios del Proyecto

- Codigo limpio y modular.
- MVP funcional antes que complejidad innecesaria.
- Separacion clara entre frontend, backend, procesamiento, IA y RAG.
- Experiencia de usuario cuidada desde el inicio.
- Respuestas de IA fundamentadas solo en los documentos cargados.
- Datos locales sensibles fuera del control de versiones.
