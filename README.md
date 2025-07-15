# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                               |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|----------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| llm\_ci\_runner/\_\_init\_\_.py    |       20 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/core.py            |       89 |       10 |       16 |        2 |     88.57% |113, 128, 193-200, 206, 222-223, 225-226 |
| llm\_ci\_runner/exceptions.py      |       10 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/io\_operations.py  |      160 |        6 |       56 |        2 |     96.30% |106, 162-163, 389, 401-402 |
| llm\_ci\_runner/llm\_execution.py  |      186 |        4 |       52 |        9 |     94.54% |22, 89->98, 162, 164, 203, 217->214, 223->214, 497->515, 499->497 |
| llm\_ci\_runner/llm\_service.py    |       84 |        0 |       20 |        0 |    100.00% |           |
| llm\_ci\_runner/logging\_config.py |       17 |        0 |        2 |        0 |    100.00% |           |
| llm\_ci\_runner/schema.py          |      116 |       14 |       62 |        7 |     87.08% |94->98, 156->177, 163->169, 165-166, 173-174, 188, 196->204, 197->196, 200-201, 231-235, 241-242 |
| llm\_ci\_runner/templates.py       |       97 |        0 |       16 |        0 |    100.00% |           |
|                          **TOTAL** |  **779** |   **34** |  **224** |   **20** | **94.42%** |           |


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