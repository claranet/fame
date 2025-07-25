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
