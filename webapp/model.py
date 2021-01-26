from __future__ import annotations

import settings
from convert import to_dict,to_list,to_string,to_set
from typing import Optional,List
import time

r = settings.r

class Timeline:
    @staticmethod
    def posts(page=1,num=10)->List[Post]:
        start = (page - 1)*num
        end = page*num-1
        posts_id = to_list(r.lrange('timeline',start,end))
        return [Post(pid) for pid in posts_id]

class User:
    def __init__(self,id:str):
        self.id  = str(id)
        udata = to_dict(r.hgetall('user:{}'.format(self.id)))
        self.username = udata['username']
        self.image = udata['image']
        self.gender = udata['gender']
        self.city = udata['city']
        self.intro = udata['intro']
        self.province = udata['province']
        self.bgimage = udata['bgimage']
            

    @staticmethod
    def find_by_id(id:str)->Optional[User]:
        if r.exists('user:{}'.format(str(id))):
            return User(str(id))
        return None

    @staticmethod
    def create(uid:str,userdata:dict)->Optional[User]:
        if not r.exists('user:{}'.format(str(uid))):
            udata = {
                'username':userdata['username'],
                'image':userdata['image'],
                'gender':userdata['gender'],
                'city':userdata['city'],
                'intro':userdata['intro'],
                'province':userdata['province'],
                'bgimage':userdata['bgimage']
            }
            r.hmset('user:{}'.format(uid),udata)
            r.set('user:{}:thumbs'.format(uid),'0')
            r.set('user:{}:views'.format(uid),'0')
        return User(uid)

    def changeinfo(self,udata:dict):
        r.hmset('user:{}'.format(self.id),udata)

    def userinfo(self)->dict:
        return to_dict(r.hgetall('user:{}'.format(self.id)))

    def posts(self)->List[Post]:
        posts_id=to_list(r.lrange('user:{}:posts'.format(self.id),0,9))
        return  [ Post(pid) for pid in posts_id]

    def timeline(self)->List[Post]:
        posts_id=to_list(r.lrange('user:{}:timeline'.format(self.id),0,9))
        return  [ Post(pid) for pid in posts_id]

    def followers(self) -> List[User]:
        followers = to_list(r.smembers('user:{}:followers'.format(self.id)))
        return [ User(uid) for uid in followers]

    def following(self)->List[User]:
        following = to_list(r.smembers('user:{}:following'.format(self.id)))
        return [User(uid) for uid in following]

    def followers_num(self)->int:
        return r.scard('user:{}:followers'.format(self.id))

    def following_num(self)->int:
        return r.scard('user:{}:following'.format(self.id))

    def isfollowing(self,user:User)->bool:
        if self.id != user.id:
            return r.sismember('user:{}:following'.format(self.id),user.id)
        return False

    def add_following(self,user:User)->bool:
        if self.id != user.id:
            r.sadd('user:{}:following'.format(self.id),user.id)
            r.sadd('user:{}:followers'.format(user.id),self.id)
            return True
        return False

    def remove_following(self,user:User)->bool:
        if self.id != user.id:
            r.srem('user:{}:following'.format(self.id),user.id)
            r.srem('user:{}:followers'.format(user.id),self.id)
            return True
        return False
    
    def add_timeline(self,pid:int):
        r.lpush('user:{}:timeline'.format(self.id),pid)

    def getViews(self):
        return to_string(r.get("user:{}:views".format(self.id)))

    def getThumbs(self):
        return to_string(r.get("user:{}:thumbs".format(self.id)))
    
    # def incrViews(self):
    #     r.incr("user:{}:views".format(self.id)) 
    
    # def incrThumbs(self):
    #     r.incr("user:{}:thumbs".format(self.id)) 

    def isThumbs(self,pid):
        return r.sismember('thumbs:{}'.format(pid),self.id)

    def isThumbsComment(self,cid:str):
        return r.sismember('commentthumbs:{}'.format(cid),self.id)

    def isCollect(self,pid):
        return r.sismember('user:{}:collects'.format(self.id),pid)

    def collectpost(self,pid):
        if not r.sismember('user:{}:collects'.format(self.id),pid):
            r.sadd('user:{}:collects'.format(self.id),pid)
            r.incr('post:{}:collects'.format(pid)) 
            return True
        return False

    def uncollectpost(self,pid):
        r.srem('user:{}:collects'.format(self.id),pid)
        r.decr('post:{}:collects'.format(pid))

    def collects(self):
        collects = to_list(r.smembers('user:{}:collects'.format(self.id)))
        return [ Post(pid) for pid in collects]

    def messages(self):
        messages_id=to_list(r.lrange('user:{}:messages'.format(self.id),0,9))
        return  [ Message(mid) for mid in messages_id]
    
    def messagescomment(self):
        messagescomment_id=to_list(r.lrange('user:{}:messagescomment'.format(self.id),0,9))
        return  [ Message(mid) for mid in messagescomment_id]
    
