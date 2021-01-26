from bottle import route, run, view, request, post, get, BaseRequest
import time, redis, convert, json
from gevent import monkey; monkey.patch_all()
import requests
from model import User,Post,Timeline,Message,Comment

# 5M
BaseRequest.MEMFILE_MAX = 5242880 

@post('/user/create')
def newuser():
    userdata = request.forms.getunicode('userdata')
    userdata = json.loads(userdata)
    openid = request.forms.getunicode('openid')
    user = User.create(openid,userdata)
    if not user:
        return dict(res="老客户",userInfo=user.userinfo())
    return dict(res="新用户",userInfo=user.userinfo())

@post('/article/post')
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

@get('/article/detail/<postid>')
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
        'thumbs':post.getThumbs(),
        'collect_num':post.collects_num(),
        'username':postuser.username,
        'id':post.id,
        'postuserid':postuser.id,
        'title':post.title,
        'posttime':post.posttime,
        'faceimage':post.faceimage,
        'content':post.content,
        'views':views,
        'location':location,
        'comments':comments,
        'commentsnum':commentsnum
    }
    return dict(article=res)

@get('/article/myshow')
def postmyshow():
    # visittimes = r.zincrby('article:visited',1,postid)
    # add user views

    return

@get('/article/timelineshow')
def posttimelineshow():
    uid = request.query.getunicode('openid')
    user = User.find_by_id(uid)
    arr=[]
    for k in user.timeline():
        # tmp = {
        #     'id':k.id,
        #     'userid':k.userid,
        #     'content':k.content,
        #     'title':k.title,
        #     'posttime':k.posttime,
        #     'faceimage':k.faceimage
        # } 
        postuser = User.find_by_id(k.userid)
        tmp = {
            'isThumbs':user.isThumbs(k.id),
            'userimage':postuser.image,
            'thumbs':k.getThumbs(),
            'username':postuser.username,
            'id':k.id,
            'postuserid':k.userid,
            'title':k.title,
            'posttime':k.posttime,
            'faceimage':k.faceimage
        } 
        # console.log(content)
        arr.append(tmp)
    res = {
        'articles':arr
    }
    return res
    # return dict()

@get('/article/hotshow')
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

@post('/article/vote')
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

@get('/user/info')
def userinfo():
    uid = request.query.getunicode('openid')
    
    user = User.find_by_id(uid)
    fansnum = user.followers_num()
    idolnum = user.following_num()
    if not fansnum:
        fansnum='0'
    if not idolnum:
        idolnum='0'
    res = {
        'followers_num':fansnum,
        'following_num':idolnum,
        'views':user.getViews(),
        'thumbs':user.getThumbs(),
        'image':user.image,
        'gender':user.gender,
        # 'city':user.city,
        'username':user.username
    }
    return dict(state=res)

@get('/user/personal')
def userpersonal():
    uid = request.query.getunicode('openid')
    selfuid = request.query.getunicode('selfopenid')
    user = User.find_by_id(uid)
    selfuser = User.find_by_id(selfuid)
    arr=[]
    for k in user.posts():
        # tmp = {
        #     'id':k.id,
        #     'userid':k.userid,
        #     'content':k.content,
        #     'title':k.title,
        #     'posttime':k.posttime,
        #     'faceimage':k.faceimage
        # } 
        tmp = {
            'isThumbs':selfuser.isThumbs(k.id),
            'userimage':user.image,
            'thumbs':k.getThumbs(),
            'username':user.username,
            'id':k.id,
            'postuserid':user.id,
            'title':k.title,
            'posttime':k.posttime,
            'faceimage':k.faceimage
        } 
        # console.log(content)
        arr.append(tmp)
    fansnum = user.followers_num()
    idolnum = user.following_num()
    if not fansnum:
        fansnum='0'
    if not idolnum:
        idolnum='0'
    
    if selfuid==uid :
        followstate='-1'
    else :
        t1 = selfuser.isfollowing(user)
        t2 = user.isfollowing(selfuser)
        if t1 and t2 :
            followstate='1'
        elif t1:
            followstate='2'
        elif t2:
            followstate='3'       
        else:
            followstate='0'       
    
    res = {
        'followers_num':fansnum,
        'following_num':idolnum,
        'views':user.getViews(),
        'thumbs':user.getThumbs(),
        'image':user.image,
        'gender':user.gender,
        'city':user.city,
        'username':user.username,
        'articles':arr,
        'postuserid':uid,
        'followstate':followstate,
        'intro':user.intro,
        'bgimage':user.bgimage,
        'province':user.province
    }
    return dict(state=res)

