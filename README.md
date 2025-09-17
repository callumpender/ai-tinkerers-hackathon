# faculty_ai_tinkerers_hackathon

A short description of your project goes here...

## Description

A longer description of your project goes here...

## Getting started
This project makes use of `pyenv` for python version management and `poetry` for virtual environment/ dependency management. To get started with these tools, you can refer to [Python dev](https://www.notion.so/facultyai/Tips-and-tricks-027fd336f3b34e3ba4f487899826bb12?pvs=4) in Notion.

```bash
#Clone the repository using your preferred method(SSH vs HTTPS)
git clone <repo_url>
cd <repo>
```
```bash
#Create the poetry virtual environment (if you don't have a compatible version of python on your system
#you might have to install it !!Danger platform user see pyenv in Notion above!!)
poetry install
```
```bash
#you can now run all packages installed such as pre-commit, ruff and pytest using
poetry run <package>
```

Note `poetry shell` has been deprecated in 2.0.0, use `eval $(poetry env activate)` to create a poetry shell.

## Local development
 Relying on the remote CI pipeline to check your code leads to slow development  iteration. Locally, you can trigger:

 - linting & formatting checks : `poetry run pre-commit run --all-files`
 - tests: `poetry run pytest tests/`


## Note

This project has been setup using Faculty's [consultancy-cookie](https://gitlab.com/facultyai/faculty-tools/consultancy-cookie).
