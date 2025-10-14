## Evaluation
This directory contains the data and source code used to evaluate our system. `e2e` contains data for evaluating the end-to-end system, and `te` contains data for evaluating the text extraction module only. The source code for the evaluation can be found in `src`.

## Requirements

To run the evaluation code, you must first generate the prediction files by running our system. For end-to-end system, please run `src/driver.py` as described in the README located in the base directory. For the baseline system, please run `baseline/src/main.py`. For text extraction module, please run `frontend/text2extractions/src/main.py` as described in the README located in the `frontend/text2extractions` directory.

## Run the code

After generating the prediction files, update the file paths in the evaluation source code to match your actual input and output locations:

- End-to-End System & Baseline: Edit the paths in `compute_accuracy.py`.
- Text Extraction Module: Edit the paths in `te_evaluator.py`.

Once the paths are updated, you can proceed to run the evaluation. To run the evaluations, use the following commands after updating the file paths as described above.

- End-to-end or baseline evaluation:

```
python3 compute_accuracy.py <root_folder>
```

- Text extraction module evaluation:

```
python3 te_evaluator.py
```

## Contact

If you have any questions about the data or the codes, please contact Alice (alicekwak@arizona.edu) or file a GitHub issue.