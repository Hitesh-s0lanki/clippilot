# Prompts

One Markdown file per agent. The file **is** the system prompt: it is sent to the model
verbatim, so it is written as instructions to the model, not as documentation about the
model.

Prompts live here rather than in Python string literals so they can be read, reviewed and
diffed as prose. A change to a prompt is a change to behaviour and should show up in a
diff looking like one.

## Naming

`<agent-name>.md`, matching the agent's `name` — `campaign-strategist.md` for
`CampaignStrategistAgent`. The agent points at it with `prompt_file`, without the suffix.

Files beginning with `_`, and `README.md`, are ignored by `PromptLibrary.available()`.

## Placeholders

`{{name}}` is replaced when `name` is one of the variables the agent supplies, and is
**left exactly as written** when it is not.

That second half is load-bearing. The campaign prompts have to teach the model to emit the
product's own personalisation token — the literal text `{{customer_name}}` — and a
templating engine that substituted or errored on every placeholder it saw would eat it.

Two variables are supplied to every prompt by `BaseAgent`:

| Placeholder | Value |
| --- | --- |
| `{{output_tool}}` | The name of the terminal tool the model calls to finish. Derived from the agent's `output_model`, so a renamed schema never leaves the prompt naming a tool that no longer exists. |
| `{{research_tools}}` | The tools that actually loaded this run, comma-separated, or `none available`. |

Anything else comes from the agent's `prompt_variables()`.

## What belongs in the prompt, and what does not

| Goes in the prompt | Goes in the schema | Goes in code |
| --- | --- | --- |
| Method, priorities, standards of evidence, tone | Field names, types, lengths, enum values, per-field instructions | Rules that must hold every time |

Field-level instruction belongs in the Pydantic `description=`, because the output schema
is handed to the model as a tool definition and every description is read as part of the
instructions. Restating the schema in the prompt just creates a second copy to keep in
sync.

Rules that must hold every time belong in `finalise()` — a user-chosen objective the model
may not override, for instance. A prompt makes something likely; only code makes it
certain.
