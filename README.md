# Ultimate Agents Hackathon

This project is our submission for the Ultimate Agents Hackathon, the biggest hackathon yet in London. We are building with cutting-edge AI agent tools to compete for fun, and to learn.

## The Team

- Hans
- Claude
- Spyros
- Callum

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
Relying on the remote CI pipeline to check your code leads to slow development iteration. Locally, you can trigger:

- linting & formatting checks : `poetry run pre-commit run --all-files`
- tests: `poetry run pytest tests/`

## Streaming Client

This project includes a Dedalus streaming client that connects to a WebSocket server.

### Running the Example

1.  **Start the server:** The included server in `src/Dedalus/src/server.ts` is configured to listen for WebSocket connections. To start it, navigate to the `src/Dedalus` directory and run:
    ```bash
    npm install
    npm run build
    npm start
    ```
2.  **Run the client:** In a separate terminal, navigate to `src/Dedalus` and run the example client:
    ```bash
    node dist/streaming-client-example.js
    ```

The client will connect to the server, send a dummy audio chunk, and close the connection.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. It also includes a custom license in [LICENSE.txt](LICENSE.txt).