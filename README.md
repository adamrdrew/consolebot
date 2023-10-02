# ConsoleBot - GitHub Repository Assistant

ConsoleBot is a CLI tool designed to assist developers in fetching summarized information about ConsoleDot (RedHatInsights) GitHub repositories based on natural language queries.

## Features

- Quickly retrieve summaries of repositories.
- Fetch recent activities of a repo.
- List contributors.
- Identify the languages a repository is written in.
- Uses fuzzy matching to identify repositories based on partial names or related terms.
- Smart intent recognition to understand your queries.
- Elegant display of results using the `rich` library.

## Installation

To get started, clone the repository:

```bash
git clone https://github.com/adamrdrew/consolebot.git
cd consolebot
```

Then, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Using ConsoleBot is simple. After installation, navigate to the project directory and execute the CLI tool:

```bash
python consoledot.py tell me about clowder
```

Example queries:

- whats new in clowder
- who works on chrome
- tell me about the frontend operator

## Development

ConsoleBot leverages multiple libraries like `spacy`, `fuzzywuzzy`, `nltk`, and `rich` to provide natural language processing capabilities and to display results beautifully.

For developers wanting to understand the code, here's a high-level overview:

- `determine_repo_name()`: Identifies the repository's name from the query.
- `determine_intent()`: Determines the user's intention (summary, contributors, languages, recent activities).
- Handlers for each intent like `get_summary()`, `get_recent_activity()`, etc.
- CLI interface using the `click` library for easy user interaction.

## Troubleshooting

If you encounter any issues, ensure:

1. All required packages are installed.
2. You've downloaded the necessary NLTK datasets using the commands provided in the main project file.

For further help, raise an issue on the GitHub repository.

## Contributing

Contributions to ConsoleBot are welcome. Fork the repository, make your changes, and submit a pull request.

## License

ConsoleBot is licensed under the MIT License. See `LICENSE` for more details.

---

Created with ❤️ 