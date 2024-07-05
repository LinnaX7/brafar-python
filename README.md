# BRAFAR: Bidirectional Refactoring, Alignment, Fault Localization, and Repair for Programming Assignments
## What is BRAFAR
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

- python3

```
sudo apt-get install python3 python3-pip
```

- install package dependencies

```
pip3 install -r requirements.txt
```



## Running BRAFAR

BRAFAR tool is invoked using the command line interface offered by `run.py`. For example, the below command runs brafar-python on the target buggy program of `question_1` in the `./data` directory, with 100% sampling rate of correct programs.

```
python3 run.py -d ./data -q question_1 -s 100
```

### The command line arguments

- `-d` flag specifies the path of the data directory.
- `-q` flag specifies the question (folder) name within the data directory.
- `-s` flag specifies the sampling rate. With -s 0 option, only the instructor provided reference program is used to repair buggy student programs. -s 100 option indicates that 100% of correct student programs (along with the instructor provided reference program) are used.

### Output

After the completion of a run by Refactory tool, the intermediate results such as repaired program, time-taken, relative patch size, etc are logged into a csv file ./data/question_x/brafar_result_*.csv. Where, * is the sampling rate of correct programs.
