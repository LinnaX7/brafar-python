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

After the completion of a run by BRAFAR tool, the intermediate results such as refactored buggy program, refactored correct program, repaired program, time-taken (e.g. search time, bidirectional refactoring time, total time), relative patch size, etc are logged into a csv file `./data/question_x/brafar_result_*.csv`, where * is the sampling rate of correct programs.

## Comparison Evaluation

### Reproduce the [Refactory](https://github.com/githubhuyang/refactory) tool

Run the Refactory tool following its instructions. The results will be logged into a CSV file located at `data/question_x/refactory_online.csv`.

### Reproduce the [CLARA](https://github.com/iradicek/clara) tool 

We cannot directly run the CLARA tool on the dataset due to the following challenges:

* The CLARA tool only provides command-line usage for repairing a single buggy program.
* The output of the CLARA tool is only feedback on different statement changes, not the repaired code.
* The patch size calculated by the CLARA tool differs from that of the Refactory and our BRAFAR tool.
* The CLARA tool does not output the repair time.
* The CLARA tool encounters exceptions when clustering the correct programs in our dataset.

Therefore, we forked the [CLARA](https://github.com/iradicek/clara) code repository and made necessary modifications to the CLARA tool. You can access it at https://github.com/LinnaX7/clara.
The code modifications include the following aspects:

To address the different patch size calculation challenge, we modified the patch size calculation to match that of the Refactory and our BRAFAR tool.
To improve exception handling, we added exception handling to the CLARA tool, enabling it to cluster the correct programs in our dataset.
To resolve the output challenge, we enhanced the output to include the repair time and the patch size.
To overcome the command-line usage limitation, we added functionality for repairing a set of buggy programs, which logs the running results into a CSV file located at `data/question_x/clara_result_*.csv`, where * is the entryfunc.

#### preprocessing the CLARA result
CLARA repairs the program within an entry function separately. We need to integrate its running results, calculate the overall repair time and overall relative patch size, and store it in `data/question_x/clara_result.csv`.

### Comparison Evaluation
After running the BRAFAR tool, the [Refactory](https://github.com/githubhuyang/refactory) tool, and the [CLARA](https://github.com/LinnaX7/clara) tool. You can find their running results in `brafar_result_100.csv`, `refactory_online.csv` and `clara_result.csv` located in `data/question_x`.

#### evaluate.py

`evaluate.py` provides different interface implementations to analyze and compare their running results.

#### The command line arguments
- `-d` flag specifies the path of the data directory.
- `-e` flag specifies the evaluation targets.

#### Overall Comparison

```python evaluate.py -d ./data -e OverallComparison```

This function compares the running time and average RPS of the BRAFAR tool, the Refactory tool, and the CLARA tool, see Section 4.2.

```python evaluate.py -d ./data -e RandomComparison```

This will get the random selected buggy programs and the repaired results of the BRAFAR tool, the Refactory tool, and the CLARA tool, see Section 4.2.3.

#### Bidirectional Refactoring Evaluation

```python evaluate.py -d ./data -e BidirectionalRefactoring```

This function compares the structural alignment between the BRAFAR tool and the Refactory tool, see Section 4.3. 

#### Repair Strategy Evaluation

```python evaluate.py -d ./data -e CompareRepairStrategy```

This function compares the repair strategy between the BRAFAR tool and the Refactory tool, see Section 4.4. 

## ChatGPT Repair Result

`ChatGPT4_RepairResult.zip` stores the repair results during the experiment by querying ChatGPT4 the following three queries:

* Repair the following incorrect code ${P}_b$ with minimal modifications.
* Repair the following incorrect code ${P}_b$ with minimal modifications along with the test cases $T$.
* Repair the following incorrect code ${P}_b$ with minimal modifications along with the reference correct code ${P}_c$.
