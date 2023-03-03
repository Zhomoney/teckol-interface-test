import json
import re

import allure
import pytest
import requests

import config
from common import getTestCases, verify, getHeader, getBody, getCode, VariableOperation
from conftest import login

testCaseList = getTestCases()


@pytest.mark.parametrize('test_info', testCaseList)
def test_case_exec(test_info):
    allure.dynamic.title(test_info['name'])
    allure.dynamic.description(test_info['remark'])

    if test_info['commonCaseId']:
        login(test_info['commonCaseId'])
    code, method, name = getCode(test_info['interfaceId'])
    allure.dynamic.suite(code)
    body, code = getBody(test_info['reqBody'], code)
    headers = getHeader(test_info['reqHeader'])
    # 接口请求
    url = config.BASEURL + code
    if method == 'get':
        if not body:
            body = "{}"
        body = json.loads(body)
        response = requests.get(url, body, headers=headers)  # 此时的body需要为字典
    else:
        response = requests.request(method=method,
                                    url=url,
                                    data=body,
                                    headers=headers)
    # 校验statusCode
    assert response.status_code == int(test_info['AssertResCode'])
    # 校验responseData
    resData = json.loads(response.text)
    verify(test_info['AssertResBody'], resData, 'str equal')
    if test_info['VariableOperation']:
        VariableOperation(test_info['VariableOperation'], resData)
