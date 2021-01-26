#!/usr/bin/python
'''
A basic bottle app skeleton
'''



from bottle import route, request, post, get,Bottle,run 
import time, redis, convert, json
import requests
from model import User,Post,Timeline,Message,Comment

app = Bottle()


# 5M
BaseRequest.MEMFILE_MAX = 5242880 

@app.post('/user/create')
def newuser():
    userdata = request.forms.getunicode('userdata')
    userdata = json.loads(userdata)
    openid = request.forms.getunicode('openid')
    user = User.create(openid,userdata)
    if not user:
        return dict(res="老客户",userInfo=user.userinfo())
    return dict(res="新用户",userInfo=user.userinfo())

@app.post('/article/post')
def postdeal():
    openid = request.forms.getunicode('openid')
    title = request.forms.getunicode('title')
    content = request.forms.getunicode('content')
    faceimage = request.forms.getunicode('faceimage')
    location = request.forms.getunicode('location')
    data={
        'title':title,
        'content':content,
        'faceimage':faceimage,
        'location':json.loads(location),
    }
    user = User.find_by_id(openid)
    Post.create(user,data)
    return dict(res="server post deal succ")

@app.get('/article/detail/<postid>')
def postdetail(postid):
    uid = request.query.getunicode('openid')
    postuserid = request.query.getunicode('postuserid')
    user = User.find_by_id(uid)
    postuser = User.find_by_id(postuserid)

    post = Post.find_by_id(postid)
    post.incrViews(user,postuser)
    views = post.getViews()
    thumbs = post.getThumbs()
    postuser = User.find_by_id(post.userid)
    isThumbs = user.isThumbs(postid)
    location = post.getLocation()
    comments = post.comments(uid)
    commentsnum = post.commentsnum()
    res = {
        'isCollect':user.isCollect(post.id),
        'isThumbs':user.isThumbs(post.id),
        'userimage':postuser.image,



@app.get('/article/hotshow')
def posthotshow():
    uid = request.query.getunicode('openid')
    user = User.find_by_id(uid)
    raw_postid_data = Post.getHotPost()    
    arr = []
    for raw_postid in raw_postid_data:
        postid = raw_postid
        post = Post.find_by_id(postid)
        postuser = User.find_by_id(post.userid)
        
        tmp = {
            'isThumbs':user.isThumbs(post.id),
            'userimage':postuser.image,
            'thumbs':post.getThumbs(),
            'username':postuser.username,
            'id':post.id,
            'postuserid':post.userid,
            'title':post.title,
            'posttime':post.posttime,
            'faceimage':post.faceimage
        } 
        # new_data[postid]=data
        arr.append(tmp)
    return dict(articles=arr)

@app.post('/article/vote')
def postvote():
    openid = request.forms.getunicode('openid')
    postuserid = request.forms.getunicode('postuserid')
    postid = request.forms.getunicode('postid')
    user = User.find_by_id(openid)
    postuser = User.find_by_id(postuserid)
    post = Post.find_by_id(postid)
    flag = post.incrThumbs(user,postuser)
    if flag:
        data={
            'type':'tpost',
            'index':postid
        }
        Message.create(user,postuserid,data)
    else:
        post.decrThumbs(user,postuser)

@app.get('/user/info')
def userinfo():
    uid = request.query.getunicode('openid')
    
    user = User.find_by_id(uid)



@app.get('/user/follow/<uid>')
def userfollow(uid):
    selfuserid = request.query.getunicode('openid')
    user = User.find_by_id(selfuserid)
    postuser = User.find_by_id(uid)
    user.add_following(postuser)

@app.get('/user/unfollow/<uid>')
def userfollow(uid):
    selfuserid = request.query.getunicode('openid')
    user = User.find_by_id(selfuserid)
    postuser = User.find_by_id(uid)
    user.remove_following(postuser)

# 关注面板
@app.get('/user/following/detail')
def userfollowingdetail():
    postuserid = request.query.getunicode('postuserid')
    postuser = User.find_by_id(postuserid)
    users = postuser.following()
    arr = []
    for user in users:
        tmp = {
            'gender':user.gender,
            'username':user.username,
            'intro':user.intro,
            'image':user.image,
            'id':user.id
        }
        arr.append(tmp)
    return dict(people=arr)

# 粉丝面板
@app.get('/user/followers/detail')
def userfollowersdetail():
    postuserid = request.query.getunicode('postuserid')
    
    postuser = User.find_by_id(postuserid)
    users = postuser.followers()
    
    arr = []
    for user in users:
        tmp = {
            'gender':user.gender,
            'username':user.username,
            'intro':user.intro,
            'image':user.image,
            'id':user.id
        }



@app.post('/user/message')
def usermessage():
    openid = request.forms.getunicode('openid')
    user = User.find_by_id(openid)
    messages = user.messages()
    arr = []
    for k in messages:
        tmp={
            'image':k.image,
            'username':k.username,
            'content':k.content,
            'time':k.time,
            'operate':k.operate,
            'type':k.type,
            'whouid':k.whouid,
            'who':k.who,
            'uid':k.uid
        }
        arr.append(tmp)
    return dict(messages=arr)

@app.post('/user/messagescomment')
def usermessagecomment():
    openid = request.forms.getunicode('openid')
    user = User.find_by_id(openid)
    messagescomment = user.messagescomment()
    arr = []
    for k in messagescomment:
        tmp={
            'image':k.image,
            'username':k.username,
            'content':k.content,
            'time':k.time,
            'uid':k.uid,
            'refercontent':k.refercontent
        }
        arr.append(tmp)
    return dict(messagescomment=arr)

@app.get('/comments/cid')
def sendCidToClient():
    cid = Comment.cid()
    return dict(cid=cid)

@app.post('/comments/create')
def commentscreate():
    data = request.forms.getunicode('data')
    data = json.loads(data)
    Comment.create(data)



@app.get('/my')
def show_index():
    '''
    The front "index" page
    '''
    return dict(res='zoujian')




class StripPathMiddleware(object):
    '''
    Get that slash out of the request
    '''
    def __init__(self, a):
        self.a = a
    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.a(e, h)

if __name__ == '__main__':
    run(app=StripPathMiddleware(app),
        host='0.0.0.0',
        port=8080)
