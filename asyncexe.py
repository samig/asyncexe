from quart import Quart, jsonify, request, abort, wrappers
import asyncio
import json
import re
import uuid
from shlex import quote

## Command, arguments and host to be received and executed
cmd = ""
args = ""


## Dictionaries to support the collection of results
## dictMain maintains all results and request IDs through the time of the execution
## if the execution is not complete the value is the process status
dictMain={}

## Variable to hold the instance of execution
processInstance = None



app = Quart(__name__)

async def exec(reqj, reqID):
    ## Variables extracted from the request
    cmd  = str( reqj['cmd'])
    args =   reqj['args'].split(',')
    #print("Args :", args,":",len(args[0]))
    command = quote(cmd)
    if len(args[0]) > 0:
        for arg in args:
            #Add space between args
            command += " "
            command +=  quote(arg)
    #execStr =  " --- Executing command :"+ command + " --- Request ---- " + str(reqID)
    #print(execStr, " started --- ")
    print ("Command  : ",command)
    processInstance = await  asyncio.create_subprocess_shell(command,stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await  processInstance.communicate()
    ## print(execStr , " is complete --- ")
    ## Collection of results or error codes into the variable result
    if processInstance.returncode == 0 or processInstance.returncode == 2:
        result = stdout.decode("utf-8")
    else :
        result = "Request: "+ str(reqID) + ", return code : " +  str(processInstance.returncode) + ", Error Message :  "  + str(stderr) + ",Output:" +str(stdout)
    ## Add results to the Main dictionary using the request ID as keys
    dictMain[reqID]=result

@app.route('/asyncexec/api/v1.0', methods=['POST'])
async def new_task():
    ## Temporary dictionary to assist in jsonification of output
    dictReq = {}
    # Generate a unique request ID using UUID
    ID = uuid.uuid1()
    reqID= ID.time_low
    ## Print command to return results (for testing)
    reqj = await request.json
    ## Get the event loop and launch task on it
    loop = asyncio.get_event_loop()
    loop.create_task(exec(reqj, reqID))
    ## Prepare the dictionary to return results
    #response = await wrapper.response(Location='/asyncexec/api/v1.0/result' + str(reqID))
    resultURL ='/asyncexec/api/v1.0/result/' + str(reqID)
    resultCmd =  " ----  curl -i -X GET  http://localhost:5000/asyncexec/api/v1.0/result/"+ str(reqID)
    return jsonify("Sample command to get result",resultCmd), 201, {'Location': resultURL}

@app.route('/asyncexec/api/v1.0/result/<int:reqID>', methods=['GET'])
async def get_result(reqID):
    ## check if the key exist in the Main dictionary and return the result
    if reqID in dictMain.keys():
        return jsonify(dictMain[reqID]), 200
    else:
        return jsonify({str(reqID):"Process is still running, please try again in a few moments ..."}), 202


if __name__ == "__main__":
    app.run('0.0.0.0', port=5000, debug=True)
