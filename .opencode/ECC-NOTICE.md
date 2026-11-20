# ECC components (third-party)

This project vendors a curated subset of the MIT-licensed
[ECC](https://github.com/affaan-m/ECC) agent harness by Affaan Mustafa.

- Source commit: `4adeee6732a12d1540f49a4d50a38ce8c97f9a53`
- License: MIT (see `.opencode/ECC-LICENSE.txt`)

## Installed skills

`api-design`, `browser-qa`, `database-migrations`, `deployment-patterns`,
`docker-patterns`, `e2e-testing`, `fastapi-patterns`, `frontend-a11y`,
`frontend-patterns`, `generating-python-installer`, `git-workflow`,
`python-patterns`, `python-testing`.

## Installed agents

`fastapi-reviewer`, `python-reviewer`, `commit-reviewer`,
`performance-optimizer`, `e2e-runner`.

The agent frontmatter was adapted to OpenCode V2: upstream `tools` and `model`
fields were removed so the agents inherit the project model, and reviewers were
made read-only (`edit: deny`).
