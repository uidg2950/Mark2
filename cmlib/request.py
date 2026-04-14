#!/usr/bin/python
"""
# *****************************************************************************
# *
# * (c) 2016-2021 Continental Automotive Systems, Inc., all rights reserved
# *
# * All material contained herein is CONTINENTAL CONFIDENTIAL and PROPRIETARY.
# * Any reproduction of this material without written consent from
# * Continental Automotive Systems, Inc. is strictly forbidden.
# *
# * Filename:     request.py
# *
# * Description:
# *
# *****************************************************************************
"""
import requests

TIMEOUT_SECONDS = 10

STATUS_CODES = requests.codes


def http_request(url, method, **kwargs):
    """
    Create post request sending a dictionary as body

    @param url: endpoint for the request
    @param method: Method HTTP to do the request.
    @param kwargs: pass optional arguments to request.
    @return: class requests.Response, which contains a server’s response to an HTTP request.
    """
    kwargs['timeout'] = TIMEOUT_SECONDS
    response = None
    try:
        # Perform HTTP request
        response = requests.request(method, url, **kwargs)

    except requests.exceptions.RequestException as err:
        print("Error HTTP request to: {} service. Method: {}".format(url, method))
        # print the exception from HTTP request
        print(err)

    if response:
        # prints values for debugging.
        print("HTTP request")
        print("Method: {}".format(response.request.method))
        print("URL: {}".format(response.request.url))
        print("Status Code: {}".format(response.status_code))
        print("Body response: {}".format(response.json()))

    return response
