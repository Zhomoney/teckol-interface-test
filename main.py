import os
import re

import pytest

import config
from common import initInterface, requestInterfaceMsg, getTestCases, iterationValue
from sqlUtil import BasePymysqlPool, PymysqlPool

if __name__ == '__main__':
    initInterface()
    pytest.main([
        '-s',
        '-v',
        '--capture=sys',
        'testcase.py','--clean-alluredir',
        '--alluredir=./report/allure_report'
    ])
    os.system(r'allure generate ./report/allure_report -o ./report/allure_report/html --clean')

