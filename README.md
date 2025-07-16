# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                               |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|----------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| llm\_ci\_runner/\_\_init\_\_.py    |       21 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/core.py            |       89 |       10 |       16 |        2 |     88.57% |113, 128, 192-199, 205, 221-222, 224-225 |
| llm\_ci\_runner/exceptions.py      |       10 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/formatters.py      |      115 |        2 |       40 |        2 |     97.42% |  125, 268 |
| llm\_ci\_runner/io\_operations.py  |      132 |        6 |       44 |        2 |     95.45% |106, 162-163, 342, 354-355 |
| llm\_ci\_runner/llm\_execution.py  |      199 |        4 |       52 |        9 |     94.82% |20, 87->96, 122, 124, 163, 343->340, 349->340, 551->569, 553->551 |
| llm\_ci\_runner/llm\_service.py    |       72 |        0 |       18 |        0 |    100.00% |           |
| llm\_ci\_runner/logging\_config.py |       17 |        0 |        2 |        0 |    100.00% |           |
| llm\_ci\_runner/schema.py          |      119 |       14 |       64 |        7 |     87.43% |97->101, 159->180, 166->172, 168-169, 176-177, 191, 199->207, 200->199, 203-204, 234-238, 244-245 |
| llm\_ci\_runner/templates.py       |      103 |        3 |       18 |        1 |     96.69% |     91-93 |
|                          **TOTAL** |  **877** |   **39** |  **254** |   **23** | **94.34%** |           |


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