class Post:
    def __init__(self,id:int):
        self.id=id
        pdata = to_dict(r.hgetall('post:{}'.format(self.id)))
        self.userid = pdata['userid']
        self.content = pdata['content']
        self.title = pdata['title']
        self.posttime = pdata['posttime']
        self.faceimage = pdata['faceimage']

    @staticmethod
    def find_by_id(id:int)->Optional[Post]:
        if r.sismember('posts:id',id):
            return Post(int(id))
        return None

    @staticmethod
    def create(user:User,data:dict)->Post:
        uid = user.id
        pid  = r.incr('post:uid')
        pdata = {
            'userid':user.id,
            'content':data['content'],
            'title':data['title'],
            'faceimage':data['faceimage'],
            'posttime':time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        }
        r.hmset('post:{}'.format(pid),pdata)
        r.hmset('post:{}:location'.format(pid),data['location'])
        r.lpush('user:{}:timeline'.format(uid),pid)
        r.lpush('user:{}:posts'.format(uid),pid)
        r.lpush('timeline',pid)
        r.sadd('posts:id',pid)
        r.set('post:{}:thumbs'.format(pid),'0')
        r.set('post:{}:views'.format(pid),'0')
        r.zadd('post:views',{pid:'0'})


        followers = user.followers()
        for follow in followers:
            follow.add_timeline(int(pid))
        return Post(pid)

    def getViews(self):
        return to_string(r.get("post:{}:views".format(self.id)))

    def getThumbs(self):
        return to_string(r.get("post:{}:thumbs".format(self.id)))
    
    def incrViews(self,user:User,postuser:User):
        if not r.sismember('views:{}'.format(self.id),user.id):
            r.sadd('views:{}'.format(self.id),user.id)
            r.incr("post:{}:views".format(self.id)) 
            r.incr("user:{}:views".format(postuser.id)) 
            r.zincrby('post:views',1,self.id)
    
    def incrThumbs(self,user:User,postuser:User):
        if not r.sismember('thumbs:{}'.format(self.id),user.id):
            r.sadd('thumbs:{}'.format(self.id),user.id)
            r.incr('post:{}:thumbs'.format(self.id)) 
            r.incr('user:{}:thumbs'.format(postuser.id)) 
            return True
        return False

    def decrThumbs(self,user:User,postuser:User):
        r.srem("thumbs:{}".format(self.id),user.id)
        r.decr("post:{}:thumbs".format(self.id)) 
        r.decr("user:{}:thumbs".format(postuser.id)) 

    def getLocation(self):
        return to_dict(r.hgetall('post:{}:location'.format(self.id)))

    @staticmethod
    def getHotPost():
        return to_list(r.zrevrange("post:views",0,-1))
    
    def collects_num(self):
        tmp =r.get("post:{}:collects".format(self.id))
        if tmp==None:
            return '0'
        return to_string(tmp)

    def comments(self,openid:str):
        originuser = User.find_by_id(openid)
        cids = to_list(r.lrange('post:{}:comments'.format(self.id),0,-1))
        arr = []
        for cid in cids:
            comment = Comment(cid)
            info = comment.info()
            user = User.find_by_id(info['openid'])
            info['userimage']=user.image
            info['isThumbs']=originuser.isThumbsComment(cid)
            info['thumbs']=comment.getThumbs()
            arr.append(info)
        return arr
            
    def commentsnum(self):
        tmp =r.get("post:{}:commentsnum".format(self.id))
        if tmp==None:
            return '0'
        return to_string(tmp)
    

