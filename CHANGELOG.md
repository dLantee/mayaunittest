# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Add example to /test/test_sample.py .
- Commandline option `--maya-app-dir` to specify a custom Maya application directory. If not provided or doesn't exist, a temporary clean one will be generated.
- Commandline option `--packages` to specify multiple Maya modules/packages containing tests.
- Commandline option `--pause` to pause the Maya session after tests complete for inspection.
- Commandline option `--maya` to specify the Maya version to use (e.g., 2022, 2023, 2024, 2025, 2026).

### Changed
- Updated README with new commandline options and examples.
- Renamed /bin/runmoduletests.py to /bin/run_maya_tests.py for clarity.

