from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

import authentication.models as auth_models
from nollesystemet.managers import UserProfileManager
from .misc import validate_no_emoji, IntegerChoices


class NolleGroup(models.Model):
    """
    Model for "nØllegrupper". Also contains extra information on the group itself.
    """
    name = models.CharField(verbose_name="Namn", max_length=150, unique=True, null=False, blank=False, validators=[validate_no_emoji])
    description = models.TextField(blank=True, validators=[validate_no_emoji])
    logo = models.ImageField(null=True, blank=True)
    group_photo = models.ImageField(null=True, blank=True)
    schedule = models.ImageField(null=True, blank=True)
    forfadders = models.ManyToManyField('UserProfile', blank=True, related_name='responsible_nolle_group')

    class Meta:
        verbose_name = 'nØllegrupp'
        verbose_name_plural = 'nØllegrupper'

    def __str__(self):
        return str(self.name)

    @staticmethod
    def is_forfadder(user):
        return user.user_type == UserProfile.UserType.FORFADDER

    @staticmethod
    def get_forfadder_group(user, accept_multiple=False):
        if NolleGroup.is_forfadder(user):
            if accept_multiple:
                return NolleGroup.objects.filter(forfadders=user)
            else:
                return NolleGroup.objects.get(forfadders=user)
        else:
            return None


