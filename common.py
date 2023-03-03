import json
import re
from copy import deepcopy
from json import JSONDecodeError

import requests
import config
from excelUtil import write_xlsx_excel, FileIsExist, read_xlsx_excel
from sqlUtil import PymysqlPool

ExcelPath = config.testCasePath + '\\' + config.ExcelName


# 获取接口信息
def requestInterfaceMsg():
    '''
    请求tecgo-service接口信息
    :return: 字典列表：【{接口，请求方法，名称}】
    '''
    res = requests.get(
        url=config.INTERFACEURL + '/v2/api-docs',
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        })
    response = json.loads(res.text)
    interfaceList = response['paths'].keys()
    resData = []
    for i in interfaceList:
        method = list((response['paths'][i]).keys())[0]

        resData.append({
            'code': i,
            'method': method,
            'name': response['paths'][i][method]['summary'],
        })
    return resData


# 对excel-sheet：interface初始化
def initInterface():
    '''
    初始化excel表的sheet：interface
    :return:
    '''
    FileIsExist(config.ExcelName)
    readData = read_xlsx_excel(ExcelPath, 'interface')
    readData.pop(0)
    reqData = requestInterfaceMsg()
    readInterfaceList = []
    insertMsg = deepcopy(readData)
    maxId = 1
    for i in insertMsg:
        readInterfaceList.append(i[1])
        if maxId < int(i[0]):
            maxId = int(i[0])
    for i in reqData:
        if i['code'] not in readInterfaceList:
            insertMsg.append([
                maxId,
                i['code'],
                i['method'],
                i['name'],
            ])
            maxId += 1
    insertMsg.insert(0, ['id', 'method', 'name', 'code'])

    write_xlsx_excel(ExcelPath, 'interface', insertMsg)
    for i in range(1, len(insertMsg)):
        config.INTERFACELIST.append({
            'id': insertMsg[i][0],
            'method': insertMsg[i][1],
            'name': insertMsg[i][2],
            'code': insertMsg[i][3],
        })


# 获取所有testCase
def getTestCases():
    '''
    读取excel-sheet:testcase返回测试用例列表
    :return:字典列表
    '''
    readTestCase = read_xlsx_excel(ExcelPath, 'testcase')
    keyList = readTestCase[0]
    testCase = []
    for i in range(1, len(readTestCase)):
        case = {}
        for index, value in enumerate(keyList):
            val = readTestCase[i][index]
            if isinstance(val, str) and '\n' in val:
                val = val.replace('\n', '')
            if value in ['reqHeader', 'reqBody']:
                if val:
                    try:
                        val = json.loads(val)
                    except JSONDecodeError as e:
                        assert False, str(readTestCase[i]) + ' from sheet:testcase is JSONDecodeError'
            case[value] = val
        testCase.append(case)
    testCase = checkTestCase(testCase)
    return testCase


# 检查testCase部分数据格式是否正确
def checkTestCase(testCase):
    '''
    校验excel-sheet：testcase数据是否合规输入
    :param testCase: 字典列表
    :return: 返回字典列表
    '''
    for i in testCase:
        if not i['interfaceId']:
            assert False, "interfaceId is None, please check the sheet of 'testcase' by " + str(i['id'])
        else:
            flag = False
            for j in config.INTERFACELIST:
                if str(j['id']) == str(i['interfaceId']):
                    flag = True
                    break
            if not flag:
                assert False, "interfaceId is not in the sheet of 'interface', please check the sheet of 'testcase' by " + str(
                    i['id'])
        if not i['reqBody']:
            i['reqBody'] = {}
        if not i['name']:
            i['name'] = ''
    return testCase


# 验证数据
def verify(verifyMsg, resData, OperationType):
    '''
    assertBody
    :param verifyMsg:需要校验的数据str ：'res.data.email=xxx;res.code=xxx;'
    :param resData: 返回的resData:字典
    :param type: 暂无用处
    :return:
    '''
    assertList = verifyMsg.split(';')
    for i in assertList:
        if i != '':
            operation = '='
            if '=' in i:
                operation = '='
            elif ' IN ' in i:
                operation = ' IN '
            elif ' CONTAINS ' in i:
                operation = ' CONTAINS '
            oldKey = i.split(operation, 1)[0].strip()
            verifyValue = i.split(operation, 1)[1].strip()
            keyList = oldKey.split('.')
            # 获取返回要校验的值
            resValue = iterationValue(keyList, resData)
            # 替换testcase verify的值
            verifyValue = variableReplace(verifyValue)
            if 'sqlSearch(' in verifyValue and ')' == verifyValue[-1]:
                verifyValue = SearchSql(verifyValue)

            if operation == '=':
                verifyValue = str(verifyValue)
                resValue = str(resValue)
                assert verifyValue == resValue, "[value]responseValue:" + str(
                    resValue) + " not equal to  verifyValue :" + str(
                    verifyValue)
            elif operation == ' IN ':  # 格式：  xxx=[11,22,33]
                verifyList = verifyValue[1:-1].split(',')
                for v in range(0, len(verifyList)):
                    verifyList[v] = verifyList[v].strip()
                assert resValue in verifyList, '[value]responseValue:' + str(
                    resValue) + ' not in [list]VerifyValue' + str(verifyValue)
            elif operation == ' CONTAINS ':
                assert verifyValue in resValue, '[value]verifyValue:' + str(
                    verifyValue) + ' not in [list]resValue' + str(resValue)


