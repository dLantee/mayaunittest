# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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


[0.0.1]: 

[4]: https://github.com/dLantee/mayaunittest/issues/4