# Thomas Horak (thorames), Chris Lee (chrisree), Xun Zhou (xunzhou)
# updated_pyterrier_search.py
import os
import pyterrier as pt
import json
# from clue_backend.models import Video
from threading import Thread
import boto3
import botocore
import concurrent.futures
from multiprocessing import Process, Pipe
from functools import partial

import rds_config
import pymysql
import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#rds settings
rds_host  = rds_config.db_host
name = rds_config.db_user
password = rds_config.db_password
db_name = rds_config.db_name

try:
    conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

def download_one_file(s3_bucket, key, full_path):
    s3_bucket.download_file(key, full_path)

def download_index(s3_bucket, local_path, folder_name, conn):
    key_full_path_list = []
    bucket_objects = s3_bucket.objects.filter(Prefix=folder_name)
    # throw error if objects is empty

    for obj in bucket_objects:
        full_path = os.path.join(local_path, os.path.relpath(obj.key, folder_name))
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))
        else:
            # if the file still exists in /tmp/
            if os.path.exists(full_path):
                continue

        key_full_path_list.append((obj.key, full_path))

    func = partial(download_one_file, s3_bucket)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(func, kf[0], kf[1]): kf for kf in key_full_path_list
        }

    conn.send([pt.IndexRef.of(local_path + "/data.properties")])
    conn.close()

def retrieve_indexes(class_id):
    print("retrieve start")
    # Temporary local folder for index loaded from S3
    pt_index_path = '/tmp/Index/' + str(class_id)

    # Increases the amount of active threads in boto to 50
    client_config = botocore.config.Config(
        max_pool_connections=50
    )

    s3_bucket = boto3.resource('s3', config=client_config).Bucket("pyterrier-indexes")

    # async downloading of transcript and sentence folders
    processes = []
    parent_connections = []
    for file_types in ["/Transcripts", "/Sentences"]:
        parent_conn, child_conn = Pipe()
        parent_connections.append(parent_conn)

        process = Process(target=download_index, args=(s3_bucket, pt_index_path + file_types, str(class_id) + file_types, child_conn,))
        processes.append(process)

    for process in processes:
        process.start()

    for process in processes:
        process.join()
    print("retreive end")
    return parent_connections[0].recv()[0], parent_connections[1].recv()[0]


def get_vid_info(class_id):
    # print("PYT-13: Beginning read_transcripts(\"",class_id,"\")")
    vid_info = {}

    # Retrieve videos from database
    query_str = "SELECT * FROM videos WHERE canvasSiteId=" + str(class_id)
    with conn.cursor() as cur:
        cur.execute(query_str)
        videos = cur.fetchall()

    # videos = Video.query.filter_by(class_id=class_id)
    # print("============get_vid_info==========")
    # print(videos[0][2])
    # Load each video transcript, process sentences and full text
    for video in videos:
        # translate to dot dictionary, to avoid refactor
        video_id = video[0]
        upload_src = video[1]
        title = video[2]
        video_link = video[3]
        date = video[5]
        image = video[7]

        vid_info[str(video_id)] = [title, image, video_link, date, upload_src]

    return vid_info

# def pull_vid_info(class_id):
#     # Retrieve video info from database
#     return dict([(video.video_id, [video.title, video.image, video.video_link, video.date, video.upload_src]) for video in Video.query.filter_by(class_id=class_id)])

def perform_search(query, transcript_index, sentence_index):
    # Instantiate PyTerrier search object with TF-IDF weighting
    tfidf = pt.BatchRetrieve(transcript_index, wmodel="TF_IDF")

    # Perform query search using PyTerrier search object
    transcript_results = tfidf.search(query)

    # Instantiate PyTerrier search objects (Sequential Dependence Model, Query Expansion, Term Frequency weighting)
    sdm = pt.rewrite.SDM()
    qe = pt.rewrite.Bo1QueryExpansion(sentence_index)
    tf = pt.BatchRetrieve(sentence_index, wmodel="Tf")
    results = pt.BatchRetrieve(sentence_index, metadata=["docno", "sentence", "time"])

    # String search objects together to create pipeline
    pipeline = tf >> sdm >> tf >> qe >> tf >> results

    # Perform query search using PyTerrier search pipeline
    sentence_results = pipeline.search(query)

    return transcript_results, sentence_results

def return_results(query, transcript_results, sentence_results, vid_info):
    search_results = {"recordings": {query: []}}

    # Reformat sentence search results
    sentence_scores = sentence_results[['docno', 'score', 'sentence', 'time']].values.tolist()

    lecture_moments = {}
    query_len = len(query.split())

    # Loop over sentence search results in order of relevance to query
    for docno, score, sentence, time in sentence_scores:

        # Threshold to limit number of sentences returned
        if score >= query_len - 0.5:
            lecture_name = "_".join(docno.split("_")[:-1])
            if lecture_name in lecture_moments:
                lecture_moments[lecture_name].append({"context": sentence, "timestamp": time})
            else:
                lecture_moments[lecture_name] = [{"context": sentence, "timestamp": time}]

    # Reformat transcript search results
    transcript_scores = transcript_results[['docno', 'score']].values.tolist()

    # Loop over lectures and assign ordered sentence search results as well as corresponding video info for front end
    for docno, score in transcript_scores:
        if docno in lecture_moments:
            vid_date = vid_info[docno][3].strftime("%m/%d/%Y, %H:%M:%S")
            result = {"vid_id": docno, "title": vid_info[docno][0], "vid_date": vid_date, "timestamps": lecture_moments[docno], "image": vid_info[docno][1], "video_link": vid_info[docno][2]}
            search_results["recordings"][query].append(result)

    return search_results

def pyterrier_search(query, class_id):
    # Set java virtual machine path (important for PyTerrier)
    os.environ["JVM_HOME"] = "/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home/lib/libjli.dylib"

    # Initialize PyTerrier
    if (not pt.started()):
        pt.init()

    # Retrieve indexes from S3 and corresponding video info
    transcript_index, sentence_index = retrieve_indexes(class_id)
    #vid_info = pull_vid_info(class_id)

    # Perform search
    transcript_results, sentence_results = perform_search(query, transcript_index, sentence_index)
    vid_info = get_vid_info(class_id)
    # Format and return results
    # print("====================================")
    # print("print the result of pyterrier search")
    # print("query: ", query)
    # print("vid_info: ", vid_info)
    # print("transcript_results: ", transcript_results)
    # print("sentence_results: ", sentence_results)
    # search_results = return_results(query, transcript_results, sentence_results, vid_info)
    # print("result")
    # print(search_results["recordings"][query])
    # print(search_results["recordings"][query][0])

    return return_results(query, transcript_results, sentence_results, vid_info)