# Transcript → Instagram Carousel (multi-agent)

Takes a video transcript and produces one background image per slide, the slide text, and a post
caption. The curator combines image + text in Canva and posts.

```
transcript ─► Content Writer ─► Prompt Writer ─► Designer ─► package
              (tree-of-thoughts)                 (generate → check → Reflexion, ≤2 retries)
```

| Agent | File | Does |
|---|---|---|
| Content Writer | `agents/content_writer.py` | Proposes 3 slide breakdowns, picks one, writes slide text, caption, mood |
| Prompt Writer | `agents/prompt_writer.py` | One image prompt per slide, one shared style, no text, space left for overlay |
| Designer | `agents/designer.py` | Calls `generate_slide_image` (MCP), `check_slide`, retries, `package_carousel` |

- `tools/image_server.py` – MCP server with `generate_slide_image`; swap the backend with `IMAGE_BACKEND`
  (`placeholder` offline gradients, `openai` = `gpt-image-1`).
- Shared state (`state.py`) grows at each handoff; the style guide (`style_guide.json`) reaches every agent.
- Slides still failing after 2 retries are marked `flagged_for_curator` in `carousel.json`.

## Run
```bash
pip install -e '.[dev]'        # add ',openai' for the OpenAI image backend
export ANTHROPIC_API_KEY=...
carousel transcript.txt -o output --max-slides 8
pytest                         # offline: scripted LLM + real MCP server
```
Text agents use `claude-opus-5-5` (override with `CAROUSEL_MODEL`).

## Not built yet
A2A deployment of the Designer (optional in the design) — the Designer already takes an
`ImageGenerator`, so it can be moved behind a service later.
