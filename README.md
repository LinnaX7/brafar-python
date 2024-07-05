# BRAFAR: Bidirectional Refactoring, Alignment, Fault Localization, and Repair for Programming Assignments
## What is BRAFAR
BRAFAR is a general feedback generation system for introductory programming assignments (IPAs). It takes three inputs: a buggy program $P_b$, (one or more) correct programs $C$, and test cases $T$. Initially, It searches for the closest program $P_c$ as a repair reference. Subsequently, It uses the closest program correct program $P_c$ to repair the given buggy program $P_b$.

If $P_b$ and $P_c$ share different control-flow structures, we will use a novel **bidirectional refactoring** algorithm to align their control-flow structures. After that, we use three major components to generate feedback for the given buggy program $P_b$: (1) **Aligner**, aligns the basic blocks and variables between the buggy program and the reference program. (2) **Fault Locator**, locates the suspicious basic block of the buggy program in a coarse-to-fine manner. And (3) **Repairer**, takes the suspicious basic block and its corresponding basic block in the correct program as input, and outputs block repairs. Notably, the fault localization and block repair will be repeatedly conducted until the generated program passes all the test suites.                    

## About

This is an implementation of the brafar-python tool for Python introductory programming assignments.


## Setup

### Operation System

The package is currently supported/tested on the following operating systems:

- Ubuntu
- MacOS

### Install Python packages

The package is currently supported/tested on the following Python versions:

- python3

```
sudo apt-get install python3 python3-pip
```

- zss

```
pip3 install zss
```

- timeout_decorator

```
pip3 install timeout_decorator
```

### Docker environment

As an alternative to setting up the Python packages manually, the same environment can be obtained by building a docker image based on `Dockerfile`.

```
docker build -t brafar-python .
```

## Running brafar-python

Brafar-python tool is invoked using the command line interface offered by `brafar-python/run.py`. For example, the below command runs brafar-python on the target buggy program of `question_1` in the `./example` directory, with 100% sampling rate of correct programs.

```
python3 brafar-python/run.py ./dara -q question_1 -s 100
```

### The command line arguments

- `-d` flag specifies the path of the data directory.
- `-q` flag specifies the question (folder) name within the data directory.
- `-s` flag specifies the sampling rate.

### Output

After the completion of a run by Refactory tool, the intermediate results such as repaired program, time-taken, relative patch size, etc are logged into a csv file ./data/question_x/brafar_result_*.csv. Where, * is the sampling rate of correct programs.
