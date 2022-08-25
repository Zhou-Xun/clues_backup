# Thomas Horak (thorames), Chris Lee (chrisree), Xun Zhou (xunzhou)

import sys
import logging
import json
from pyterrier_search import  pyterrier_search
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Error:
  def __init__(self, msg):
    self.message = msg

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def handler(event, context):
    """
    leccap embed link
    image url tumbnail
    """
    # todo :rename class_id to canvassite d
    params = event.get('queryStringParameters')
    if params == None:
        logger.error("missing all parameters in request")
        return respond(Error("missing query, canvasSiteId, and session_id in request"))
    query = params['q']
    # class_id = params['class_id']
    canvasSiteId = params['canvasSiteId']
    session_id = params['session_id']
    
    if not all(params.values()):
        logger.error("missing query, canvasSiteId, or session_id in request")
        return respond(Error("missing query, canvasSiteId, or session_id in request"))
    if int(canvasSiteId) < 0 or int(session_id) < 0:
        logger.error("invalid canvasSiteId or session_id")
        return respond(Error("invalid canvasSiteId or session_id"))

    modified_query = query.lower()
    info = {}
    #base_dirname = app.config['LOCAL_INDEX_PATH']

    #This is where we choose the search engine


    try:
        info["search_algo"] = "pyterrier"
        print("S-31: Beginning PyTerrier")
        vid_result = pyterrier_search(modified_query, canvasSiteId)
        print("S-32: ",vid_result)
    except Exception as e:
        print ("S-36: ",e)
        return respond(Error("e"))
        #pass

    return respond(None, {
        "canvasSiteId": canvasSiteId,
        "vid_result": vid_result,
    })
    #
    # try:
    #     temp = {}
    #     temp['DICT_API'] = 'https://api.dictionaryapi.dev/api/v2/entries/en_US/'
    #     definition = requests.get(f"{temp['DICT_API']}{query}")
    #     if definition.status_code == 200:
    #         info['query'] = query
    #         info['definition'] = definition.json()[0]['meanings'][0]['definitions'][0]['definition']
    #     else:
    #         info['query'] = query
    #         info['definition'] = 'No Definition Found'
    # except (IndexError, KeyError) as e:
    #     info['query'] = query
    #     info['definition'] = 'No Definition Found'
    # print("56: ",class_id, info)
    # return respond(None, {
    #         "class_id":class_id,
    #         "definition":info['definition'],
    #         "searched term":info['query'],
    #         #"recordings":info['recordings'],
    #         "search algorithm":info['search_algo']
    #     })
        