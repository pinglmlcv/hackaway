import re
import asyncio
import aiohttp
import time


START_TIME = time.time()
IMAEG_LIST = []


async def fetch(word):
    """ return html page
    word: kind
    """
    def get_urls(html):
        """ parse image from html page
        html: html page from fetch
        """
        pattern = re.compile('"objURL":"(https?:[\/a-zA-Z0-9_\-\.]+.jpg)"')
        urls = pattern.findall(html)
        # for debug
        IMAEG_LIST.append(urls)
        return urls

    print(f'start fetch task {word} at: {time.time() - START_TIME}')
    url = "https://image.baidu.com/search/index?tn=baiduimage&word={}"
    url = url.format(word)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()
            return get_urls(text)
            

async def download(url, name):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            content = await resp.read()
            with open(name, 'wb') as f:
                f.write(content)


def main():
    global IMAEG_LIST
    words = [
        '人类笑容', "青年笑容", '小孩笑容', "美女笑容", "医生笑容", "学生笑容", "护士笑容", 
        '程序员的笑容', '马云的笑容', '奥巴马笑容', '习近平笑容', '车模笑容', '清洁工的笑容',
        '妻子的笑容', '丈夫的笑容', '杀手的笑容', '黑客的笑容', '建筑师的笑容', '法师的笑容',
        '藏民的笑容', '回族的笑容', '基督教的笑容', '白种人的笑容', '蓝眼睛的人的笑容', '黄种人的笑容',
        '黑人的笑容', '空姐的笑容', '行政小哥的笑容', '人事小妹的笑容', '叔叔的笑容', '警察的笑容',
        '军人的笑容', '导演的笑容', '大学生的笑容', '暨南大学生的笑容', '农村孩子的笑容', 
        '贫困山区的人的笑容', '放牛娃的笑容', '古装女子的笑容'
    ]

    tasks = [asyncio.ensure_future(fetch(word)) for word in words]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    
    # download
    IMAEG_LIST = [url for lst in IMAEG_LIST for url in lst]
    tasks = [asyncio.ensure_future(download(url, "%s.jpg" % i)) for i, url in enumerate(IMAEG_LIST)]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == '__main__':
    main()