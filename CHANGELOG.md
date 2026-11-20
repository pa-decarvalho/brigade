# [0.32.3](https://github.com/pa-decarvalho/brigade/compare/0.32.2...0.32.3) - 2026-11-20

### 🐛 Bug Fixes

- Releasaurus 1.4.1, local GitLab without the TLS proxy (#309) [_(4fd565ec)_](https://github.com/pa-decarvalho/brigade/commit/4fd565ec05ab5fa0e4a9b72c133c749c27c56311)

# [0.32.2](https://github.com/pa-decarvalho/brigade/compare/0.32.1...0.32.2) - 2026-11-19

### 🐛 Bug Fixes

- lock Renovate in .brigade/mise.lock, installed with the other tools (#306) [_(d517c50c)_](https://github.com/pa-decarvalho/brigade/commit/d517c50c5946e911294d575e83fb431618894789)

# [0.32.1](https://github.com/pa-decarvalho/brigade/compare/0.32.0...0.32.1) - 2026-11-19

### 🐛 Bug Fixes

- uv:deploy drops empty UV_PUBLISH_* variables (#304) [_(c9c442da)_](https://github.com/pa-decarvalho/brigade/commit/c9c442da9a07e3b060f474ea59b857c500f70411)

# [0.32.0](https://github.com/pa-decarvalho/brigade/compare/0.31.0...0.32.0) - 2026-11-19

### 🚀 Features

- <cli>:setup task, and the forge check after brigade:update (#295) [_(c812f065)_](https://github.com/pa-decarvalho/brigade/commit/c812f065a6ab3e31e18474d1d38f4e80bfa81989)

# [0.31.0](https://github.com/pa-decarvalho/brigade/compare/0.30.0...0.31.0) - 2026-11-18

### 🚀 Features

- forge CLIs (gh, glab, tea) with a check of the repository's settings (#292) [_(15e2f9ab)_](https://github.com/pa-decarvalho/brigade/commit/15e2f9aba3df8b8bd94dda2e515ee7ad5d4f051b)

### 🐛 Bug Fixes

- github.com token for Renovate off GitHub (RENOVATE_GITHUB_COM_TOKEN) (#289) [_(54eda9b3)_](https://github.com/pa-decarvalho/brigade/commit/54eda9b38f55de728daaa76ebc74caaaec0fcc2c)

# [0.30.0](https://github.com/pa-decarvalho/brigade/compare/0.29.0...0.30.0) - 2026-11-18

### 🚀 Features

- renovate_automerge question, and ci commits for brigade updates (#286) [_(34f8712b)_](https://github.com/pa-decarvalho/brigade/commit/34f8712b61de1c6f95d19127affbcab0cd822950)

# [0.29.0](https://github.com/pa-decarvalho/brigade/compare/0.28.2...0.29.0) - 2026-11-18

### 🚀 Features

- Renovate config in .brigade/configs, with a renovate_updates question (#284) [_(9e6c2732)_](https://github.com/pa-decarvalho/brigade/commit/9e6c27322592e05bcf501d0efbdaadf863c485f7)

# [0.28.2](https://github.com/pa-decarvalho/brigade/compare/0.28.1...0.28.2) - 2026-11-18

### 🐛 Bug Fixes

- mise's shims on PATH on GitLab and Gitea, for task tools aube builds (#280) [_(0b4115f9)_](https://github.com/pa-decarvalho/brigade/commit/0b4115f9ce2e999f2bd724bc2bc1e5e836100ca3)

- _(deps)_ update template (#277) [_(c2f78add)_](https://github.com/pa-decarvalho/brigade/commit/c2f78add2960453a812860ffbbb979b8f3c2f4e3)

# [0.28.1](https://github.com/pa-decarvalho/brigade/compare/0.28.0...0.28.1) - 2026-11-18

### 🐛 Bug Fixes

- Renovate leaves brigade-owned files to brigade:update (#275) [_(5182a686)_](https://github.com/pa-decarvalho/brigade/commit/5182a6868c0b29e76dcd29bb1b49fcd9f2e2b5eb)

# [0.28.0](https://github.com/pa-decarvalho/brigade/compare/0.27.1...0.28.0) - 2026-11-18

### 🚀 Features

- a direct release workflow for releasaurus (#274) [_(3bbe671c)_](https://github.com/pa-decarvalho/brigade/commit/3bbe671c675ed3c19c32e6519bfe3044aad155dd)

- Releasaurus config in .brigade/configs, with release_type from the tools (#272) [_(0a9b4cce)_](https://github.com/pa-decarvalho/brigade/commit/0a9b4cce3be6dfd78cd4ed560e5163983983a2d4)

# [0.27.1](https://github.com/pa-decarvalho/brigade/compare/0.27.0...0.27.1) - 2026-11-18

### 🐛 Bug Fixes

- release on the repository's default branch on GitHub and Gitea (#270) [_(5361050e)_](https://github.com/pa-decarvalho/brigade/commit/5361050e63e8f6fdf8f9d529ad34e59b439c14c9)

- _(deps)_ update template (#264) [_(db417b7c)_](https://github.com/pa-decarvalho/brigade/commit/db417b7c490773721ba381881d28f0c4ae7c02ca)

# [0.27.0](https://github.com/pa-decarvalho/brigade/compare/0.26.0...0.27.0) - 2026-11-17

### 🚀 Features

- add codeceptjs, with an Angular recipe (#261) [_(0d1ea788)_](https://github.com/pa-decarvalho/brigade/commit/0d1ea78892e6e2e7577b7f6eaccd0555ff1b9bcc)

# [0.26.0](https://github.com/pa-decarvalho/brigade/compare/0.25.4...0.26.0) - 2026-11-17

### 🚀 Features

- optional git hooks with the prek tool (#258) [_(a3970704)_](https://github.com/pa-decarvalho/brigade/commit/a39707041d7d8d87edec3e2321e4db7add465220)

# [0.25.4](https://github.com/pa-decarvalho/brigade/compare/0.25.3...0.25.4) - 2026-11-17

### 🐛 Bug Fixes

- yamllint skips .ctt/, zizmor comments in the Gitea actions (#254) [_(64b5c8d9)_](https://github.com/pa-decarvalho/brigade/commit/64b5c8d9b2d2ee2c6f95e3bafe35546a79dc6689)

# [0.25.3](https://github.com/pa-decarvalho/brigade/compare/0.25.2...0.25.3) - 2026-11-17

### 🐛 Bug Fixes

- lint the Renovate config wherever Renovate reads it (#252) [_(81e655ea)_](https://github.com/pa-decarvalho/brigade/commit/81e655ea44daa55c2b7a6c16b6d7d1aab0eb2bed)

# [0.25.2](https://github.com/pa-decarvalho/brigade/compare/0.25.1...0.25.2) - 2026-11-17

### 🐛 Bug Fixes

- run ty without uv sync (#250) [_(41bd4bf8)_](https://github.com/pa-decarvalho/brigade/commit/41bd4bf883fd1df23bc12c0cd6bceb93710282e2)

# [0.25.1](https://github.com/pa-decarvalho/brigade/compare/0.25.0...0.25.1) - 2026-11-17

### 🐛 Bug Fixes

- rumdl defaults for generated changelogs and README headers (#248) [_(90f47205)_](https://github.com/pa-decarvalho/brigade/commit/90f4720550890519c5c6a632f721384a1edbaf35)

# [0.25.0](https://github.com/pa-decarvalho/brigade/compare/0.24.2...0.25.0) - 2026-11-17

### 🚀 Features

- brigade-owned tool configs, with a config answer per tool (#246) [_(f0c18bc2)_](https://github.com/pa-decarvalho/brigade/commit/f0c18bc2b6722a2620d4b3c62d65eaa0f63cf49e)

# [0.24.2](https://github.com/pa-decarvalho/brigade/compare/0.24.1...0.24.2) - 2026-11-16

### 🐛 Bug Fixes

- exclude mise's lock sidecars from the scanners (#241) [_(b7e71da8)_](https://github.com/pa-decarvalho/brigade/commit/b7e71da8fc20e4d8dd814bd8cd90a5188bdf55bf)

# [0.24.1](https://github.com/pa-decarvalho/brigade/compare/0.24.0...0.24.1) - 2026-11-16

### 🐛 Bug Fixes

- lock brigade's tools from .brigade/ (#239) [_(f2c9f57f)_](https://github.com/pa-decarvalho/brigade/commit/f2c9f57fa445e3e85d8074d6f0f05f40e0c29cdf)

# [0.24.0](https://github.com/pa-decarvalho/brigade/compare/0.23.0...0.24.0) - 2026-11-16

### 🚀 Features

- lock brigade's tools in .brigade/mise.lock (#236) [_(58e5e0ad)_](https://github.com/pa-decarvalho/brigade/commit/58e5e0ad09c80fc2461872e91677eb393af85ff1)

# [0.23.0](https://github.com/pa-decarvalho/brigade/compare/0.22.0...0.23.0) - 2026-11-16

### 🚀 Features

- node and rust presets, rust tool with crates.io publishing (#233) [_(65804e1e)_](https://github.com/pa-decarvalho/brigade/commit/65804e1e7f6f7ce93942a2fc16994000e402e6d3)

# [0.22.0](https://github.com/pa-decarvalho/brigade/compare/0.21.1...0.22.0) - 2026-11-16

### 🚀 Features

- named CI jobs with the jobs answer (#230) [_(811425c)_](https://github.com/pa-decarvalho/brigade/commit/811425ca924c3e8313a5e757e6bf7e12bd371023)

# [0.21.1](https://github.com/pa-decarvalho/brigade/compare/0.21.0...0.21.1) - 2026-11-16

### 🐛 Bug Fixes

- remove the brigade-data.py relay (#227) [_(05a4b61)_](https://github.com/pa-decarvalho/brigade/commit/05a4b6142c6f8ba885ac95f847880e39046ff2a3)

- _(deps)_ update template (#228) [_(b1db984)_](https://github.com/pa-decarvalho/brigade/commit/b1db9840596e1a394d4119a86d3fb6f3dae22ca1)

# [0.21.0](https://github.com/pa-decarvalho/brigade/compare/0.20.1...0.21.0) - 2026-11-16

### 🚀 Features

- one CI job per command with <stage>_jobs (#222) [_(6aa1326)_](https://github.com/pa-decarvalho/brigade/commit/6aa13263304edfe49acb9e06b811bbb4e50ef167)

# [0.20.1](https://github.com/pa-decarvalho/brigade/compare/0.20.0...0.20.1) - 2026-11-15

### 🐛 Bug Fixes

- split the test stage only for tools with a matrix, read the jobs from mise (#218) [_(8c76e9c)_](https://github.com/pa-decarvalho/brigade/commit/8c76e9c993c50d64a394dd3a13410280f566c1c2)

# [0.20.0](https://github.com/pa-decarvalho/brigade/compare/0.19.0...0.20.0) - 2026-11-15

### 🚀 Features

- one CI job per task (ci_jobs: tool), with molecule and ctt matrices (#216) [_(30ff278)_](https://github.com/pa-decarvalho/brigade/commit/30ff278fe5bf9007e6a2ff5f57b9909b8508278e)

### 🐛 Bug Fixes

- _(deps)_ update dependency cspell to v10.5.1 (#214) [_(e6ac67c)_](https://github.com/pa-decarvalho/brigade/commit/e6ac67cd3b5ecbac68a8cd5a3282647f06ab8fc8)

# [0.19.0](https://github.com/pa-decarvalho/brigade/compare/0.18.0...0.19.0) - 2026-11-15

### 🚀 Features

- add the node tool, with TypeScript and React recipes (#210) [_(a753b63)_](https://github.com/pa-decarvalho/brigade/commit/a753b63b217be9d32edeae6cd1567ace9e101d77)

- add docker and container-structure-test, with Docker recipes (#207) [_(67a8bb7)_](https://github.com/pa-decarvalho/brigade/commit/67a8bb7fea702b73c9f301d2036b5faae06d3a65)

# [0.18.0](https://github.com/pa-decarvalho/brigade/compare/0.17.2...0.18.0) - 2026-11-14

### 🚀 Features

- add go and goreleaser, and a Go recipe (#205) [_(02debbc)_](https://github.com/pa-decarvalho/brigade/commit/02debbc9f164e52d925ac343930cbc4cedbbed59)

- publish Python packages with uv:deploy and add a Python recipe (#203) [_(943af52)_](https://github.com/pa-decarvalho/brigade/commit/943af524f690c86c6c3c7212ea97ac7902e904f4)

# [0.17.2](https://github.com/pa-decarvalho/brigade/compare/0.17.1...0.17.2) - 2026-11-14

### 🐛 Bug Fixes

- keep data.yml edits on interrupted updates, skip CHANGELOG.md in lychee (#191) [_(fe5e337)_](https://github.com/pa-decarvalho/brigade/commit/fe5e337dffa845f7795a35bef09a82b2445a9e4f)

- biome skips what git ignores (#192) [_(16e6726)_](https://github.com/pa-decarvalho/brigade/commit/16e6726db596c04ada479a5edd2fcc8f24a47534)

# [0.17.1](https://github.com/pa-decarvalho/brigade/compare/0.17.0...0.17.1) - 2026-11-14

### 🐛 Bug Fixes

- import PyYAML at run time in brigade-data.py (#189) [_(7631d70)_](https://github.com/pa-decarvalho/brigade/commit/7631d70caa17fdd980e14094141f1d793cedaf7e)

# [0.17.0](https://github.com/pa-decarvalho/brigade/compare/0.16.1...0.17.0) - 2026-11-14

### 🚀 Features

- add revive, cfn-lint, cspell and ls-lint to the tool catalog (#183) [_(2f048da)_](https://github.com/pa-decarvalho/brigade/commit/2f048dada6064d63fd817119741ac503237ed7a1)

# [0.16.1](https://github.com/pa-decarvalho/brigade/compare/0.16.0...0.16.1) - 2026-11-14

### 🐛 Bug Fixes

- _(deps)_ update template (#177) [_(5679a5f)_](https://github.com/pa-decarvalho/brigade/commit/5679a5ff351eb3d37fe1a7cafe233fbdacb8482f)

# [0.16.0](https://github.com/pa-decarvalho/brigade/compare/0.15.1...0.16.0) - 2026-11-13

### 🚀 Features

- add prettier, biome, opentofu, clang-format and trivy to the tool catalog (#173) [_(9ea21b6)_](https://github.com/pa-decarvalho/brigade/commit/9ea21b6d1c5f83cf11a6c7c6fd6695980685e71a)

- add vale, lychee, codespell, markdownlint and sqlfluff to the tool catalog (#171) [_(378b349)_](https://github.com/pa-decarvalho/brigade/commit/378b349f58a8bf2aead684edf1f13f898184be13)

# [0.15.1](https://github.com/pa-decarvalho/brigade/compare/0.15.0...0.15.1) - 2026-11-13

### 🐛 Bug Fixes

- write editorconfig-checker's config on one line (#169) [_(b688977)_](https://github.com/pa-decarvalho/brigade/commit/b688977080d99eb9488b5e2cb42ded8b89093ac7)

# [0.15.0](https://github.com/pa-decarvalho/brigade/compare/0.14.0...0.15.0) - 2026-11-13

### 🚀 Features

- tool configs in .brigade/configs/ (#167) [_(74ad696)_](https://github.com/pa-decarvalho/brigade/commit/74ad69677bdc2c7c519422329ace75e40c8edcc8)

- apply an uncommitted data.yml in brigade:update (#165) [_(91127d4)_](https://github.com/pa-decarvalho/brigade/commit/91127d43a0f7eab4d91ea036e6f6906a743b1149)

# [0.14.0](https://github.com/pa-decarvalho/brigade/compare/0.13.0...0.14.0) - 2026-11-13

### 🚀 Features

- write data.yml with double quotes and indented lists (#162) [_(77073de)_](https://github.com/pa-decarvalho/brigade/commit/77073de874a67c48de8a840246c481c68f2c02f6)

### 🐛 Bug Fixes

- _(deps)_ update template (#158) [_(d2cebb5)_](https://github.com/pa-decarvalho/brigade/commit/d2cebb57695934e3d010e6670770ca55343f70b0)

# [0.13.0](https://github.com/pa-decarvalho/brigade/compare/0.12.0...0.13.0) - 2026-11-13

### 🚀 Features

- declarative answers in .brigade/copier/ (#157) [_(ef9c15d)_](https://github.com/pa-decarvalho/brigade/commit/ef9c15d1a81fda4ef049a21ec3a2f0247b09e0be)

# [0.12.0](https://github.com/pa-decarvalho/brigade/compare/0.11.0...0.12.0) - 2026-11-13

### 🚀 Features

- add tool presets (#154) [_(b932c61)_](https://github.com/pa-decarvalho/brigade/commit/b932c610c929e19ad10fb6b7605e9c5887dd55ff)

# [0.11.0](https://github.com/pa-decarvalho/brigade/compare/0.10.0...0.11.0) - 2026-11-13

### 🚀 Features

- add golangci-lint, tflint, checkov, dotenv-linter and stylua to the tool catalog (#152) [_(3358713)_](https://github.com/pa-decarvalho/brigade/commit/33587135a1674ec09c0f8f76b749b767bdb7aa75)

### 🐛 Bug Fixes

- _(deps)_ update template (#150) [_(0b48f39)_](https://github.com/pa-decarvalho/brigade/commit/0b48f39da1b0cfb8cb70385f4be715ff0df7f95a)

# [0.10.0](https://github.com/pa-decarvalho/brigade/compare/0.9.0...0.10.0) - 2026-11-12

### 🚀 Features

- add ty, shellcheck, shfmt, rumdl and osv-scanner to the tool catalog (#144) [_(96b586c)_](https://github.com/pa-decarvalho/brigade/commit/96b586cf91aff346ebbd473d93187dec32e100f9)

- add hadolint to the tool catalog (#143) [_(76841fd)_](https://github.com/pa-decarvalho/brigade/commit/76841fd80189c94c25fc20cf4d91428b3bf573e6)

- add zizmor to the tool catalog (#141) [_(c557fa3)_](https://github.com/pa-decarvalho/brigade/commit/c557fa3992207de0757b60248cb29d0ce9af2915)

# [0.9.0](https://github.com/pa-decarvalho/brigade/compare/0.8.2...0.9.0) - 2026-11-12

### 🚀 Features

- add ansible deploy and operate tasks (#140) [_(00e5f3e)_](https://github.com/pa-decarvalho/brigade/commit/00e5f3efc2b808eef8d9b447987060ddff32681f)

- add molecule to the tool catalog (#137) [_(3468c82)_](https://github.com/pa-decarvalho/brigade/commit/3468c827baf4d40ea285f7d663be793966fa640f)

- add ansible-lint to the tool catalog (#136) [_(7dadb45)_](https://github.com/pa-decarvalho/brigade/commit/7dadb45ae7c51f41811be20595caf31cdc15e93b)

### 🐛 Bug Fixes

- _(deps)_ update dependency renovate to v44.235.3 (#133) [_(8a2161d)_](https://github.com/pa-decarvalho/brigade/commit/8a2161d9893e6291fd61fe7d089fd6a6e5a3fe4f)

# [0.8.2](https://github.com/pa-decarvalho/brigade/compare/0.8.1...0.8.2) - 2026-11-12

### 🐛 Bug Fixes

- _(deps)_ update template (#130) [_(cd8a18a)_](https://github.com/pa-decarvalho/brigade/commit/cd8a18ae53cb55b18fa849acd9659988e7f1c38f)

# [0.8.1](https://github.com/pa-decarvalho/brigade/compare/0.8.0...0.8.1) - 2026-11-12

### 🐛 Bug Fixes

- keep brigade updates in their own Renovate PR, with 4-space JSON (#127) [_(b782054)_](https://github.com/pa-decarvalho/brigade/commit/b7820548f3c963c62a764d43e47e645280bb77bd)

# [0.8.0](https://github.com/pa-decarvalho/brigade/compare/0.7.1...0.8.0) - 2026-11-12

### 🚀 Features

- open a brigade update PR with Renovate on each release (#124) [_(0b6af03)_](https://github.com/pa-decarvalho/brigade/commit/0b6af037242bf332c451277c4e799936bee68fab)

# [0.7.1](https://github.com/pa-decarvalho/brigade/compare/0.7.0...0.7.1) - 2026-11-11

### 🐛 Bug Fixes

- run brigade:lint from git hooks (#120) [_(263abcb)_](https://github.com/pa-decarvalho/brigade/commit/263abcb11e77d708d5f3942ff86d7bff4684d362)

# [0.7.0](https://github.com/pa-decarvalho/brigade/compare/0.6.1...0.7.0) - 2026-11-11

### 🚀 Features

- add brigade:lint, checking that brigade-owned files are not edited (#118) [_(5ef6aa1)_](https://github.com/pa-decarvalho/brigade/commit/5ef6aa17737b159c1f4919d169214b5bcab36209)

# [0.6.1](https://github.com/pa-decarvalho/brigade/compare/0.6.0...0.6.1) - 2026-11-11

### 🐛 Bug Fixes

- set Renovate's git author to the token owner on GitHub (#114) [_(41ad9d9)_](https://github.com/pa-decarvalho/brigade/commit/41ad9d9e0f8c3afde11e491e2a209a57f2e3d9d9)

- _(deps)_ update template (#107) [_(8907c6e)_](https://github.com/pa-decarvalho/brigade/commit/8907c6ed9aaaab8109006ba54115bacf5c85b7e7)

# [0.6.0](https://github.com/pa-decarvalho/brigade/compare/0.5.1...0.6.0) - 2026-11-11

### 🚀 Features

- group brigade files in .brigade/, with one CI action per stage (#109) [_(957025c)_](https://github.com/pa-decarvalho/brigade/commit/957025ca6570b3a91b9f63c02f2beef6959be865)

# [0.5.1](https://github.com/pa-decarvalho/brigade/compare/0.5.0...0.5.1) - 2026-11-11

### 🐛 Bug Fixes

- build re2 for Renovate, set Renovate's git author (#104) [_(76f4370)_](https://github.com/pa-decarvalho/brigade/commit/76f437003e024f59c98dcd85c104d4efb519e214)

# [0.5.0](https://github.com/pa-decarvalho/brigade/compare/0.4.0...0.5.0) - 2026-11-11

### 🚀 Features

- act and gitlab-ci-local tools replace ci-local, brigade tests with its own tools (#102) [_(4b6b7e9)_](https://github.com/pa-decarvalho/brigade/commit/4b6b7e9068373127d31adadd55ed91e76ea7703b)

- lint workflows with jactionlint, harden the generated workflows (#100) [_(54bed8a)_](https://github.com/pa-decarvalho/brigade/commit/54bed8a3bfc26eb54645f9a9a09d68da5e9cab09)

# [0.4.0](https://github.com/pa-decarvalho/brigade/compare/0.3.1...0.4.0) - 2026-11-11

### 🚀 Features

- schedule the operate workflow with an operate_schedule answer (#93) [_(5eb11d9)_](https://github.com/pa-decarvalho/brigade/commit/5eb11d95b0ed42d53358a170866c0a4b0a1c3468)

### 🐛 Bug Fixes

- install Renovate despite a dependency without npm provenance (#92) [_(0367b41)_](https://github.com/pa-decarvalho/brigade/commit/0367b4144a601222f5130c9f3dd8bb3d485ff75d)

# [0.3.1](https://github.com/pa-decarvalho/brigade/compare/0.3.0...0.3.1) - 2026-11-11

### 🐛 Bug Fixes

- _(deps)_ update template (#85) [_(93597f9)_](https://github.com/pa-decarvalho/brigade/commit/93597f97cb964c8fb8d7cc138c00bbcfb7a31084)

# [0.3.0](https://github.com/pa-decarvalho/brigade/compare/0.2.0...0.3.0) - 2026-11-10

### 🚀 Features

- run the operate stage in CI, on manual runs (#82) [_(1c7590c)_](https://github.com/pa-decarvalho/brigade/commit/1c7590c83cbcb253c9eec97f1386cefac4c5bc61)

# [0.2.0](https://github.com/pa-decarvalho/brigade/compare/0.1.2...0.2.0) - 2026-11-10

### 🚀 Features

- one CI workflow per stage, lint/build/test on pull requests only (#75) [_(ab136ae)_](https://github.com/pa-decarvalho/brigade/commit/ab136ae72d18545a2aa31d7813983df687cd18e8)

### 🐛 Bug Fixes

- pages publishes site/, whatever tool builds it (#76) [_(d9b7cb1)_](https://github.com/pa-decarvalho/brigade/commit/d9b7cb1eb8edfd57dcfec99d7d92ce18618ad866)

### ⏩ CI/CD

- generate brigade with brigade (#73) [_(9fb660a)_](https://github.com/pa-decarvalho/brigade/commit/9fb660a98c6683832029369eda4c186ea9397e9a)

# [0.1.2](https://github.com/pa-decarvalho/brigade/compare/0.1.1...0.1.2) - 2026-11-10

### 🐛 Bug Fixes

- make the Releasaurus bot token optional (#71) [_(d6b1557)_](https://github.com/pa-decarvalho/brigade/commit/d6b155797d1db989da1597e97168506ff1c5c906)

# [0.1.1](https://github.com/pa-decarvalho/brigade/compare/0.1.0...0.1.1) - 2026-11-10

### 🐛 Bug Fixes

- run releasaurus release before release-pr (#69) [_(9cb9487)_](https://github.com/pa-decarvalho/brigade/commit/9cb9487d234974b99b9b5173343b16db42d6a5c4)

# [0.1.0](https://github.com/pa-decarvalho/brigade/releases/tag/0.1.0) - 2026-11-10

### 🚀 Features

- release with Releasaurus, deploy to publish, operate for Renovate (#65) [_(e5a60b9)_](https://github.com/pa-decarvalho/brigade/commit/e5a60b921442a00781670f0af3b149de3430f168)

- replace the CI plan job with per-stage commands in mise (#63) [_(4e72fe8)_](https://github.com/pa-decarvalho/brigade/commit/4e72fe8fea145579cf1ca97cd4543fb1c64e8f76)

- pick tools in one list, with <tool>:<action> tasks (#61) [_(9476e15)_](https://github.com/pa-decarvalho/brigade/commit/9476e15ba77fab12042ad930d4d54f9459c9bad3)

- add taplo, renovate, ctt and ci-local to the catalog (#58) [_(e30c929)_](https://github.com/pa-decarvalho/brigade/commit/e30c9298c8df71c19571c07586146e5266b95967)

- add the deploy stage with Zensical and Pages (#57) [_(15a7f10)_](https://github.com/pa-decarvalho/brigade/commit/15a7f104f85afe85b57900171675178dbbd6bfc0)

- customize tool versions and commands per tool (#56) [_(f2ef96b)_](https://github.com/pa-decarvalho/brigade/commit/f2ef96b7b2bcae6c7d04609c9be05bfe773e5790)

- add build and release stages (#55) [_(ab886c1)_](https://github.com/pa-decarvalho/brigade/commit/ab886c1bff3e42b171a7f36531a6c2e12582b7ad)

- pick tools per stage, with languages as presets (#53) [_(8e5e496)_](https://github.com/pa-decarvalho/brigade/commit/8e5e49626ca7449e28d4ccd7a308c8fbaa87d49a)

- brigade-owned CI with user-owned ci.toml and custom.yml (#51) [_(00c9da2)_](https://github.com/pa-decarvalho/brigade/commit/00c9da22e4bd3db50cd7af7242e4297b7ee99d99)

- add optional mirrors for corporate networks (#47) [_(dbb3460)_](https://github.com/pa-decarvalho/brigade/commit/dbb3460da94cc3bc8ee3d5a150bc4f800ed1aedf)

- add a Gitea/Forgejo CI option (#46) [_(4f320c9)_](https://github.com/pa-decarvalho/brigade/commit/4f320c92e0d955b6256aa8b632e54d300967d77f)

- move GitLab CI jobs to .gitlab/ci/ and rename the Copier answers file (#44) [_(23f3444)_](https://github.com/pa-decarvalho/brigade/commit/23f3444eadfdae4f92032853c8d236ab1e2aacc3)

- add a rust project type (#42) [_(976e047)_](https://github.com/pa-decarvalho/brigade/commit/976e047ebde11ce02e03aa94d4d25aaf1c57ce8e)

- add a git pre-commit hook that runs mise run lint [_(9afe0b8)_](https://github.com/pa-decarvalho/brigade/commit/9afe0b8a49f0266f5083ad9f20908752e02d2207)

- add gitleaks and typos to the common lint stage [_(fd418e6)_](https://github.com/pa-decarvalho/brigade/commit/fd418e60d6b5988d02419ae3b066c851417235c6)

- run Renovate weekly in a GitHub Actions workflow [_(3da812a)_](https://github.com/pa-decarvalho/brigade/commit/3da812ad700cebf20c368f0638d972bcc48d4379)

- keep pinned versions up to date with Renovate [_(0ede0bd)_](https://github.com/pa-decarvalho/brigade/commit/0ede0bd7212cc7c4116928ee4279cfd9d583cd93)

- release brigade with release-please [_(f600048)_](https://github.com/pa-decarvalho/brigade/commit/f6000484cc8803fbdd6f4b41a7876b213e3f2bbd)

- init project [_(89905d7)_](https://github.com/pa-decarvalho/brigade/commit/89905d7313ac1c332783c4003fc3fd5bb47d4878)

### 🐛 Bug Fixes

- ignore Copier answers in typos and time out CI jobs [_(49731a6)_](https://github.com/pa-decarvalho/brigade/commit/49731a61f29a0c022551001a57166b0769a18bd0)

- _(deps)_ update template [_(1845b42)_](https://github.com/pa-decarvalho/brigade/commit/1845b42494bbb1ac6169e975a06f8289f95e435d)

- work around ctt git archive failure on Windows [_(91a6aa3)_](https://github.com/pa-decarvalho/brigade/commit/91a6aa35db1d5599e2021a5cbcf27b388de804fe)

- name GitHub releases X.Y.Z without the v prefix [_(b08c141)_](https://github.com/pa-decarvalho/brigade/commit/b08c14124b44dc8258ad0a430eb76bb45fbe435b)

- start releases at 0.1.0 [_(93536cf)_](https://github.com/pa-decarvalho/brigade/commit/93536cf0b2e19c3570831e80fec598eeb0893748)

### 📚 Documentation

- add a Zensical documentation site (#50) [_(0c34103)_](https://github.com/pa-decarvalho/brigade/commit/0c341033a4a2a48e10297d6005aded76080200aa)

- add CLAUDE.md with project principles [_(6fbc728)_](https://github.com/pa-decarvalho/brigade/commit/6fbc72802c9aaedfb2de60da02a1a290d717a142)

### 🧪 Testing

- run the generated CI of every variant and split brigade's CI jobs (#45) [_(cdbff81)_](https://github.com/pa-decarvalho/brigade/commit/cdbff81785921c0e08b7de097bbbba2149d661f8)

- check copier update from the latest release [_(0d696f3)_](https://github.com/pa-decarvalho/brigade/commit/0d696f3a4358f10d7cb19f09e4ada32ecf789620)

### 🧹 Chore

- _(main)_ release 0.10.0 (#66) [_(5082bf8)_](https://github.com/pa-decarvalho/brigade/commit/5082bf869567702a0415e569039daf33946ffa74)

- _(main)_ release 0.9.0 (#64) [_(bebeb83)_](https://github.com/pa-decarvalho/brigade/commit/bebeb8322fa742fd0c6090013e69d498442b5ef7)

- _(main)_ release 0.8.0 (#62) [_(267e13f)_](https://github.com/pa-decarvalho/brigade/commit/267e13f288dff2d447b9c6b7a2f755555ed3b373)

- _(main)_ release 0.7.0 (#59) [_(baef8bd)_](https://github.com/pa-decarvalho/brigade/commit/baef8bdbcc81499c5a0b9d8981560aebf4847cda)

- _(main)_ release 0.6.0 (#54) [_(b91ee0f)_](https://github.com/pa-decarvalho/brigade/commit/b91ee0f994f1f4c1988183c1abf920feaaa550fb)

- _(main)_ release 0.5.0 (#52) [_(f3d9d85)_](https://github.com/pa-decarvalho/brigade/commit/f3d9d85d18fc79956d6d65df136d3e407e13a793)

- _(main)_ release 0.4.0 (#43) [_(edb8a79)_](https://github.com/pa-decarvalho/brigade/commit/edb8a79c82591523faa41ce2e2921363daf21621)

- _(main)_ release 0.3.0 (#38) [_(9099b52)_](https://github.com/pa-decarvalho/brigade/commit/9099b52fa3805307b1f4002184bad87a27e658d1)

- _(main)_ release 0.2.1 [_(fc6f5fe)_](https://github.com/pa-decarvalho/brigade/commit/fc6f5fe12bb2c735247dc67b06e1dac0fb3d1300)

- _(deps)_ update tooling [_(b080c91)_](https://github.com/pa-decarvalho/brigade/commit/b080c91905e3fe08f82553d3e95fdf3532db2cb5)

- split Renovate updates into template and tooling groups [_(1ff1606)_](https://github.com/pa-decarvalho/brigade/commit/1ff16065bb9a2b94ba11db03dbd8734e1936db63)

- group Renovate updates in one PR and drop the dashboard [_(8190551)_](https://github.com/pa-decarvalho/brigade/commit/8190551ce7bb47ce172fb218696e8b1b917c1d44)

- _(main)_ release 0.2.0 [_(e70f07c)_](https://github.com/pa-decarvalho/brigade/commit/e70f07c0d8a0715c5face33f0825482ed7477d7a)

- _(main)_ release 0.1.1 [_(b70f2f2)_](https://github.com/pa-decarvalho/brigade/commit/b70f2f2c7ae8a71dab56136ad996aaf7177b2b58)

- _(main)_ release 0.1.0 [_(ac3f15a)_](https://github.com/pa-decarvalho/brigade/commit/ac3f15a9d8a64f88b490f3b325a915d0832e66f3)

- tag releases as X.Y.Z without the v prefix [_(a638ab5)_](https://github.com/pa-decarvalho/brigade/commit/a638ab54c173d33fece8306f3c1958d74f43ddb3)

- fix ci tests triggers 2 times [_(1e2e6b7)_](https://github.com/pa-decarvalho/brigade/commit/1e2e6b790529ea55320ecd7688acd4903a8a19d7)

- change new-lines yamllint rule in template [_(3cf0dbb)_](https://github.com/pa-decarvalho/brigade/commit/3cf0dbb441cf8beda7ca252c66491a1f630e38c9)

- add claude settings.json [_(7c9e7e5)_](https://github.com/pa-decarvalho/brigade/commit/7c9e7e52555f522a6da4602bfbd5bc4a2751b242)

- add editorconfig [_(6bb738c)_](https://github.com/pa-decarvalho/brigade/commit/6bb738c468f91fb8618ffc40b1904c6808ae241e)

- change CLAUDE.md [_(30c76c6)_](https://github.com/pa-decarvalho/brigade/commit/30c76c66f151b9f458fdf67ce93dda666fbde773)

### ⏩ CI/CD

- release brigade with Releasaurus (#67) [_(73f90c5)_](https://github.com/pa-decarvalho/brigade/commit/73f90c5480d1bff88f5b15b17743326bda8b994a)
