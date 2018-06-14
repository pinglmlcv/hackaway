import pymysql
import json
import re


SERVER_PARAMS = {
    'host': "119.84.122.135",
    'port': 27702,
    'user': 'like_jian',
    'password': 'worldcup2018',
    'database': 'worldcup',
    'charset': 'utf8'
}

server = pymysql.Connection(**SERVER_PARAMS)

teams = [
    [1, '俄罗斯', '沙特'],
    [2, '埃及', '乌拉圭'],
    [3, '葡萄牙', '西班牙'],
    [4, '摩洛哥', '伊朗'],
    [5, '法国', '澳大利亚'],
    [6, '秘鲁', '丹麦'],
    [7, '阿根廷', '冰岛'],
    [8, '克罗地亚', '尼日利亚'],
    [9, '巴西', '瑞士'],
    [10, '哥斯达黎加', '塞尔维亚'],
    [11, '德国', '墨西哥'],
    [12, '瑞典', '韩国'],
    [13, '比利时', '巴拿马'],
    [14, '突尼斯', '英格兰'],
    [15, '哥伦比亚', '日本'],
    [16, '波兰', '塞内加尔'],
    [17, '俄罗斯', '埃及'],
    [18, '乌拉圭', '沙特'],
    [19, '葡萄牙', '摩洛哥'],
    [20, '法国', '秘鲁'],
    [21, '伊朗', '西班牙'],
    [22, '丹麦', '澳大利亚'],
    [23, '阿根廷', '克罗地亚'],
    [24, '尼日利亚', '冰岛'],
    [25, '巴西', '哥斯达黎加'],
    [26, '塞尔维亚', '瑞士'],
    [27, '韩国', '墨西哥'],
    [28, '德国', '瑞典'],
    [29, '比利时', '突尼斯'],
    [30, '英格兰', '巴拿马'],
    [31, '波兰', '哥伦比亚'],
    [32, '日本', '塞内加尔'],
    [33, '乌拉圭', '俄罗斯'],
    [34, '沙特', '埃及'],
    [35, '伊朗', '葡萄牙'],
    [36, '西班牙', '摩洛哥'],
    [37, '丹麦', '法国'],
    [38, '澳大利亚', '秘鲁'],
    [39, '尼日利亚', '阿根廷'],
    [40, '冰岛', '克罗地亚'],
    [41, '塞尔维亚', '巴西'],
    [42, '瑞士', '哥斯达黎加'],
    [43, '韩国', '德国'],
    [44, '墨西哥', '瑞典'],
    [45, '英格兰', '比利时'],
    [46, '巴拿马', '突尼斯'],
    [47, '日本', '波兰'],
    [48, '塞内加尔', '哥伦比亚'],
]

def get_content():
    sqls = "select Blogerid, Content from Data where  Addon >= NOW() - interval 1 day"
    with server.cursor() as cursor:
        cursor.execute(sqls)
        content = cursor.fetchall()
    return content

content = get_content()
# print(len(content))

def gen_rate_patterns(host, guest):
    patterns = [
        f'.*?(?P<Points>{host}[打对完胜比：:]+{guest}\d[：:\-比]\d).*?',
        f'.*?(?P<Points>{host}\d[：:\-比]\d).*?{guest}.*?',
        f'.*?(?P<Points>{host}.*?[输|赢]?.*?).*?',
        f'.*?(?P<Points>{guest}.*?[输|赢]?.*?).*?',
        f'.*?(?P<Points>{guest}.*?[输|赢]?).*?',
    ]
    return patterns

def get_host_and_guest(gpid):
    team = teams[gpid-1]
    return team[1], team[2]


def test_gen_rate_patterns(gpid):
    host, guest = get_host_and_guest(gpid)
    patterns = gen_rate_patterns(host, guest)
    text = [c for (id, c) in content]
    print("in")
    for p in patterns:
        for t in text:
            res = re.search(p, t)
            if res:
                group = res.group("Points")
                print(res.group(), group)

test_gen_rate_patterns(1)
server.close()
