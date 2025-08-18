[![REUSE status](https://api.reuse.software/badge/github.com/SAP/pylint-per-file-ignores)](https://api.reuse.software/info/github.com/SAP/pylint-per-file-ignores)


# Pylint Per File Ignores 😲

This pylint plugin will enable per-file-ignores in your project!

The project was initaly created by [christopherpickering](https://github.com/christopherpickering).
Please stay tuned for fixes, feature, etc. in the next months but please give me some time to board on :).

## Install

```
# w/ poetry
poetry add pylint-per-file-ignores --group dev

# w/ pip
pip install pylint-per-file-ignores
```

## Add to Pylint Settings

```toml
[tool.pylint.MASTER]
load-plugins=[
    "pylint_per_file_ignores",
    ...
]
```


## Usage

Add list of patterns and codes you would like to ignore.

### Using native pylint settings

Section "MESSAGES CONTROL". Examples:

```ini
# .pylintrc

[MESSAGES CONTROL]
per-file-ignores =
  .*_test\.py:protected-access # ignore "protected-access" errors in test files ending in "_test.py"
```

```ini
# setup.cfg

[pylint.MESSAGES CONTROL]
per-file-ignores =
  /folder_1/:missing-function-docstring,W0621,W0240,C0115
  file.py:C0116,E0001
```

```toml
# pyproject.toml

[tool.pylint.'messages control']
per-file-ignores = [
    "/folder_1/:missing-function-docstring,W0621,W0240,C0115",
    "file.py:C0116,E0001"
]
```

### Using custom `pyproject.toml` section

For backwards compatibility only. Example:

```toml
[tool.pylint-per-file-ignores]
"/folder_1/"="missing-function-docstring,W0621,W0240,C0115"
"file.py"="C0116,E0001"
```

## Thanks

To pylint :) And the plugin `pylint-django` who produced most of the complex code.

## Support, Feedback, Contributing

This project is open to feature requests/suggestions, bug reports etc. via [GitHub issues](https://github.com/SAP/pylint-per-file-ignores/issues). Contribution and feedback are encouraged and always welcome. For more information about how to contribute, the project structure, as well as additional contribution information, see our [Contribution Guidelines](CONTRIBUTING.md).

## Security / Disclosure
If you find any bug that may be a security problem, please follow our instructions at [in our security policy](https://github.com/SAP/pylint-per-file-ignores/security/policy) on how to report it. Please do not create GitHub issues for security-related doubts or problems.

## Code of Conduct

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone. By participating in this project, you agree to abide by its [Code of Conduct](https://github.com/SAP/.github/blob/main/CODE_OF_CONDUCT.md) at all times.

## Licensing

Copyright 2025 SAP SE or an SAP affiliate company and pylint-per-file-ignores contributors. Please see our [LICENSE](LICENSE) for copyright and license information. Detailed information including third-party components and their licensing/copyright information is available [via the REUSE tool](https://api.reuse.software/info/github.com/SAP/pylint-per-file-ignores).
