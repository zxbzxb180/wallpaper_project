import pymongo
import pymysql

import traceback
import hashlib
from datetime import datetime

from upload_2_qiniuyun import uploader
from logger import logger

class AutoUploader():

    def __init__(self):
        self.sql_client = pymysql.connect(host='172.17.0.1',
                             port=3306,
                             user='web',
                             password='cx6222580',
                             db='web',
                             charset='utf8')
        self.client = pymongo.MongoClient('139.198.181.33', 17027)
        self.db = self.client['wallpaper']
        self.android_wallpaper = self.db['android_wallpaper']
        self.uploader = uploader()


    def __del__(self):
        self.sql_client.close()


    def get_android_wallpaper(self):
        wallpapers = self.android_wallpaper.find()
        for wallpaper in wallpapers:
            print(wallpaper)
            #img_id = wallpaper['id']
            img_url = wallpaper['wp']

            m = hashlib.md5()
            m.update(img_url.encode(encoding='utf-8'))
            img_id = m.hexdigest()
            self.to_th_upload(img_id, img_url)


    def to_th_upload(self, img_id, img_url):
        th_url = img_url+'&imageMogr2/thumbnail/!240x240r/gravity/Center/crop/240x240'
        qiniu_url = 'https://yueeronline.xyz/adwp_th_{}.jpg'.format(img_id)
        result = self.uploader.upload('adwp_th_{}'.format(img_id), th_url)
        if result:
            sql = "UPDATE `wallpaper_wallpaper` SET `thumbnail` = '{}' WHERE img_id = '{}'".format(qiniu_url, img_id)
            self.save_to_mysql(sql)

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
        self.get_android_wallpaper()
        print('finish!')


if __name__ == '__main__':
    AU = AutoUploader()
    AU.main()


