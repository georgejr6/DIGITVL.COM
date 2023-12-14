import random
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import get_template
from django.utils import timezone

from djstripe.models import Customer, Subscription
from easy_thumbnails.fields import ThumbnailerImageField
from phonenumber_field.modelfields import PhoneNumberField

from beats.utils import get_username_unique_slug
from rest_framework.authtoken.models import Token


def generate_user_verification_code():
    n = 6
    return random.randint(10 ** (n - 1), 10 ** n - 1)


class BaseTimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Custom User Manager for email field login
class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("email is required")
        email = self.normalize_email(email)
        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        """creates new super user with details """

        user = self.create_user(email, username, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100, blank=False)
    username = models.CharField(max_length=100, unique=True, db_index=True, validators=[UnicodeUsernameValidator()])
    phone_number = PhoneNumberField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=250, null=True, blank=True)
    username_slug = models.SlugField(max_length=200, db_index=True, blank=True, null=True)
    algorand_public_address = models.CharField(max_length=255, null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):

        if not self.username_slug and self.pk:
            slug_str = f'{self.username}'
            self.username_slug = get_username_unique_slug(self, slug_str, User.objects)
            # print(self.id)
            # token = Token.objects.create(user_id=self.pk)
            # self.email_verification_token = token.key

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    @property
    def profile_pic(self):
        return self.profile.avatar.url

    # email verification code

    def reset_password(self):
        upr = UserPasswordReset.objects.create(reset_code=generate_user_verification_code(), user=self)
        return upr

    def reset_password_verify_code(self, code, confirmed=False):
        try:
            upr = self.userpasswordreset_set.get(reset_code=int(code), confirmed=False)
            if upr:
                upr.confirmed = confirmed
                upr.save()

                # send_welcome_email(self)

                return True
            else:
                return False
        except UserPasswordReset.DoesNotExist:
            return False
        except:
            # traceback.print_exc()
            return False

    def __str__(self):
        return self.username


# password Rest Model
class UserPasswordReset(BaseTimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_code = models.CharField(max_length=6)

    reset_code_sent_at = models.DateTimeField(null=True, blank=True)

    confirmed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'User Password Reset'
        verbose_name_plural = 'User Password Resets'

    @property
    def reset_code_str(self):
        rc = str(self.reset_code)
        return rc[:3] + rc[3:]

    def send_reset_password_email(self):
        password_reset_email_template_html = 'users/emails/password_reset/request.html'

        sender = '"Digitvl" <noreply.digitvlhub@gmail.com>'
        send_to = [self.user.email]
        headers = {'Reply-To': 'do-not-reply@digitvl.com'}

        mail_subject = "Reset Password"

        template_context = {
            'reset_code': self.reset_code_str
        }

        html_message = get_template(password_reset_email_template_html)
        html_content = html_message.render(template_context)
        email = EmailMultiAlternatives(
            subject=mail_subject, from_email=sender, to=send_to, headers=headers
        )
        email.attach_alternative(html_content, 'text/html')
        email.send()

        self.reset_code_sent_at = timezone.now()
        self.save()

        return True


@receiver(post_save, sender=UserPasswordReset)
def send_user_password_reset_email(sender, instance, created, **kwargs):
    if created:
        instance.send_reset_password_email()


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    avatar = ThumbnailerImageField(upload_to='users/%Y/%m/%d/', resize_source=dict(size=(250, 250), sharpen=True),
                                   default='avatar.jpg')
    cover_photo = ThumbnailerImageField(upload_to='users/%Y/%m/%d/', resize_source=dict(size=(900, 300), blank=True))
    blue_tick_verified = models.BooleanField(default=False)
    website_link = models.URLField(null=True, blank=True)
    instagram_link = models.URLField(null=True, blank=True)
    twitter_link = models.URLField(null=True, blank=True)
    facebook_link = models.URLField(null=True, blank=True)
    youtube_link = models.URLField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    class Meta:
        ordering = ('-created',)

    @property
    def get_absolute_image_url(self, request=None):
        return request.build_absolute_uri(self.avatar.url, request=request)

    @property
    def username_slug(self):
        return self.user.username_slug

    @property
    def followers_count(self):
        return self.user.followers.count()

    @property
    def following_count(self):
        return self.user.following.count()

    @property
    def full_name(self):
        return self.user.full_name

    @property
    def track_count(self):
        return self.user.beats.count()

    @property
    def username(self):
        return self.user.username

    @property
    def get_subscription_badge(self):
        return self.user.membership_plan.subscription_badge

    def __str__(self):
        return f'Profile for user {self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Contact(models.Model):
    user_from = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  related_name='rel_from_set',
                                  on_delete=models.CASCADE)
    user_to = models.ForeignKey(settings.AUTH_USER_MODEL,
                                related_name='rel_to_set',
                                on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f'{self.user_from} follows {self.user_to}'


# Add following field to User dynamically
user_model = get_user_model()
user_model.add_to_class('following',
                        models.ManyToManyField('self',
                                               through=Contact,
                                               related_name='followers',
                                               symmetrical=False))

class SendImportantAnnouncement(models.Model):
    message  = models.TextField(help_text='Message Should Be Concise.')
    created_at = models.DateTimeField(auto_now_add=True,
                                  db_index=True)

    def __str__(self):
        return self.message[:12]
