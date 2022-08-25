# Pyterrier-Search Lambda Function


Authors: Thomas Horak (thorames), Chris Lee (chrisree) & Xun Zhou (xunzhou)

This lambda function utilizes the Docker image container option in AWS to include the big dependencies (i.e. pyterrier) as the image can go upto 10GB.

## How to Run

Have Docker installed
Have AWS CLI installed (I think)

run `run_docker.bash`
deploy new lambda image from `pyterrier-search` repository on https://us-east-2.console.aws.amazon.com/lambda/home?region=us-east-2#/functions/pyterrier-search?tab=testing

You can call the lambda api using the function url https://3kgb5un3sbrqa5z2p54xkkct6a0iemkq.lambda-url.us-east-2.on.aws/ 

Requires parameters: `query`, `canvasSiteId`, and `session_id`

## Important Lambda Configurations

# environment variables

| variable | value |
| ---------| -------- | 
| BUCKET_HOME | pyterrier-indexes |
| JAVA_HOME | /var/task/amazon-corretto-11.0.15.9.1-linux-x64 |
| JVM_PATH	| /var/task/amazon-corretto-11.0.15.9.1-linux-x64/lib/server/libjvm.so | 

/var/task/ is where the libraries will be installed by Docker

# execution role

lambda-vpc-role

# memory and ephermeral storage

Higher memory = better performance, and faster runtimes
Enough ephermeral storage to hold indexes in /tmp/ folder

Current values are 3000MB and 2000MB for memory and ephemeral storage, respectively

# vpc

vpc-1d03de76 (172.31.0.0/16) | Default

# subnets

subnet-0f70b3960592997d3 (172.31.64.0/20) | us-east-2b, umdb_eb_priv_2b
subnet-028771bf0641fb2f9 (172.31.128.0/20) | us-east-2a, umdb_eb_priv_2a
subnet-0ca93b854c2cc6551 (172.31.96.0/20) | us-east-2c, umdb_eb_priv_2c

# security group 
sg-1308436b (default) | MySQL

## Structure

```
pyterrier-search
│   Dockerfile
|   README.md
|   rds_config.py
│   run_docker.bash 
|   search.py
|   pyterrier_search.py   
│
└───packages
│   │   botocore
│   │   java
│   │   jnius 
│   │   nltk
│   │   numpy
│   │   pandas
│   │   pymysql
│   │   pyterrier * 
│   │   regex
```

\* `packages/pyterrier` has been modified for our usage (mainly just changing download locations, its possible to also just set environment variables, but this is what we rolled with), particularly `packages/pyterrier/pyterrier/__init__.py`, `packages/pyterrier/ir_datasets/util/__init__.py`; our changes begin with `LEARNING_CLUES BEGIN` and end with `LEARNING_CLUES END`

### Dockerfile

Required by Docker in order to create a container

### README.md

this

### rds_config.py 

Holds credentials for database and such. Currently hardcoded.

### run_docker.bash

A bash script that rebuilds the Docker image on your local device (named pyterrier-search), then pushes it to the ECR repository - 229471331279.dkr.ecr.us-east-2.amazonaws.com/pyterrier-search

### search.py 

Wrapper for lambda handler, calls pyterrier_search to get results. Requires `query`, `canvasSiteId`, and `session_id`, and returns an error otherwise.

### pyterrier_search.py

Contains code for executing pyterrier search, querying database and s3 buckets.

#### packages 

Folder containng all the dependencies required for `search.py` and `pyterrier_search.py`.

Using dependencies with Lambda ~ 

Follwing a guide from [medium](https://korniichuk.medium.com/lambda-with-pandas-fd81aa2ff25e#:~:text=numpy%20*.dist%2Dinfo-,Solution,-AWS%20Lambda%20use)

Summary:

Using `pip install` will sometimes not correctly grab the correct version needed for Amazon Linux environment (which is what lambda runs on), so you have to go to the specific package's `pypi.org/project/package_name/#files` page and download a file that includes `cp38` for `python 3.8` and ends with something like `manylinux1_x86_64.whl` (the important things to look for are `manylinux` and `x86_64.whl`).

This method is required for packages like `jnius`, `numpy`, `regex`, `java`, etc. The whl files I downloaded were `pyjnius-1.4.2-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`, `numpy-1.23.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`, and `regex-2022.7.9-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` for example. For java, I downloaded `amazon-corretto-8.332.08.1-linux-x64.tar.gz` from the AWS website.

Some of the folders may contain duplicate packages (i.e. multiple numpy packages across the folders), and this is fine. Feel free to delete the unecessary packages but it doesn't affect the output unless you have the wrong version downloaded.