# 查询sql
def SearchSql(reqSql):
    '''
    assert时sql查询，初始化获取sql后查询返回
    :param reqSql: sqlSearch(users.id,[{email=test_IP_adv@tec-do.com}])# (表名.字段 , [{字段=值},])
    :return: str
    '''
    table = reqSql.split(',', 1)[0].split('.')[0].split('(')[1]
    field = reqSql.split(',', 1)[0].split('.')[1]
    whereStr = ' where '
    whereStr_back = reqSql.split(',', 1)[1][1:-1]
    whereStrList = whereStr_back.split(',')
    for i in whereStrList:
        operation = '='
        str1 = i[1:-1]
        if '=' in str1:
            operation = '='
        elif ' like ' in str1:
            operation = ' like '
        key = str1.split(operation, 1)[0].strip()
        value = '"' + str1.split(operation, 1)[1].strip().split('}')[0] + '"'
        whereStr_i = key + operation + value + ' and '
        whereStr += whereStr_i
    whereStr = whereStr[0:-5]
    sqlConn = PymysqlPool(config.MYSQL_TECGOSERVICE_DATABASE)
    sql = 'SELECT ' + field + ' FROM ' + table + whereStr
    print(sql)
    result = sqlConn.getAll(sql)
    return result[0][field]


# 设置变量
def setVariable(name, value, scope):  # VarStr ：      set(name,value,scope)
    if scope == 'testcase':  # python对大小写不敏感
        config.CASE_VARIABLE[name] = value
    elif scope == 'global':
        config.GLOBAL_VARIABLE[name] = value
    else:
        assert False, 'please check excel ==>set(' + name + ',' + value + "," + scope + ")"


# 获取变量
def getVariable(varKey):
    '''

    :param varKey:  variableName
    :return:    variableValue
    '''
    if varKey in config.CASE_VARIABLE.keys():
        return config.CASE_VARIABLE[varKey]
    elif varKey in config.GLOBAL_VARIABLE.keys():
        return config.GLOBAL_VARIABLE[varKey]


# 根据res.data.xxx获取response的Value值
def iterationValue(lists, value):
    '''

    :param lists: ['res','xxx','yyy']
    :param value: {'xxx':{'yyy':'vvv'}}
    :return:
    '''
    index = 1

    while index < len(lists):

        if lists[index].isdigit():
            if isinstance(value, list):
                if not value:
                    assert False, lists[index] + " not in " + str(
                        value) + ",please check testcase of assertBody or submit a bug to the developer"
                value = value[int(lists[index])]
            else:
                assert False, lists[index] + " not in " + str(
                    value) + ",please check testcase of assertBody or submit a bug to the developer"
        elif lists[index] in value.keys():
            value = value[lists[index]]
        else:
            assert False, lists[index] + " not in " + str(
                value) + ",please check testcase of assertBody or submit a bug to the developer"

        index += 1
    return value


# 获取Headers
def getHeader(resHeader):
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }
    if resHeader is not None:
        headers = {**headers, **resHeader}
    headers = variableReplace(headers)

    return headers


# 获取Body
def getBody(resBody, resCode):
    body = {}
    if resBody is not None:
        result = re.search('{\w*\W*}', resCode)
        if result:
            for i in result:
                k = i[1:-1]
                v = body[k]
                resCode = resCode.replace(i, v)
                body.pop(k)
        resBody = variableReplace(resBody)
        body = {**body, **resBody}
    return json.dumps(body), resCode


# 从接口列表获取获取路径(/user/adv/login)
def getCode(interfaceId):
    for i in config.INTERFACELIST:
        if interfaceId == int(i['id']):
            return i['method'], i['name'], i['code']


# 变量替换 ${}
def variableReplace(data):
    '''
    替换格式为 ${}的变量
    :param data:(dict/str): 'fdoeriwuegjndsow${name}+++fdspwe'
    :return:'fdoeriwuegjndsowNAME+++fdspwe'
    '''
    d = data
    flagDict = False
    if isinstance(data, dict):
        flagDict = True
        d = json.dumps(data)
    varList = re.findall('\${\w*}', d)
    for i in varList:
        j = i[2: -1]
        value = getVariable(j)
        d = d.replace(i, value)

    if flagDict:
        data = json.loads(d)
    else:
        data = d
    return data


# 变量设置
def VariableOperation(operationStr, responseData):
    '''
    :param operationStr:   set(xxx,xxx,xxx);set(xyy,yyy,cc);
    set():赋值：（variableName, value, scope作用域）   scope: Global, TestCase
    若想获取值，请使用'${变量}'方式
    :return: value
    '''
    operationStr = variableReplace(operationStr)
    operationList = operationStr.split(';')
    for i in operationList:
        if re.search('set(\w*\W*)', i):
            setValue = i[4: -1]
            setArgs = setValue.split(',')
            # response赋值
            if 'res.' in setArgs[1]:
                setArgs[1] = iterationValue(setArgs[1].split('=')[0].split('.'), responseData)
            if len(setArgs) == 2:  # 默认放入作用域scope=testCase
                setVariable(setArgs[0], setArgs[1], 'testcase')
            elif len(setArgs) == 3:
                setVariable(setArgs[0], setArgs[1], setArgs[2])
            else:
                assert False, 'please check excel[testcase] => ' + i


def insertSuccess(id):
    pass
    # TODO 修改excel某个值 SuccessCount
