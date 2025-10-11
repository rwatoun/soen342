# soen342

# Team Members
| Full Name      | Username     | Student ID |
| -------------- | ------------ | ---------- |
| Marwa Hammani  | @rwatoun     | 40289362   |
| Justyne Phan   | @JustynePhan | 40278509   |
| Elif Sag Sesen | @elif5446    | 40283343   |

Must have Python installed.

- Depending on your Python version, you might have to replace the python command with python3.

- Colorama library (for colored CLI output)


After cloning the repository:

```python -m venv .venv```

```pip install -e .```

```pip install colorama```

To run the program:

```python -m EURailNetwork data/eu_rail_network.csv```

This will launch the interactive menu where you can view the network summary, search for connections, view city information, or view train details.

To run tests:

```pytest -v```

