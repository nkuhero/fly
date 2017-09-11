#coding=utf-8
import web
import json
from WXBizDataCrypt import WXBizDataCrypt
import urllib2
import time
import datetime

appId = 'wx24ff63b17aa9251f'
secret = '3935aac884f4ec0fe38e0d8af33640ec'


urls = (
    '/order', 'index',
    '/order/create', 'add_order',
    '/order/get', 'get_order',
    '/order/follow', 'follow_order',
    '/order/cancel', 'cancel_order',
    '/order/openid', 'get_openid',
    '/order/list', 'order_list',
    '/order/follow/list', 'follow_list',
    '/order/moneypic', 'get_moneypic'
)

url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code'

db = web.database(dbn='mysql', host='127.0.0.1', user='root', pw='1234.com', db='fly')

class index:
    def GET(self):
        orders = list(db.select('s_order', where="id>0"))
        return json.dumps(orders)


class get_moneypic:
    def GET(self):
        i = web.input()
        openid = i.openid
        pay_info = db.select('pay_info', where="user_id='%s'"%openid)[0]
        result = {"user_id" : openid, "money_pic" : pay_info.money_pic}
        return json.dumps(result)

class add_order:
    def POST(self):
        i = web.data()
        i = json.loads(i)
        openid = i["openid"]
        now = datetime.datetime.now()
        create_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        create_time = time.mktime(now.timetuple())
        try:
            db.insert('pay_info', user_id=openid, money_pic=i["money_pic"])
        except:
            db.update('pay_info', where="user_id=%s"%openid, money_pic=i["money_pic"])

        n = db.insert('s_order', nick_name=i["nick_name"].encode("utf-8"), user_id=openid, item_name=i["item_name"].encode("utf-8"), price=i["price"], item_pic=i["item_pic"], money_pic=i["money_pic"], follow_id="", status="create", create_time = create_time, cancel="")
        return json.dumps({"order_id" : n, "create_time" : create_time_str })

class get_openid:
    def GET(self):
        i = web.input()
        js_code = i.js_code
        response = urllib2.urlopen(url%(appId, secret, js_code))
        content = json.loads(response.read())
        openid = content["openid"]
        return json.dumps({"openid" : openid})

class order_list:
    def GET(self):
        i = web.input()
        openid = i.openid
        order_list = list(db.select('s_order', where="user_id='%s'"%openid, order="create_time desc"))
        result_list = []
        now = datetime.datetime.now()
        now_timestamp = time.mktime(now.timetuple())
        for order in order_list:
            create_time = order.create_time
            create_time_str = datetime.datetime.fromtimestamp(create_time).strftime(('%Y-%m-%d %H:%M:%S'))
            follow_time = order.follow_time
            follow_time_str = datetime.datetime.fromtimestamp(follow_time).strftime(('%Y-%m-%d %H:%M:%S')) if follow_time  else ""
            if now_timestamp - create_time > 1 * 60 or order.cancel == "yes":
                timeout = "true"
            else:
                timeout = "false"
            result = {"id" : order.id, "timeout" : timeout, "user_id" : order.user_id,
                  "item_name" : order.item_name, "price" : order.price,
                  "item_pic" : order.item_pic, "create_time" : create_time_str,
                  "money_pic" : order.money_pic, "follow_id" : order.follow_id,
                  "status" : order.status, "nick_name" : order.nick_name,
                  "follow_time" : follow_time_str, "f_nick_name": order.f_nick_name
                  }
            result_list.append(result)

        return json.dumps(result_list)

class follow_list:
    def GET(self):
        i = web.input()
        openid = i.openid
        order_list = list(db.select('s_order', where="follow_id='%s'"%openid, order="create_time desc"))
        result_list = []
        now = datetime.datetime.now()
        now_timestamp = time.mktime(now.timetuple())
        for order in order_list:
            create_time = order.create_time
            create_time_str = datetime.datetime.fromtimestamp(create_time).strftime(('%Y-%m-%d %H:%M:%S'))
            follow_time = order.follow_time
            follow_time_str = datetime.datetime.fromtimestamp(follow_time).strftime(('%Y-%m-%d %H:%M:%S')) if follow_time else ""

            if now_timestamp - create_time > 1 * 60 or order.cancel == "yes":
                timeout = "true"
            else:
                timeout = "false"
            result = {"id" : order.id, "timeout" : timeout, "user_id" : order.user_id,
                  "item_name" : order.item_name, "price" : order.price,
                  "item_pic" : order.item_pic, "create_time" : create_time_str,
                  "money_pic" : order.money_pic, "follow_id" : order.follow_id,
                  "status" : order.status, "nick_name" : order.nick_name,
                  "follow_time" : follow_time_str, "f_nick_name": order.f_nick_name
                  }
            result_list.append(result)

        return json.dumps(result_list)        


class get_order:
    def GET(self):
        i =  web.input()
        order_id = i.order_id
        order = db.select('s_order', where="id=%s"%order_id)[0]
        now = datetime.datetime.now()
        now_timestamp = time.mktime(now.timetuple())
        create_time = order.create_time
        #大于15分钟或者用户自己取消
        if now_timestamp - create_time > 1 * 60 or order.cancel == "yes":
            timeout = "true"
        else:
            timeout = "false"
        
        create_time_str = datetime.datetime.fromtimestamp(create_time).strftime(('%Y-%m-%d %H:%M:%S'))
        follow_time = order.follow_time
        
        follow_time_str = datetime.datetime.fromtimestamp(follow_time).strftime(('%Y-%m-%d %H:%M:%S')) if follow_time else ""
        result = {"timeout" : timeout, "user_id" : order.user_id, 
                  "item_name" : order.item_name, "price" : order.price, 
                  "item_pic" : order.item_pic, "create_time" : create_time_str, 
                  "money_pic" : order.money_pic, "follow_id" : order.follow_id, 
                  "status" : order.status, "nick_name" : order.nick_name,
                  "follow_time" : follow_time_str, "f_nick_name": order.f_nick_name
                  }
        return json.dumps(result)
        

class follow_order:
    def POST(self):
        i = json.loads(web.data())
        openid = i["openid"]
        now = datetime.datetime.now()
        now_timestamp = time.mktime(now.timetuple())
        f_nick_name = i["f_nick_name"]
        db.update('s_order', where="id=%s"%i["order_id"], follow_id=openid, status="paid", follow_time=now_timestamp, f_nick_name=f_nick_name)
        return "success"


class cancel_order:
    def POST(self):
        i = json.loads(web.data())
        order = db.update('s_order', where="id=%s"%i["order_id"], cancel="yes")
        return "success"



if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