class Comment:
    def __init__(self,id:int):
        self.id=id
        # cdata = to_dict(r.hgetall('comments:{}'.format(id)))
        # return cdata
    
    def info(self):
        cdata = to_dict(r.hgetall('comments:{}'.format(self.id)))
        return cdata

    @staticmethod
    def cid():
        return r.incr('comments:uid') 

    @staticmethod
    def create(data:dict)->Comment:
        # print(data)
        if data['replyid']!=-1 :
            #几条回复
            howmanyreply = int(to_string(r.hget('comments:{}'.format(data['replyid']),'howmanyreply')))+1
            r.hset('comments:{}'.format(data['replyid']),'howmanyreply',howmanyreply)
            #作者有没有回复
            replycomment = Comment(data['replyid'])
            replycommentinfo = replycomment.info()
            if data['referid']==-1:
                if data['openid']==data['postuserid'] and replycommentinfo['openid']!=data['openid']:
                    authorreply = int(to_string(r.hget('comments:{}'.format(data['replyid']),'authorreply')))+1
                    r.hset('comments:{}'.format(data['replyid']),'authorreply',authorreply)
            else:
                refercomment = Comment(data['referid'])
                refercommentinfo = refercomment.info()
                if data['openid']==data['postuserid'] and refercommentinfo['openid']!=data['openid']:
                    authorreply = int(to_string(r.hget('comments:{}'.format(data['replyid']),'authorreply')))+1
                    r.hset('comments:{}'.format(data['replyid']),'authorreply',authorreply)
                elif data['openid']==data['postuserid'] and refercommentinfo['openid']!=data['openid']:
                    authorreply = int(to_string(r.hget('comments:{}'.format(data['replyid']),'authorreply')))+1
                    r.hset('comments:{}'.format(data['replyid']),'authorreply',authorreply)
                
            r.rpush('subcomments:{}'.format(data['replyid']),data['cid'])
        else:
            r.lpush('post:{}:comments'.format(data['postid']),data['cid'])
            

        # if hostid!=data['userid']:
            # 评论通知效果先不考虑
            # r.lpush('user:{}:comments'.format(data['replyuserid']),cid)        
        r.incr('post:{}:commentsnum'.format(data['postid']))
        r.hmset('comments:{}'.format(str(data['cid'])),data)
        return Comment(data['cid'])
        # 评论通知效果先不考虑
        # r.lpush('post:{}:comments'.format(data['pid']),cid)
        
    @staticmethod
    def find_by_id(id:int)->Optional[Comment]:
        if r.exists('messages:{}'.format(id)):
            return Comment(id)
        return None

    def subcomments(self,openid:str):
        originuser = User.find_by_id(openid)
        cids = to_list(r.lrange('subcomments:{}'.format(self.id),0,-1))
        arr = []
        for cid in cids:
            comment = Comment(cid)
            info = comment.info()
            user = User.find_by_id(info['openid'])
            info['isThumbs']=originuser.isThumbsComment(cid)
            info['thumbs']=comment.getThumbs()
            info['userimage']=user.image
            info['referhead']=''
            info['refercontent']=''
            if str(info['referid'])!='-1':
                refercomment = Comment(info['referid'])
                refercommentinfo = refercomment.info()
                info['referhead']='@'+refercommentinfo['username']+':'
                info['refercontent']=refercommentinfo['content']
                info['referopenid']=refercommentinfo['openid']
            arr.append(info)
        return arr

    def incrThumbs(self,uid:str):
        if not r.sismember('commentthumbs:{}'.format(self.id),uid):
            r.sadd('commentthumbs:{}'.format(self.id),uid)
            r.incr('comment:{}:thumbs'.format(self.id)) 
            return True
        return False

    def decrThumbs(self,uid:str):
        r.srem("commentthumbs:{}".format(self.id),uid)
        r.decr("comment:{}:thumbs".format(self.id)) 
        

    def getThumbs(self):
        tmp =r.get("comment:{}:thumbs".format(self.id))
        if tmp==None:
            return '0'
        return to_string(tmp)


