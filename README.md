# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                               |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|----------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| llm\_ci\_runner/\_\_init\_\_.py    |       21 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/core.py            |      318 |       44 |      114 |       15 |     84.49% |211->225, 218->225, 299-304, 364-390, 438->441, 540, 647, 673-675, 683-687, 688->694, 702-703, 709->718, 749-751, 780, 795, 811-816, 875-883 |
| llm\_ci\_runner/exceptions.py      |       10 |        0 |        0 |        0 |    100.00% |           |
| llm\_ci\_runner/formatters.py      |      119 |        0 |       42 |        0 |    100.00% |           |
| llm\_ci\_runner/io\_operations.py  |      137 |        3 |       50 |        2 |     97.33% |106, 158->181, 178-179 |
| llm\_ci\_runner/llm\_execution.py  |      194 |       10 |       50 |       11 |     90.57% |20, 88->97, 124, 126, 165, 273-274, 289-290, 358-359, 364->355, 517->535, 519->517 |
| llm\_ci\_runner/llm\_service.py    |       74 |        0 |       18 |        0 |    100.00% |           |
| llm\_ci\_runner/logging\_config.py |       17 |        0 |        2 |        0 |    100.00% |           |
| llm\_ci\_runner/retry.py           |       72 |        0 |       20 |        0 |    100.00% |           |
| llm\_ci\_runner/schema.py          |      111 |       10 |       64 |        7 |     86.86% |97->101, 143, 159->180, 166->172, 191, 199-201, 234-238 |
| llm\_ci\_runner/templates.py       |      123 |        0 |       22 |        0 |    100.00% |           |
| **TOTAL**                          | **1196** |   **67** |  **382** |   **35** | **92.52%** |           |


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