# Presentation script (slides + demo video)

Content the delivery asks for: *how the project was created, the problems it
solves, and how it works.* Ten slides, about 45 seconds each (≈ 8 minutes),
plus a 3-minute demo video. Each slide lists what goes **on screen** and what to
**say**. The spoken lines are in Spanish on purpose: the talk is given in Spanish.

## Slides (10)

### 1. Title
- **On screen:** *Un cortado, por favor* · "tu podcast, a tu gusto" · Abel Rincón ·
  Máster de Desarrollo con IA (BIG school) · gitlab.com/fabelium/cortado
- **Say:** "Soy Abel Rincón y esto es Un cortado, por favor: una app que convierte un
  podcast enorme en un audio corto y a tu medida."

### 2. The problem
- **On screen:** ~480 episodes × ~1.5 h ≈ **700 hours** of audio · "¿Qué dijeron
  sobre agujeros negros?" → impossible by hand.
- **Say:** "Coffee Break: Señal y Ruido es un podcast de ciencia con cientos de
  episodios. Cada uno tiene la lista de temas con sus minutos, pero encontrar qué
  se dijo sobre un tema en 700 horas no se puede hacer a mano."

### 3. The solution
- **On screen:** Search → Curate → Generate (audio · transcript · book · chat) and
  one screenshot of the UI (`make up`, taken at 1440 px).
- **Say:** "Buscas un tema, eliges los fragmentos que te interesan y la app te
  prepara un MP3 con ellos, la transcripción, un resumen tipo libro o un chat que
  responde citando los episodios."

### 4. How it works
- **On screen:** the architecture diagram from the README
  (`Browser → Nuxt → Laravel API → JSON contract → Python engine`) and, below,
  "RSS · ffmpeg · whisper · LLM".
- **Say:** "Son tres piezas independientes: un frontend en Nuxt, una API en Laravel
  y un motor en Python. Solo hablan a través de un contrato JSON versionado,
  validado con tests en ambos lados. Así cada pieza evoluciona sin romper a las
  demás."

### 5. The AI inside the product
- **On screen:** semantic search (embeddings) · LLM relevance classifier · RAG
  chat · book composer · "no fine-tuning, RAG" · local-first (fastembed), Gemini
  optional.
- **Say:** "La búsqueda semántica entiende significado: 'vida extraterrestre'
  también encuentra OVNIs. Un LLM filtra los candidatos y da una razón. El chat
  responde solo con tus fragmentos, citando episodio y fecha. Decidí no entrenar
  ningún modelo: RAG es más barato, actualizable y verificable."

### 6. The AI building the product
- **On screen:** spec before code · TDD · subagents · a review pass per change ·
  **319 tests** (engine 126 + API 90 + frontend 103).
- **Say:** "También usé IA para construirlo, con disciplina: primero la
  especificación, luego un test que falla, luego el código mínimo y una revisión de
  cada cambio. Yo defino los criterios y verifico; la IA hace el trabajo. El
  resultado son 319 tests entre los tres componentes."

### 7. Working with parallel AI sessions
- **On screen:** three sessions → engine · api · frontend · "one session, one
  subproject" · rules: stage only your own files, claim shared work before
  starting it.
- **Say:** "Lo más original: tres sesiones de IA trabajando a la vez, cada una
  dueña de un componente y coordinadas por el contrato. Hubo dos colisiones reales
  y de ahí salió una regla: reclamar el trabajo compartido antes de empezarlo."

### 8. Problems and solutions
- **On screen:** a *symptom → cause → fix → test* table with four rows:

  | Problem | Solution |
  |---|---|
  | ~700 h of audio cannot be transcribed up front | **On-demand transcription**: only the fragments the user picks, cached forever |
  | Generating takes minutes; HTTP requests time out | **Async jobs** (`202` + polling), 30 min job timeout |
  | Fragment ids collapsed (`Ep563_B` → `ep0`) | Ids keep the episode part; unnumbered episodes get a stable digest |
  | gTTS broke the disclaimer mid-phrase | A comma keeps each segment under its 100-char limit, guarded by a test |

- **Say:** "Cuatro problemas reales. Por ejemplo, el audio largo: una petición HTTP
  no aguanta minutos, así que cada generación es un job en cola con progreso. Lo
  probé de verdad: tres fragmentos, unos tres minutos y un MP3 de 64 minutos."

### 9. Quality and responsibility
- **On screen:** 3 test suites + CI · contract validation · security hardening
  (ffmpeg/yt-dlp injection, API key in header, login throttling) · legal posture:
  private use behind login, spoken disclaimer, self-hosted fonts and icons.
- **Say:** "Calidad: tests en las tres capas y validación del contrato. Seguridad:
  protección frente a inyección en comandos y límite de intentos de login. Y
  responsabilidad: el audio es de otros, así que la app es de uso privado con
  login, cada archivo empieza con un aviso hablado y no la he desplegado
  públicamente a propósito."

### 10. What's next
- **On screen:** live progress (Reverb) · Docker images for the API and engine ·
  more AI providers · rename the package to `cortado` · repo URL · test account.
- **Say:** "Lo siguiente: progreso en tiempo real, imágenes Docker de todo el
  sistema y más proveedores de IA. El código está en GitLab, con instrucciones y un
  usuario de prueba. Gracias."

If time runs short, drop slide 7 or 9 (≈ 7 minutes).

## Video script (≈3 min, screen recording of `make up`)

| Time | On screen | Say |
|---|---|---|
| 0:00 | Login page, log in with the test account | What the app is, in one sentence |
| 0:20 | Search "agujero negro", results appear | Keyword + semantic search over the catalogue |
| 0:50 | Include 3 fragments, drag to reorder | Curation: the user decides the order |
| 1:20 | Pick Audio + Transcript, **Preparar** | Async job with progress; engine cuts with ffmpeg |
| 1:50 | Play the generated MP3 (intro + disclaimer) | Spoken announcements, disclaimer, Spanish audio |
| 2:15 | Chat: ask a question, show cited sources | RAG over the transcripts |
| 2:40 | Terminal: `make test` green | Three test suites, CI, contract validation |
| 2:55 | README | Built with AI sessions that coordinate through files |

Tips: record at 1080p, pre-warm the cache (run one search and one generation
beforehand — the first download of an episode is slow; three fragments took about
3 minutes), set `GEMINI_API_KEY` so chat answers are real, and use the seeded demo
user from the README.
