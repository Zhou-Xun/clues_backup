FROM amazon/aws-lambda-python:3.8

# you could also put every package on the base dir,
# but that might get messy pretty fast

# import packages
ADD packages/botocore ./
ADD packages/java ./
ADD packages/jnius ./
ADD packages/nltk ./
ADD packages/numpy ./
ADD packages/pandas ./
ADD packages/pymysql ./
ADD packages/pyterrier ./
ADD packages/regex ./

ADD search.py ./
ADD rds_config.py ./
ADD pyterrier_search.py ./

# specify lambda handler
CMD ["search.handler"]