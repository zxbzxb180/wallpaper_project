import pymongo
import pymysql

import traceback
import hashlib
from datetime import datetime

from upload_2_qiniuyun import uploader

from logger import logger
from settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MONGO_HOST, MONGO_PORT, HANDLE_LIST

from utils.uid import get_uid

class AutoUploader():

    def __init__(self):
        self.sql_client = pymysql.connect(host=MYSQL_HOST,
                             port=MYSQL_PORT,
                             user=MYSQL_USER,
                             password=MYSQL_PASSWORD,
                             db=MYSQL_DB,
                             charset='utf8')
        logger.info("连接mysql数据库成功")
        self.client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        logger.info("连接mongodb数据库成功")
        self.mongodb = self.client['wallpaper']
        self.uploader = uploader()


    def __del__(self):
        self.sql_client.close()


    def get_android_wallpaper(self):
        android_collection = self.mongodb[HANDLE_LIST["android"]["mongodb"]]
        wallpapers = android_collection.find({"is_handle": {"$exists": False}})
        for wallpaper in wallpapers:
            img_url = wallpaper['wp']
            # th_url = img_url+'&imageMogr2/thumbnail/!240x240r/gravity/Center/crop/240x240'
            img_id = get_uid(img_url)

            result1 = self.to_upload(img_id, img_url, HANDLE_LIST["android"]["mongodb"])
            # result2 = self.to_th_upload(img_id, th_url, HANDLE_LIST["android"]["mongodb"])

            # if result1 and result2:
            if result1:
                android_collection.update_one({'_id':wallpaper['_id']}, {'$set':{'is_handle':True}})


    def get_wallhaven_wallpaper(self):
        wallhaven_collection = self.mongodb[HANDLE_LIST["wallhaven"]["mongodb"]]
        wallpapers = wallhaven_collection.find({"is_handle":  False })
        for wallpaper in wallpapers:
            img_url = wallpaper['wp']
            # th_url = wallpaper['thumb']
            img_id = get_uid(img_url)

            result1 = self.to_upload(img_id, img_url, HANDLE_LIST["wallhaven"]["mongodb"])
            # result2 = self.to_th_upload(img_id, th_url, HANDLE_LIST["wallhaven"]["mongodb"])

            # if result1 and result2:
            if result1:
                wallhaven_collection.update_one({'_id':wallpaper['_id']}, {'$set':{'is_handle':True}})



    def to_upload(self, img_id, img_url, source):
        result = self.uploader.upload(img_id, img_url)
        if result:
            sql = "INSERT IGNORE INTO `wallpaper_wallpaper` (`img_id`, `url`, `thumbnail`, `source`, `add_time`) VALUES (%s, %s, %s, %s, %s);"
            url = 'https://yueeronline.xyz/{}.jpg'.format(img_id)
            thumbnail = url + '?imageView2/1/w/240/h/240/q/75'
            data = (img_id, url, thumbnail, source, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.save_to_mysql(sql, data)
            logger.info("壁纸已写入mysql数据库，id：{}, 链接：{}".format(img_id, url))
            return True


    # 七牛云支持访问图片时改变分辨率，因此不需要额外存储缩略图了
    # def to_th_upload(self, img_id, th_url, source):
    #     qiniu_url = 'https://yueeronline.xyz/th_{}.jpg'.format(img_id)
    #     result = self.uploader.upload('th_{}'.format(img_id), th_url)
    #     if result:
    #         sql = "UPDATE `wallpaper_wallpaper` SET `thumbnail` = '{}' WHERE img_id = '{}' and source = '{}'".format(qiniu_url, img_id, source)
    #         self.save_to_mysql(sql)
    #         logger.info("壁纸已写入mysql数据库，id：{}, 链接：{}".format(img_id, th_url))
    #         return True


    def save_to_mysql(self, sql, data=None):
        cursor = self.sql_client.cursor()
        try:
            # 执行sql语句
            cursor.execute(sql, data)
            # 执行sql语句
            self.sql_client.commit()
        except Exception as e:
            # 发生错误时回滚
            print(traceback.format_exc())
            self.sql_client.rollback()
        cursor.close()


    def main(self):
        # 上传安卓壁纸
        self.get_android_wallpaper() if HANDLE_LIST.get("android") else None
        # 上传wallhaven壁纸
        self.get_wallhaven_wallpaper() if HANDLE_LIST.get("wallhaven") else None
        print('finish!')
        logger.info("今日壁纸上传七牛云并保存外链至mysql完毕！")


if __name__ == '__main__':
    try:
        AU = AutoUploader()
        AU.main()
        logger.info("wallpaper uploader success!")
    except Exception as e:
        logger.exception(e)


