## 2.0.3 (2025-08-29)

### Bug Fixes

* **deps:** update dependency azure-identity to v1.24.0 8c4379d
* **deps:** update dependency datadog to ^0.52.0 938cd1d

### Code Refactoring

* **metrics:** replace SignalFx lib by api calls bb40990

### Continuous Integration

* update release config 2e3994e

### Miscellaneous Chores

* **deps:** update actions/checkout action to v5 0cd43f2
* **deps:** update actions/setup-python action to v5 aef4512
* **deps:** update dependency claranet/guildes/pipeline/python-templates/python-gitlab-ci-templates to v0.18.0 9a74caa
* **deps:** update dependency pre-commit to v4.3.0 216a319
* **deps:** update dependency pytest to v8.4.1 00374cb
* **deps:** update dependency ruff to ^0.12.0 231aafe
* **deps:** update dependency tox to v4.28.4 a9828fe
* **deps:** update pre-commit hook asottile/add-trailing-comma to v3.2.0 f810bbc
* **deps:** update pre-commit hook astral-sh/ruff-pre-commit to v0.12.10 ddbcdd4
* **deps:** update pre-commit hook astral-sh/ruff-pre-commit to v0.12.11 dcdcc22
* **deps:** update pre-commit hook compilerla/conventional-pre-commit to v4.2.0 e357133
* **deps:** update pre-commit hook editorconfig-checker/editorconfig-checker.python to v3.4.0 5b89c80
* **deps:** update pre-commit hook pre-commit/pre-commit-hooks to v6 2012daf
* **deps:** update pre-commit hook tox-dev/tox-ini-fmt to v1.6.0 cd711fb
* improve logging and exception handling 0848f00

## 2.0.2 (2025-08-26)

### Bug Fixes

* **deps:** update dependency requests to v2.32.5 7a71586

## 2.0.1 (2025-08-25)

### Bug Fixes

* **deps:** update dependency cryptography to v45.0.6 884a7c0

### Miscellaneous Chores

* **deps:** update dependency pyright to v1.1.404 7e6e12c

## 2.0.0 (2025-06-27)

### ⚠ BREAKING CHANGES

* datadog support

### Features

* datadog support 3aff5c6
* python 3.11 support 609d6c0
* python 3.12 0d63297
* use poetry 32816df

### Bug Fixes

* try fix up things 9a059d6

### Documentation

* update documentation with datadog support 705e173
* update README d24a425

### Code Refactoring

* move code to src 7b37e0b

### Continuous Integration

* disable image build d6e8b4d
* disable pyright b805dbb
* fix semantic release 2e2c3db
* get rid of function core tools 6b0643f
* update semantic release configuration c1fc6c0

### Miscellaneous Chores

* back to python 3.10 e170e0e
* bump dependencies a2a8d03
* bump dev dependencies 43851a2
* code cleanup 4b38fe3
* **deps:** add renovate.json f69d227
* **deps:** update actions/checkout action to v4 6aae41f
* **deps:** update dependency azure-common to v1.1.28 f9ca65f
* **deps:** update dependency azure-core to v1.30.2 03c1970
* **deps:** update dependency azure-identity to v1.16.1 6df31d8
* **deps:** update dependency azure-loganalytics to v0.1.1 ae26c64
* **deps:** update dependency certifi to v2024.6.2 69ec54d
* **deps:** update dependency cryptography to v3.4.8 00cd3e3
* **deps:** update dependency cryptography to v42.0.8 0eaf8e1
* **deps:** update dependency idna to v3.7 757bcb3
* **deps:** update dependency isodate to v0.6.1 fd741cf
* **deps:** update dependency msal to v1.28.1 c0309ac
* **deps:** update dependency msal-extensions to v0.3.1 a417fb8
* **deps:** update dependency packaging to v24.1 9b50a5e
* **deps:** update dependency requests to v2.32.1 219de0a
* **deps:** update dependency requests to v2.32.3 0d64f4e
* **deps:** update dependency signalfx to v1.1.16 8caef81
* **deps:** update dependency typing-extensions to v4.12.2 561a6c3
* **deps:** update dependency urllib3 to v2.2.2 97f9857
* **deps:** update renovate.json 35b8511

# v1.2.1 - 2023-09-01

Fixed
  * AZ-1151: Fix bug related to `metric_value` and `timestamp` columns order
  * AZ-1151: Fix execution stopping when metric related exception

# v1.2.0 - 2023-06-15

Added
  * AZ-673: Resource graph querying support

# v1.1.0 - 2022-06-14

Changed
  * AZ-686: Allow sending other metrics when on query fails
  * AZ-686: Bump requirements

Fixed
  * AZ-686: Fix authentication token scope for Log Analytics

# v1.0.1 - 2022-01-14

Changed
  * AZ-663: Update README

# v1.0.0 - 2021-07-19

Added:
  * AZ-393: First version
