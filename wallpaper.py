import time
import aiohttp
import asyncio
import pymongo
import traceback
from auto_upload import AutoUploader
from logger import logger


async def fetch(session, url):
    for i in range(10):
        try:
            async with session.get(url, proxy=await get_proxies(), headers=headers, timeout=6) as response:
            # async with session.get(url, headers=headers) as response:
                return await response.content()
        except Exception as e:
            # print(traceback.format_exc())
            logger.exception(e)

    return False


# 解析网页
async def parser(data_json, session):
    datas = data_json.get('res', {}).get('vertical', [])
    for data in datas:
        #id = data.get('id', '')
        #img = data.get('img', '')
        #async with session.get(img, proxy=await get_proxies(), headers=headers, timeout=6) as response:
        #    if response.status == 200:
        #        with open('./images/{}.jpg'.format(id), 'wb') as f:
        #            f.write(await response.content.read())
        #    else:
        #        raise
        data['crawl_date'] = time.strftime("%Y-%m-%d",time.localtime(time.time()))
        data['crawl_time'] = time.time()
        collection.update_one({'id':data['id']}, {'$setOnInsert':data}, upsert=True)
        print(data)


# 处理网页
async def download(url):
    print(url)
    async with asyncio.Semaphore(50):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            for i in range(20):
                try:
                    async with session.get(url, proxy=await get_proxies(), headers=headers, timeout=12) as response:
                        if response.status == 200:
                            response = await response.json()
                            await parser(response, session)
                            break
                except Exception as e:
                    # print(traceback.format_exc())
                    logger.exception(e)


async def get_proxies():
    """
    获取代理
    :return: 代理
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://139.198.181.33:5010/get/', timeout=12) as response:
                proxy_dict = await response.json()
                return 'http://' + proxy_dict['proxy'] + '/'
        except Exception as e:
            logger.exception(e)


async def main():
    tasks = [download(url) for url in urls]
    results = await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        # 全部网页
        urls = ['http://service.picasso.adesk.com/v1/vertical/category/4e4d610cdf714d2966000003/vertical?&adult=false&order=new&skip={}'.format(i) for i in range(0, 450, 30)]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        }

        # 初始化mongodb
        client = pymongo.MongoClient('139.198.181.33', 17027)
        db = client['wallpaper']
        #today = time.strftime("%Y-%m-%d",time.localtime(time.time()))
        collection = db['android_wallpaper']
        logger.info("初始化mongodb成功！")
        # 统计该爬虫的消耗时间
        print('#' * 50)
        t1 = time.time()  # 开始时间

        # # 利用asyncio模块进行异步IO处理
        # loop = asyncio.get_event_loop()
        # tasks = [download(url) for url in urls]
        # # tasks = asyncio.gather(*tasks)
        # loop.run_until_complete(asyncio.wait(tasks))

        #另一种写法
        asyncio.run(main())

        t2 = time.time()  # 结束时间
        logger.info('使用aiohttp完成壁纸链接抓取，总共耗时：%s' % (t2 - t1))
        print('#' * 50)

        # 立即开始下载图片，防止t参数实效
        AU = AutoUploader()
        AU.main()
        logger.info("每日壁纸程序执行完毕!")

    except Exception as e:
        logger.exception(e)