class UserProfile(auth_models.UserProfile):
    """
    Customized UserProfile model for nollesystemet. Defines all info relevant about a user.
    Objects of this model should be the model to interact with form other model in nollessytemet,
    like Happening and Registration.
    """

    class UserType(IntegerChoices):
        """
        Enum target for choices of UserProfile.user_type
        """
        FADDER = 1, _("Fadder")
        NOLLAN = 2, _("nØllan")
        SENIOR = 3, _("Senior")
        EXTERNAL = 4, _("Extern")
        ADMIN = 5, _("Administrativ")
        FORFADDER = 6, _("Förfadder")

    class Program(IntegerChoices):
        """
        Enum target for choices of UserProfile.user_type
        """
        NONE = 0, _("Inget")
        CTFYS = 1, _("Teknisk fysik")
        CTMAT = 2, _("Teknisk matematik")

    user_type = models.PositiveSmallIntegerField(verbose_name="Användartyp",
                                                 choices=UserType.choices, blank=False, null=False)
    nolle_group = models.ForeignKey(NolleGroup, verbose_name="nØllegrupp", blank=True, null=True,
                                    on_delete=models.SET_NULL)

    program = models.PositiveSmallIntegerField(blank=False, null=False, choices=Program.choices, default=Program.NONE)

    kth_id = models.CharField(max_length=20, blank=True, validators=[validate_no_emoji])
    phone_number = models.CharField(max_length=30, blank=True, validators=[validate_no_emoji])
    food_preference = models.TextField(blank=True, validators=[validate_no_emoji])

    objects = UserProfileManager()

    class Meta(auth_models.UserProfile.Meta):
        permissions = [
            ("see_users", "Can see any user profile"),
            ("edit_users", "Can edit any user profile"),
            ("edit_system", "Can edit the system itself"),
        ]
        verbose_name = 'Användarprofil'
        verbose_name_plural = 'Användarprofiler'

    @property
    def type(self):
        return UserProfile.UserType(self.user_type).label

    @property
    def program_name(self):
        return UserProfile.Program(self.program).label

    def has_perm(self, codename):
        """ :return Boolean indicating if user has specified permission. """
        return self.auth_user.has_perm(codename)

    @staticmethod
    def can_create(observing_user):
        """ :return Boolean indicating if observing_user has the right to create a new user. """
        return observing_user.has_perm('nollesystemet.edit_users')

    def can_see(self, observing_user):
        """ :return Boolean indicating if observing_user has the right to see the profile of calling user. """
        if self.can_edit(observing_user):  # Has permission to edit the user
            return True
        if NolleGroup.is_forfadder(observing_user):  # Is forfadder for the user
            if self.nolle_group in NolleGroup.get_forfadder_group(observing_user, accept_multiple=True):
                return True
        if observing_user.has_perm('nollesystemet.see_users'):  # Has correct permission
            return True
        return False

    def can_edit(self, observing_user):
        """ :return Boolean indicating if observing_user has the right to edit the profile of calling user. """
        if observing_user == self:  # Is their own profile
            return True
        if observing_user.has_perm('nollesystemet.edit_users'):  # Has correct permission
            return True
        return False

    def can_see_registrations(self, observing_user):
        """ :return Boolean indicating if observing_user has the right to see the registrations of calling user. """
        return self.can_see(observing_user)

    def can_see_nolleForm_answer(self, observing_user):
        """ :return Boolean indicating if observing_user has the right to see the nolleForm of calling user. """
        try:
            has_answer = (self.nolleformanswer is not None)
        except apps.get_model('nollesystemet.NolleFormAnswer').DoesNotExist:
            has_answer = False
        return has_answer and self.can_see(observing_user)

    @staticmethod
    def can_edit_groups(observing_user):
        """ :return Boolean indicating if observing_user has the right to edit the groups of calling user. """
        return observing_user.has_perm('nollesystemet.edit_users')

    @staticmethod
    def can_see_some_user(observing_user):
        """ :return Boolean indicating if observing_user has the right to see the profile of some user. """
        # If can see more than one user. Larger than 1 because all users can see their own profile
        return len(
            [True for user in UserProfile.objects.all() if user.can_see(observing_user)]
        ) > min(1, UserProfile.objects.count() - 1)

    @staticmethod
    def can_edit_some_user(observing_user):
        """ :return Boolean indicating if observing_user has the right to edit the profile of some user. """
        # If can edit more than one user. Larger than 1 because all users can edit their own profile
        return len(
            [True for user in UserProfile.objects.all() if user.can_edit(observing_user)]
        ) > min(1, UserProfile.objects.count() - 1)

    def is_responsible_forfadder(self, potential_forfadder):
        """ :return Boolean indicating if potential_forfadder is the forfadder of calling user. """
        if not NolleGroup.is_forfadder(potential_forfadder):
            return False
        else:
            return self.nolle_group in NolleGroup.get_forfadder_group(potential_forfadder, accept_multiple=True)

    def is_nollan(self):
        return self.user_type == UserProfile.UserType.NOLLAN

    def is_fadder(self):
        return self.user_type == UserProfile.UserType.FADDER or self.user_type == UserProfile.UserType.FORFADDER

    @staticmethod
    def update_user(username, email, password=None, **kwargs):
        auth_user = apps.get_model(settings.AUTH_USER_MODEL).objects.get(username=username)

        prev_email = auth_user.email
        auth_user.email = email

        if not auth_user.has_usable_password():
            if password:
                auth_user.set_password(password)
            else:
                auth_user.set_unusable_password()

        try:
            auth_user.save()
        except ValidationError as e:
            raise e

        if 'kth_id' in kwargs and kwargs['kth_id'] is None:
            kwargs.pop('kth_id')
        user_profile = UserProfile.objects.get(pk=auth_user.profile.pk)

        try:
            for field_name, field_value in kwargs.items():
                user_profile.__setattr__(field_name, field_value)
            user_profile.save()
        except ValidationError as e:
            auth_user.email = prev_email
            auth_user.save()
            raise e

        return user_profile

    @staticmethod
    def create_new_user(username, email, password=None, **kwargs):
        auth_user = apps.get_model(settings.AUTH_USER_MODEL)(username=username, email=email)
        if password:
            auth_user.set_password(password)
        else:
            auth_user.set_unusable_password()

        try:
            auth_user.save()
        except ValidationError as e:
            raise e

        if 'kth_id' in kwargs and kwargs['kth_id'] is None:
            kwargs.pop('kth_id')
        user_profile = UserProfile(**kwargs, auth_user=auth_user)
        try:
            user_profile.save()
        except ValidationError as e:
            apps.get_model(settings.AUTH_USER_MODEL).objects.get(pk=auth_user.pk).delete()
            raise e

        return user_profile


@receiver(models.signals.post_delete, sender=UserProfile)
def delete_auth_user(sender, instance, *args, **kwargs):
    """ Deletes image files on `post_delete` """
    try:
        if instance.auth_user:
            instance.auth_user.delete()
    except:
        pass