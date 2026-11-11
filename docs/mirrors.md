# Mirrors

Behind a corporate network, optional questions point downloads at internal mirrors (e.g. Nexus).
They are written to `.brigade/mirror.toml`; leave them empty to download from the internet.

| Question | Example | Used for |
|---|---|---|
| `github_mirror` | `https://nexus.example.com/repository/github/` | Tools mise downloads from GitHub releases (mise `url_replacements`). |
| `pypi_index` | `https://nexus.example.com/repository/pypi/simple` | Python tools installed by mise (`pipx:`), and `uv` / `uvx` in tasks (`UV_DEFAULT_INDEX`). |

mise still reads release metadata from `mise-versions.jdx.dev` or `api.github.com`.
Allow them, or see mise's [URL replacements](https://mise.jdx.dev/url-replacements.html).
