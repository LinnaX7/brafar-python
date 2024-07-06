# BRAFAR: Bidirectional Refactoring, Alignment, Fault Localization, and Repair for Programming Assignments
## What is BRAFAR
[![DOI](https://zenodo.org/badge/824122847.svg)](https://zenodo.org/doi/10.5281/zenodo.12670361)
BRAFAR is a general feedback generation system for introductory programming assignments (IPAs). It takes three inputs: a buggy program $P_b$, (one or more) correct programs $C$, and test cases $T$. Initially, It searches for the closest program $P_c$ as a repair reference. Subsequently, It uses the closest program correct program $P_c$ to repair the given buggy program $P_b$.

If $P_b$ and $P_c$ share different control-flow structures, we will use a novel **bidirectional refactoring** algorithm to align their control-flow structures. After that, we use three major components to generate feedback for the given buggy program $P_b$: (1) **Aligner**, aligns the basic blocks and variables between the buggy program and the reference program. (2) **Fault Locator**, locates the suspicious basic block of the buggy program in a coarse-to-fine manner. And (3) **Repairer**, takes the suspicious basic block and its corresponding basic block in the correct program as input, and outputs block repairs. Notably, the fault localization and block repair will be repeatedly conducted until the generated program passes all the test suites.                    

## Dataset
The dataset is from [Refactory](https://github.com/githubhuyang/refactory), a large dataset which consists of 2442 correct submissions and 1783 incorrect student programs from 5 different introductory programming assignments, along with reference programs and instructor-designed test suites. 

The `data.zip` contains all the experiments data and the data files are organized in the folder structure described below.
```
|-data
    |-question_xx
    |    |-ans
    |    |   |-input_xxx.txt
    |    |   |-output_xxx.txt
    |    |   |-...
    |    |   
    |    |-code
    |    |   |-reference
    |    |   |   |-reference.py
    |    |   |
    |    |   |-correct
    |    |   |   |-correct_xx_xxx.py
    |    |   |   |-...
    |    |   |
    |    |   |-wrong
    |    |   |   |-wrong_xx_xxxx.py
    |    |   |   |-... 
    |    |   |
    |    |   |-global.py   
    |    
    |-...
```


## Setup

### Extract Dataset
`unzip data.zip`

### Operation System
The package is currently supported/tested on the following operating systems:

- Ubuntu
- MacOS

### Install Python packages

The package is currently supported/tested on the following Python versions:

- python 3.11

- install package dependencies

```
pip install -r requirements.txt
```



## Running BRAFAR

BRAFAR tool is invoked using the command line interface offered by `run.py`. For example, the below command runs brafar-python on the target buggy program of `question_1` in the `./data` directory, with 100% sampling rate of correct programs.

```
python run.py -d ./data -q question_1 -s 100
```

### The command line arguments

- `-d` flag specifies the path of the data directory.
- `-q` flag specifies the question (folder) name within the data directory.
- `-s` flag specifies the sampling rate. With -s 0 option, only the instructor provided reference program is used to repair buggy student programs. -s 100 option indicates that 100% of correct student programs (along with the instructor provided reference program) are used.

### Output

After the completion of a run by Refactory tool, the intermediate results such as refactored buggy program, refactored correct program, repaired program, time-taken (e.g. search time, bidirectional refactoring time, total time), relative patch size, etc are logged into a csv file ./data/question_x/brafar_result_*.csv. Where, * is the sampling rate of correct programs.

## Comparison Evaluation

### run evaluate.py

After running the BRAFAR tool and the [Refactory](https://github.com/githubhuyang/refactory) tool. You can get their running result in `brafar_result_100.csv` and `refactory_online.csv`.

`evaluate.py` provides different interface implementations to analyze and compare their running results.

#### Bidirectional Refactoring Evaluation

```Run evaluate.py bidirectional_refactoring_evaluation("data")```

This function compares the structural alignment between the BRAFAR tool and the Refactory tool, see Section 4.3. 

#### Repair Strategy Evaluation

```Run evaluate.py compare_repair_size("data")```

This function compares the repair strategy between the BRAFAR tool and the Refactory tool, see Section 4.4. 

## ChatGPT Repair Result

`ChatGPT4_RepairResult.zip` stores the repair results during the experiment by querying ChatGPT4 the following three queries:

* Repair the following incorrect code ${P}_b$ with minimal modifications.
* Repair the following incorrect code ${P}_b$ with minimal modifications along with the test cases $T$.
* Repair the following incorrect code ${P}_b$ with minimal modifications along with the reference correct code ${P}_c$.
