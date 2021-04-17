from uuid import uuid4
import os

from sanic import app
from sanic.log import logger

import aiofiles
import datetime
import aiohttp

import datetime
import asyncio

from sanic.response import json

import pymysql
import argparse
import datetime

parser = argparse.ArgumentParser()
parser.add_argument('date', type=str)
args = parser.parse_args()
print(args.date)


async def get_userprofile():
    db1 = pymysql.connect(host='172.16.254.9', user='root', password='1q2w3e4r', database='uat')
    cursor1 = db1.cursor()
    db2 = pymysql.connect(host='172.16.254.9', user='root', password='1q2w3e4r', database='imcddb-uat')
    cursor2 = db2.cursor()
    db3 = pymysql.connect(host='172.16.254.9', user='root', password='1q2w3e4r', database='db_event')
    cursor3 = db3.cursor()

    # 按天查询表1
    sql = f"select wechat_union_id from mcd_member_wx where create_time LIKE '{args.date}%'"
    sql1 = f"select count(wechat_union_id) from mcd_member_wx where create_time LIKE '{args.date}%'"
    cursor1.execute(sql)
    results1 = cursor1.fetchall()
    cursor1.execute(sql1)
    results11 = cursor1.fetchall()
    num = results11[0][0]
    # print(results)
    result = results1[0]
    for i in range(1, num):
        result += results1[i]
    result = f"('{result[0]}')" if len(result) == 1 else result
    # 将表1 的查询结果放入表2查询
    sql2 = f"select unionid from t_userinfo where unionid in {result} and new_avatar_url is null"
    sql22 = f"select count(unionid) from t_userinfo where unionid in {result} and new_avatar_url is null"
    cursor2.execute(sql2)
    results2 = cursor2.fetchall()
    # 若不存在，新建
    if not results2:
        sql5 = f"select nickname,openid,gender,province,avatar_url,create_time,unionid from t_wechat_userinfo where unionid in {result} order by create_time desc limit 1"
        cursor3.execute(sql5)
        results5 = cursor3.fetchall()
        for row in results5:
            nickname = row[0]
            openid = row[1]
            gender = row[2]
            province = row[3]
            avatar_url = row[4]
            create_time = row[5]
            unionid = row[6]
            sql6 = f"insert into t_userinfo (nickname,openid,unionid,gender,province,create_time)values('{nickname}','{openid}','{unionid}','{gender}','{province}','{create_time}')"
            cursor2.execute(sql6)
            # 下载头像
            await store_user_info(avatar_url, cursor2, unionid)
    else:
        print(results2)
        cursor2.execute(sql22)
        results22 = cursor2.fetchall()
        num = results22[0][0]
        result1 = results2[0]
        for i in range(1, num):
            result += results2[i]
        print(result1)
        result1 = f"('{result1[0]}')" if len(result1) == 1 else result1
        # 将满足表2的查询结果放入表3查询，头像url
        sql3 = f"select avatar_url,unionid from t_wechat_userinfo where unionid in {result1} order by create_time desc limit 1"
        cursor3.execute(sql3)
        results3 = cursor3.fetchall()
        for row in results3:
            avatar_url = row[0]
            unionid = row[1]
            # 下载头像保存本地并上传表2
            await store_user_info(avatar_url, cursor2, unionid)
    db1.commit()
    db2.commit()
    db3.commit()
    db2.close()
    db1.close()
    db3.close()


# 下载头像并上传表2
async def store_user_info(avatar_url, cursor2, unionid):
    print(unionid)
    img_url = avatar_url
    base_path = '/home/chen'
    now_dt = datetime.datetime.now().strftime("%Y%m%d")
    img_folder = '%s/%s' % (now_dt, 'sss')
    # img_type = img_url[img_url.rindex(".") + 1:]
    img_name = '%s/%s' % (img_folder, str(uuid4()))
    img_path = "%s/%s" % (base_path, img_name)
    if not os.path.exists(os.path.join(base_path, img_folder)):
        os.makedirs(os.path.join(base_path, img_folder))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=img_url) as resp:
                async with aiofiles.open(img_path, 'wb') as fd:
                    while 1:
                        chunk = await resp.content.read(1024)  # 每次获取1024字节
                        if not chunk:
                            break
                        await fd.write(chunk)
        sql4 = f"update t_userinfo set new_avatar_url='{img_path}' where unionid ='{unionid}'"
        cursor2.execute(sql4)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    # 获取事件循环
    loop = asyncio.get_event_loop()
    # 运行任务
    loop.run_until_complete(get_userprofile())
    # 关闭事件循环
    loop.close()
