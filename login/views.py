from django.shortcuts import render
from django.shortcuts import redirect
from . import models, forms
from django.conf import settings
from django.utils import timezone
import hashlib
import datetime



# Create your views here.


def hash_code(s, salt='Jacob'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()


def make_confirm_string(user):
    now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, salt=now)   # 用户名和创建时间hash成一个独一无二的确认码
    models.ConfirmString.objects.create(code=code, user=user,)     # 填表：填ConfirmString这个表，即创建model的一个实例：填充外键字段和code字段
    return code     # 返回确认码
def send_email(dst_email, code):

    from django.core.mail import EmailMultiAlternatives

    subject = '来自www.zhangkailun.com的注册确认邮件'

    text_content = '''感谢注册www.zhangkailun.com，这里是kai的测试站点！\
                       如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请联系管理员！'''

    html_content = '''
                       <p>感谢注册农夫山泉有点甜，火锅底料有点咸 网<a href="http://{}/confirm/?code={}" target=blank>www.youdiantian.com/confirm_get</a></p>
                       <p>请点击上方链接完成注册确认！</p>
                       <p>此链接有效期为{}天！</p>
                       '''.format('127.0.0.1:8000', code, settings.CONFIRM_DAYS)

    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [dst_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def index(request):
    pass
    return render(request, 'login/index.html')


def login(request):
    if request.session.get('is_login', None):
        return redirect('index')
    if request.method == 'POST':
        # username = request.POST.get('username', None)  # 当数据请求中没有username键时不会抛出异常，而是返回一个我们指定的默认值None
        # password = request.POST.get('password', None)
        login_form = forms.UserForm(request.POST)
        message = '所有字段都必须填写！'
        # if username and password:  # 确保用户名和密码都不为空
        #     username = username.strip()
        #     # 用户名字符合法性验证
        #     # 密码长度验证
        #     # 更多的其它验证.....

        if login_form.is_valid():   # 验证，如果传入的数据合法
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            try:
                user = models.User.objects.get(name=username)
                if not user.has_confirmed:              # 检查改用户是否已经邮件确认过确认码
                    message = "该用户还未通过邮件确认！"
                    return render(request, 'login/login.html', locals())
                if user.password == hash_code(password):    # 明文密码的哈希值和数据库内的值进行比对
                    request.session['is_login'] = True
                    request.session['user_id'] = user.id
                    request.session['user_name'] = user.name
                    return redirect('index')
                else:
                    message = "密码不正确！"
            except:
                message = "用户名不存在！"
        return render(request, 'login/login.html', locals())  # 必须传回locals()，因为要在template中使用表单实例，而且把原先填写的数据也传回，方便用户修改
    login_form = forms.UserForm()                           # 如果没有收到POST请求，则应该是初次登录，返回一个空表单
    return render(request, 'login/login.html', locals())


def register(request):
    if request.session.get('is_login', None):
        # 登录状态不允许注册。可以修改这个逻辑
        return redirect('index')
    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写的内容！(填写内容不合法)"
        if register_form.is_valid():
            username = register_form.cleaned_data['username']
            password1 = register_form.cleaned_data['password1']
            password2 = register_form.cleaned_data['password2']
            email = register_form.cleaned_data['email']
            sex = register_form.cleaned_data['sex']
            if password1 != password2:
                message = '两次输入的密码不同！'
                return render(request, 'login/register.html', locals())
            else:
                # 返回满足查询参数的对象集合，没有满足则返回一个空的查询集<QuerySet []>，所以不会报错
                same_name_user = models.User.objects.filter(name=username)
                same_email_user = models.User.objects.filter(email=email)
                print(same_email_user)
                if same_name_user:  # 用户名唯一
                    message = '用户已经存在，请重新选择用户名！'
                    return render(request, 'login/register.html', locals())
                if same_email_user:  # 邮箱地址唯一
                    message = '该邮箱地址已被注册，请使用别的邮箱！'
                    return render(request, 'login/register.html', locals())

                # 当一切都OK的情况下，创建新用户

                new_user = models.User()
                new_user.name = username
                new_user.password = hash_code(password1)  # 使用加密密码，存入数据库
                new_user.email = email
                new_user.sex = sex
                new_user.save()

                code = make_confirm_string(new_user)
                send_email(email, code)

                message = '请前往注册邮箱，进行邮件确认！'
                return render(request, 'login/confirm.html', locals())  # 跳转到等待邮件确认页面

    register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        # 如果没有登录,返回首页
        return redirect('index')
    request.session.flush()  # flush()方法是比较安全的一种做法，而且一次性将session中的所有内容全部清空
    # 或者使用下面的方法
    # del request.session['is_login']
    # del request.session['user_id']
    # del request.session['user_name']

    # return redirect("/index/")
    return redirect('index')    # 反向解析URL --> /index/


def user_confirm(request):
    code = request.GET.get('code', None)
    message = ''
    try:
        confirm = models.ConfirmString.objects.get(code=code)
    except:
        message = '无效的确认请求！'
        return render(request, 'login/confirm.html', locals())

    # 确认码存在数据库中
    c_time = confirm.c_time
    now = timezone.now()
    if now > c_time + datetime.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()   # 删除已注册但过期未确认邮件的账号，因为on_delete参数设为了CASCADE，所有confirm对象也会被删除，就不用多写一条confirm.delete()
        message = '您的邮件已经过期！请重新注册！'
        return render(request, 'login/confirm.html', locals())
    else:
        confirm.user.has_confirmed = True  # 更改用户状态为已确认
        confirm.user.save()
        confirm.delete()
        message = '感谢确认，恭喜您，注册成功！请使用账户登录！'
        return render(request, 'login/confirm.html', locals())