@get('/user/follow/<uid>')
def userfollow(uid):
    selfuserid = request.query.getunicode('openid')
    user = User.find_by_id(selfuserid)
    postuser = User.find_by_id(uid)
    user.add_following(postuser)

@get('/user/unfollow/<uid>')
def userfollow(uid):
    selfuserid = request.query.getunicode('openid')
    user = User.find_by_id(selfuserid)
    postuser = User.find_by_id(uid)
    user.remove_following(postuser)

# 关注面板
@get('/user/following/detail')
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
@get('/user/followers/detail')
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
        arr.append(tmp)
    return dict(people=arr)


@post('/user/collect/<pid>')
def collectpost(pid):
    openid = request.forms.getunicode('openid')
    postuserid = request.forms.getunicode('postuserid')
    user = User.find_by_id(openid)
    flag = user.collectpost(pid)
    if flag:
        data={
            'type':'collect',
            'index':pid
        }
        Message.create(user,postuserid,data)
    else:
        user.uncollectpost(pid)
    
@post('/user/collected')
def usercollected():
    openid = request.forms.getunicode('openid')
    user = User.find_by_id(openid)
    posts = user.collects()
    arr = []
    for k in posts:
        postuser = User.find_by_id(k.userid)
        tmp = {
            'isThumbs':user.isThumbs(k.id),
            'userimage':postuser.image,
            'thumbs':k.getThumbs(),
            'username':postuser.username,
            'id':k.id,
            'postuserid':k.userid,
            'title':k.title,
            'posttime':k.posttime,
            'faceimage':k.faceimage
        } 
        # console.log(content)
        arr.append(tmp)
    return dict(articles=arr)

@post('/user/message')
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

@post('/user/messagescomment')
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

@get('/comments/cid')
def sendCidToClient():
    cid = Comment.cid()
    return dict(cid=cid)

@post('/comments/create')
def commentscreate():
    data = request.forms.getunicode('data')
    data = json.loads(data)
    Comment.create(data)
    openid = data['openid']
    user = User.find_by_id(openid)
    data['type']='comment'
    Message.create(user,'',data)
    
@post('/comments/sub')
def commentssub():
    replyid = request.forms.getunicode('replyid')
    openid = request.forms.getunicode('openid')
    comment = Comment(replyid)
    data = comment.subcomments(openid)
    return dict(comments=data)
    
@post('/comment/vote')
def commentvote():
    postuserid = request.forms.getunicode('postuserid')
    openid = request.forms.getunicode('openid')
    user = User.find_by_id(openid)
    cid = request.forms.getunicode('cid')
    comment = Comment(cid)
    flag = comment.incrThumbs(openid)
    if flag:
        data={
            'type':'tcomment',
            'index':cid
        }
        Message.create(user,postuserid,data)
    else:
        comment.decrThumbs(openid)
    
@post('/user/changeinfo')
def userchangeinfo():
    openid = request.forms.getunicode('openid')
    userinfo = request.forms.getunicode('userinfo')
    userinfo = json.loads(userinfo)
    user = User.find_by_id(openid)
    user.changeinfo(userinfo)


@get('/user/openid')
def useropenid():
    JSCODE = request.query.getunicode('code')
    SECRET = 'yoursecret'
    APPID = 'yourappid'
    url = 'https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code'.format(appid=APPID,secret=SECRET,code=JSCODE)
    res = requests.get(url)
    return dict(openid=res.json()['openid'])

#run(host='0.0.0.0',server='gevent',reloader=True, port=8888)
run(host='0.0.0.0',port=443,interval=10, certfile='/etc/letsencrypt/live/zj.louiszgm.xin/fullchain.pem', keyfile='/etc/letsencrypt/live/zj.louiszgm.xin/privkey.pem')
