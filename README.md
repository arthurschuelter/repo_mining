
# Assessment 01 - MO630 A - Replication Package

* Chosen topic: **Mining Deployment Tasks in Software Repositories (MSR)**

## Group A
* Arthur Felipe Herdt Schuelter
* José Augusto Nascimento Afonso Marcos
* Nicolas Guilhermo Silva Moliterno

## Run instructions
* To run the complete pipeline with data from March-2026:
```bash
python main.py --repos_csv repos.csv --output_dir ./outputs
```

* To run the post-processing script and generate graphics
```bash
python charts.py evidence.csv repo_summary.csv
```

## Default data
* You can find our default data for the project at `./outputs` folder. Also, our final list of repositories can be found at `repos.csv` file.