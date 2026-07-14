# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.2.0] - 2026-07-14

### Added
- `mayaunittest` console-script entry point (installed via `pip install .`), replacing the
  old `bin/run_maya_tests.py` script.
- `--test` commandline option to run a single test module/class/method instead of
  discovering a whole package's tests.
- Pytest-based unit tests (`tests_cli/test_cli.py`) for the Maya-independent CLI helper
  functions.

### Changed
- Restructured `bin/run_maya_tests.py` into `python/cli.py` as part of the installable
  package, and renamed `maya_installs.json` to `custom_installs.json` (now at the repo root).
- `--maya_installs` now defaults to the repo-root `custom_installs.json`.
- `MAYA_LOCATION` is now restored to its previous value after a run instead of being left
  permanently overwritten in the process environment.
- Updated README to match the actual CLI flags and removed references to the old
  `bin/run_maya_tests.py` script.

### Fixed
- Fixed `mayaunittest.py` crashing on import and a duplicate/broken `run_tests()`
  definition, both introduced during the `bin/` -> `python/` refactor.
- Fixed `pyproject.toml` packaging so `cli.py`/`mayaunittest.py` are actually included in
  the installed package (`py-modules`).
- Fixed a broken assertion in `tests/test_sample.py`.

## [0.1.3] - 2026-02-03

### Changed
- Fixed version in pyproject.toml.


## [0.1.2] - 2026-02-03

### Added
- Added more code examples to README. ([#11])
- Added wallpaper picture to README.

### Changed
- CHANGELOG cleanup and formatting.


## [0.1.1] - 2026-02-03

### Changed
- Set default value if `--maya` flag not set.
- Improved error handling and messages when Maya executable cannot be found.
- Updated `README` with `Howto` and clarifications.


## [0.1.0] - 2026-02-01

### Added
- maya_installs.json example file for custom Maya installation look up map. ([#2])
- Commandline option `--maya-path` to specify a custom Maya installation path. ([#2])
- Commandline option `--maya-installs` to specify a custom Maya installation look up map. ([#2])

### Changed
- README with new commandline options and examples.
- Changed priority of Maya executable resolution to:


## [0.0.1] - 2026-01-31

### Added
- Add example to /test/test_sample.py .
- Commandline option `--clean-maya-app-dir` to generate a temporary clean Maya application directory.
- Commandline option `--packages` to specify multiple Maya modules/packages containing tests.
- Commandline option `--pause` to pause the Maya session after tests complete for inspection.
- Commandline option `--maya` to specify the Maya version to use (e.g., 2022, 2023, 2024, 2025, 2026).

### Changed
- Updated README with new commandline options and examples.
- Renamed /bin/runmoduletests.py to /bin/run_maya_tests.py for clarity.
- Changed default behavior to generate a temporary clean Maya application directory if the specified one does not exist. ([4])

### Removed
- Removed Settings from README as it requires further development.




[#2]: https://github.com/dLantee/mayaunittest/issues/2
[#4]: https://github.com/dLantee/mayaunittest/issues/4
[#11]: https://github.com/dLantee/mayaunittest/issues/11