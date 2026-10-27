# Branding

The project name and how to write it.

## Name

> **Un cortado, por favor**

A warm, distinctly Spanish name: it evokes sitting down for a *coffee break* and
**ordering** your topic — with the wink that *cortado* also means "to cut" (the
tool cuts the podcast into thematic fragments). The podcast it serves is *Coffee
Break: Señal y Ruido*, so the coffee metaphor is deliberate.

**Tagline:** *tu podcast, a tu gusto.*
(Full: "Un cortado, por favor — tu podcast, a tu gusto.")

## Name vs technical handle

Two layers, on purpose — the human name is long and has a comma, which is not a
valid technical identifier:

| Layer | Use it for | Value |
|-------|-----------|-------|
| **Brand / display name** | README titles, the web UI, docs, anything user-facing | **Un cortado, por favor** |
| **Technical handle** | repo, CLI command, package/module names, domain, container/service names | **`cortado`** |

So the product *is called* "Un cortado, por favor", but in code you type
`cortado ...`, the repo is `cortado`, the domain would be `cortado.dev` / `.app`,
etc.

## Usage rules

- **User-facing text** → write the full brand name "Un cortado, por favor"
  (capital U, lowercase rest, with the comma).
- **Code / infra** → always the lowercase handle `cortado` (no spaces, no comma,
  no accents).
- Do **not** translate the brand name; it is Spanish on purpose (like the spoken
  audio content). Surrounding code/docs stay English per the repo language rule.

## Monorepo metaphor (optional flavor)

- **Un cortado, por favor** — the platform (the café).
- `engine/` — the *barista*: finds, cuts and brews the audio.
- `api/` + `frontend/` — the *counter* where you place your order.

## Migration note (not done yet)

The repo already lives at <https://gitlab.com/fabelium/cortado>. The Python
package is still `coffee` / `coffee_clips.py`; renaming it and the CLI to
`cortado` is a separate, mechanical task for a later session. This file only **fixes the name**; the rename follows.
