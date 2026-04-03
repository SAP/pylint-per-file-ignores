# Changelog

<!-- towncrier release notes start -->

## 3.2.1 (2026-04-03)

### Fixes

- Fixed an issue causing configuration parsing issues if trailing commas are used when `setup.cfg`
  or `.pylintrc` is used
- Fixed an issue causing configuration parsing issues with multiple patterns when `setup.cfg`
  or `.pylintrc` is used


## 3.2.0 (2025-11-25)

* Updated the release actions

## 3.1.0
- Support pylint 4.x

## 3.0.0
- Removed support for python 3.9

## 2.0.3
- Make glob patterns recursive

## 2.0.2
- Fixed version mismatch

## 2.0.1
- Fixed project classifiers

## 2.0.0
- Dropped support for pylint versions below 3.3
- Officially support python 3.9-3.14
- Dropped support for python 3.8 and before
- Complete refactoring of the project
- Dropped support for the custom pyproject.toml section
- Support parallel mode of pylint
- Switch from regex patterns to globs
