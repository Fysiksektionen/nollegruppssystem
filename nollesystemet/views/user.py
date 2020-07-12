from django.apps import apps
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView


import nollesystemet.models as models
import nollesystemet.forms as forms
import nollesystemet.mixins as mixins
from .misc import MultipleObjectsUpdateView, ModifiableModelFormView


class ProfilePageView(mixins.FadderietMixin, ModifiableModelFormView):
    model = models.UserProfile
    form_class = forms.ProfileUpdateForm
    deletable = False
    submit_name = "Spara"
    exclude_fields = ('nolle_group', 'user_type', 'groups')

    template_name = 'fadderiet/mina-sidor/profil.html'
    success_url = reverse_lazy('fadderiet:mina-sidor:profil')

    login_required = True

    extra_context = {
        'change_password_url': reverse_lazy('fadderiet:byt-losenord:index')
    }

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_is_editable_args(self):
        return [self.request.user.profile]


class UsersListView(mixins.FohserietMixin, ListView):
    model = models.UserProfile
    template_name = 'fohseriet/anvandare/index.html'

    login_required = True
    permission_required = 'nollesystemet.edit_user_info'

    ordering = 'first_name'

    extra_context = {
        'user_types': models.UserProfile.UserType.names,
        'nolle_groups': models.NolleGroup.objects.all()
    }

    def get_queryset(self):
        self.queryset = models.UserProfile.objects.all()
        querryset = super().get_queryset()
        return [{
            'user': user,
            'can_edit': user.can_edit(self.request.user.profile),
            'can_see': user.can_see(self.request.user.profile),
            'form': forms.ProfileUpdateForm(instance=user, editable=False)
        } for user in querryset]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'can_create': models.UserProfile.can_create(self.request.user.profile)
        })
        return context


class UserUpdateView(mixins.FohserietMixin, ModifiableModelFormView):
    model = models.UserProfile
    form_class = forms.ProfileUpdateForm
    deletable = True
    submit_name = "Spara"

    template_name = 'fohseriet/anvandare/redigera.html'
    success_url = reverse_lazy('fohseriet:anvandare:index')

    login_required = True
    permission_required = 'nollesystemet.edit_user_info'

    def get_is_editable_args(self):
        return [self.request.user.profile]

    def get_object(self, queryset=None):
        if 'pk' not in self.kwargs:
            return None
        return super().get_object(queryset=queryset)

class UserRegistrationsListView(mixins.FohserietMixin, ListView):
    model = models.Registration
    template_name = 'fohseriet/anvandare/anmalningar.html'

    login_required = True
    permission_required = 'nollesystemet.edit_user_info'

    def query_test_func(self, registration):
        return self.request.user.has_perm(
            'nollesystemet.edit_user_registration') or self.request.user.profile in registration.happening.editors.all()

    def get_queryset(self):
        try:
            self.queryset = models.Registration.objects.filter(user=models.UserProfile.objects.get(pk=self.kwargs['pk']))
            return [{'registration': registration, 'user_can_edit': self.query_test_func(registration)} for registration
                    in super().get_queryset()]
        except:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user_of_registrations': models.UserProfile.objects.get(pk=self.kwargs['pk']),
            'back_url': reverse('fohseriet:anvandare:index'),
        })
        return context
