# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                               |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|----------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| llm\_ci\_runner/\_\_init\_\_.py    |       20 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/core.py            |       65 |        9 |        6 |        2 |     84.51% |105, 123, 154-161, 174-175, 177-178 |
| llm\_ci\_runner/exceptions.py      |       10 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/io\_operations.py  |      159 |        4 |       56 |        2 |     97.21% |106, 162-163, 387 |
| llm\_ci\_runner/llm\_execution.py  |       63 |        0 |       14 |        0 |    100.00% |           |
| llm\_ci\_runner/llm\_service.py    |       84 |        0 |       20 |        0 |    100.00% |           |
| llm\_ci\_runner/logging\_config.py |       17 |        0 |        2 |        0 |    100.00% |           |
| llm\_ci\_runner/schema.py          |       22 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/templates.py       |       97 |        0 |       16 |        0 |    100.00% |           |
|                          **TOTAL** |  **537** |   **13** |  **114** |    **4** | **97.39%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/Nantero1/ai-first-devops-toolkit/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Nantero1/ai-first-devops-toolkit/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FNantero1%2Fai-first-devops-toolkit%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.