class Message:
    def __init__(self,id:int):
        self.id=id
        mdata = to_dict(r.hgetall('messages:{}'.format(self.id)))
        self.content = mdata['content']
        self.username = mdata['username']
        self.image = mdata['image']
        self.uid= mdata['uid']
        self.time = mdata['time']
        self.type = mdata['type']
        if mdata['type']!='comment':
            self.operate = mdata['operate']
            if mdata['type']=='tcomment':
                self.whouid=mdata['whouid']
                self.who=mdata['who']
            else:
                self.whouid=''
                self.who=''
        else:
            self.refercontent = mdata['refercontent']
    @staticmethod
    def create(user:User,postuserid:str,data:dict)->Message:
        
        tmp = {}
        if user.id!=postuserid:
            if data['type']=='collect': #收藏文章
                post = Post.find_by_id(data['index'])
                tmp['content']=post.title
                tmp['username']=user.username
                tmp['image']=user.image
                tmp['operate']='收藏了你的文章'
                tmp['time']=time.strftime("%Y-%m-%d %H:%M",time.localtime())
                tmp['type']='collect'
            elif data['type']=='tpost':  #点赞文章
                post = Post.find_by_id(data['index'])
                tmp['content']=post.title
                tmp['username']=user.username
                tmp['image']=user.image
                tmp['operate']='赞了你的文章'
                tmp['time']=time.strftime("%Y-%m-%d %H:%M",time.localtime())
                tmp['type']='tpost'
            elif data['type']=='tcomment':
                comment = Comment(data['index'])  
                commentinfo = comment.info()              
                if str(commentinfo['referid'])!='-1':
                    refercomment = Comment(commentinfo['referid'])
                    refercommentinfo = refercomment.info()
                    tmp['who']='@'+refercommentinfo['username']+':'
                    tmp['whouid']=refercommentinfo['openid']
                elif str(commentinfo['replyid'])!='-1':
                    replycomment = Comment(commentinfo['replyid'])
                    replycommentinfo = replycomment.info()
                    tmp['who']='@'+replycommentinfo['username']+':'
                    tmp['whouid']=replycommentinfo['openid']
                else:
                    tmp['who']=''
                    tmp['whouid']=''
                tmp['content']=commentinfo['content']
                tmp['username']=user.username
                tmp['image']=user.image
                tmp['operate']='赞了你的评论'
                tmp['type']='tcomment'
                tmp['time']=time.strftime("%Y-%m-%d %H:%M",time.localtime())
            else:
                openid = data['openid']
                tmp['uid']=user.id
                tmp['username']=user.username
                tmp['image']=user.image
                tmp['time']=data['time']
                tmp['type']='comment'
                print(data)
                if str(data['replyid'])!='-1' and str(data['referid'])=='-1':
                    #至多发两条
                    replycomment = Comment(data['replyid'])
                    replycommentinfo = replycomment.info()
                    if replycommentinfo['openid']!=openid:
                        mid  = r.incr('message:uid')
                        tmp['content']='回复我: '+data['content']
                        tmp['refercontent']='我的评论: '+replycommentinfo['content']
                        r.lpush('user:{}:messagescomment'.format(replycommentinfo['openid']),mid)
                        r.hmset('messages:{}'.format(mid),tmp)
                    if openid!=data['postuserid'] and replycommentinfo['openid']!=data['postuserid']:
                        mid  = r.incr('message:uid')
                        tmp['content']='回复'+replycommentinfo['username']+': '+data['content']
                        tmp['refercontent']=replycommentinfo['username']+'的评论: '+replycommentinfo['content']
                        r.lpush('user:{}:messagescomment'.format(data['postuserid']),mid)
                        r.hmset('messages:{}'.format(mid),tmp)
                if str(data['replyid'])=='-1':
                    #发一条
                    if openid!=data['postuserid']:
                        mid  = r.incr('message:uid')
                        post = Post.find_by_id(data['postid'])
                        tmp['content']=data['content']
                        tmp['refercontent']='我的文章《'+post.title+'》'
                        r.lpush('user:{}:messagescomment'.format(data['postuserid']),mid)
                        r.hmset('messages:{}'.format(mid),tmp)
                if str(data['referid'])!='-1':
                    #发两条
                    refercomment = Comment(data['referid'])
                    refercommentinfo = refercomment.info()
                    if refercommentinfo['openid']!=openid:
                        mid  = r.incr('message:uid')
                        tmp['content']='回复我: '+data['content']
                        tmp['refercontent']='我的评论: '+refercommentinfo['content']
                        r.lpush('user:{}:messagescomment'.format(refercommentinfo['openid']),mid)
                        r.hmset('messages:{}'.format(mid),tmp)
                    if openid!=data['postuserid'] and refercommentinfo['openid']!=data['postuserid']:
                        mid  = r.incr('message:uid')
                        tmp['content']='回复'+refercommentinfo['username']+': '+data['content']
                        tmp['refercontent']=refercommentinfo['username']+'的评论: '+refercommentinfo['content']
                        r.lpush('user:{}:messagescomment'.format(data['postuserid']),mid)
                        r.hmset('messages:{}'.format(mid),tmp)
                #由于下面是通知的数据持久化，跳过
                return
            # print(tmp)
            tmp['uid']=user.id
            mid  = r.incr('message:uid')
            r.lpush('user:{}:messages'.format(postuserid),mid)
            r.hmset('messages:{}'.format(mid),tmp)
        
