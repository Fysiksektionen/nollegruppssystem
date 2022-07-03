from cas import CASClient
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.db.models import Q

import authentication.utils as utils
from .models import AuthUser


class UserCredentialsBackend(ModelBackend):
    """ Backend defining authentication for users using username and password or email and password. """

    def authenticate(self, request, email=None, password=None, **kwargs):
        """If given email and password, try to authenticate. Else, do default auth."""
        if email is None:
            email = kwargs.get(AuthUser.EMAIL_FIELD)
        if email is None or password is None:
            return super().authenticate(request=request, password=password, **kwargs)

        try:
            user = AuthUser._default_manager.get(**{AuthUser.EMAIL_FIELD: email})
        except AuthUser.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            AuthUser().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

class CASBackend(ModelBackend):
    """ Backend defining authentication for users using CAS login. """

    def authenticate(self, request, **kwargs):
        """
        Method to verify CAS-tickets.

        :param request: HttpRequest to verification page.
        :param ticket: Ticket to verify (as string).
        :param service: Service url to use in verification.

        :returns user: User instance or None if not verified.
        """
        try:
            ticket = kwargs['ticket']
            service = kwargs['service']
        except KeyError:
            return None
        user_model = AuthUser

        # Attempt to verify the ticket with the institution's CAS server
        client = CASClient(version=2, service_url=service,
                           server_url=str(utils.get_setting('CAS_SERVER_URL')))
        username, attributes, pgtiou = client.verify_ticket(ticket)

        # Add the attributes returned by the CAS server to the session
        if request and attributes:
            request.session['attributes'] = attributes

        # If no username was returned, verification failed
        if not username:
            return None

        # Try to find user
        try:
            user = user_model.objects.get_by_natural_key(username)
        except user_model.DoesNotExist:
            user = None

        return user if self.user_can_authenticate(user) else None


class FakeCASBackend(CASBackend):
    """ Fake backend authorizing simple fake tickets """

    def authenticate(self, request, **kwargs):
        """
        Authenticates a fake ticket containing the user's username.
        Returns matching user if username exists and None if the user does not exist.
        """
        try:
            ticket = kwargs['ticket']
            service = kwargs['service']
        except KeyError:
            return None
        user_model = AuthUser

        # Try to find user
        try:
            user = user_model.objects.get_by_natural_key(ticket)
        except user_model.DoesNotExist:
            user = None

        return user if self.user_can_authenticate(user) else None


class MultipleGroupCategoriesBackend(ModelBackend):
    """ Backend for dealing with multiple groups permissions. """

    def authenticate(self, *args, **kwargs):
        return None

    def user_can_authenticate(self, user):
        return False

    def _get_group_permissions(self, user_obj):
        user_model = get_user_model()

        # If list of groups exist, is not None and not empty
        if hasattr(user_model, 'PERMISSION_GROUPS') and user_model.PERMISSION_GROUPS and len(
                user_model.PERMISSION_GROUPS) != 0:
            query = Q()

            # For all fields in the list
            for group_type_name in user_model.PERMISSION_GROUPS:
                group_field = getattr(user_obj, group_type_name)

                # If group_field is an instance of Group (or subclass)
                if isinstance(group_field, Group):
                    query = query | Q(**{'group': group_field})
                # Else assume that it's a ForignKey or many-to-many relation.
                else:
                    list_of_groups = []
                    try:
                        list_of_groups = group_field.all()
                        # Is many-to-many
                    except:
                        if isinstance(group_field, Group):
                            # Is ForeignKey
                            list_of_groups = [group_field]
                        elif group_field is None:
                            # Is nulled field or otherwise None
                            continue
                        else:
                            # Something else
                            raise Exception("%s is not an acceptable field for permission handling 1." % group_type_name)

                    for group in list_of_groups:
                        # If group_field is an instance of Group (or subclass)
                        if isinstance(group, Group):
                            query = query | Q(**{'group': group})
                        else:
                            raise Exception("%s is not an acceptable field for permission handling 2." % group_type_name)

            return Permission.objects.filter(query)
        else:
            return Permission.objects.none()
