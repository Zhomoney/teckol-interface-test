import os

testCasePath = os.getcwd()
ExcelName = 'interfaceTestCase.xlsx'

print(testCasePath)

MYSQL_HOST = "10.205.0.202"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "PK2fcEjUaUmPmlW2"
MYSQL_CPMS_DATABASE = "tecgo_cpms"
MYSQL_TECGOSERVICE_DATABASE = 'business_tecgo'

BASEURL = 'https://test01-influencerplus.tec-develop.com/tecgo-service'
INTERFACEURL = 'https://test01-unicreator.tec-develop.com/tecgo-service'

INTERFACELIST = []
GLOBAL_VARIABLE = {}

CASE_VARIABLE = {}

LOGIN_CASE = {
    'IP_adv': 1,
    'professional_member': 2,
    'IP_adLeader': 3,
    'IP_adStaff': 4,
    'enterprise_member': 5,
}
