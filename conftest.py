import json

import pytest
import requests
from common import getTestCases, getHeader, getBody, getCode, VariableOperation, verify
from config import LOGIN_CASE, BASEURL


def login(id):
    case = None
    caseList = getTestCases()
    for i in caseList:
        if str(i['id']) == str(id):
            case = i
    code, method, name = getCode(case['interfaceId'])
    body, code = getBody(case['reqBody'], code)
    headers = getHeader(case['reqHeader'])
    # 接口请求
    response = requests.request(method=method,
                                url=BASEURL + code,
                                data=body,
                                headers=headers)
    # 校验statusCode
    assert response.status_code == int(case['AssertResCode'])
    # 校验responseData
    resData = json.loads(response.text)
    verify(case['AssertResBody'], resData, 'str equal')
    if case['VariableOperation']:
        VariableOperation(case['VariableOperation'], resData)

# @pytest.fixture()
# def allureFixture():
