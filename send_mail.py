import os
from django.core.mail import send_mail

os.environ['DJANGO_SETTINGS_MODULE'] = 'Login_site.settings'

if __name__ == '__main__':

    send_mail(
        subject='来自张凯伦的测试邮件',
        message='''各位好：
           测试测试，发邮件发邮件
           这是第二行
           这是第三行                
                            此致敬礼
        ''',
        from_email='15967188037@139.com',
        recipient_list=['15394253459@139.com'],


    )
