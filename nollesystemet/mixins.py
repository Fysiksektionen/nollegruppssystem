import json
import os
import re
import sys
import urllib

from django.apps import apps
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseRedirect
from django.template import Template, Context
from django.urls import reverse, reverse_lazy
from django.views.generic.base import ContextMixin
import django.contrib.staticfiles.finders as finders
import logging

import nollesystemet.models as models


class MenuMixin(ContextMixin):
    menu_items_static_file = None

    def get_context_data(self, **kwargs):
        context = {}
        try:
            path = ""
            if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
                path = finders.find(self.menu_items_static_file)
            else:
                path = os.path.join(settings.STATIC_ROOT, self.menu_items_static_file)

            with open(path, encoding='utf-8') as json_file:
                data = json.load(json_file)
                order = data['order']
                menu_items = data['menu_items']
        except:
            raise FileNotFoundError("menu_items_static_file not set or not able to be read.")

        if not order or not menu_items:
            raise SyntaxError("order or menu_items not found in file %s" % path)

        menu = {'left': [], 'right': []}
        for items in order:
            if not isinstance(items, list):
                items = [items]

            for item in items:
                info = menu_items[item]

                render = self.check_if_to_render(info)

                if render:
                    menu[info['align']].append({
                        **info,
                        'url': reverse(info['url_name'])
                    })

                    if not 'selected_url_regex' in info:
                        info['selected_url_regex'] = '.*'
                    if re.search(menu[info['align']][-1]['url'] + info['selected_url_regex'], self.request.path):
                        menu[info['align']][-1]['classes'] = \
                            (info['classes'] + ' ' if 'classes' in info else '') + 'selected'
                    break

        if menu:
            context['menu'] = menu
        context.update(kwargs)
        return super().get_context_data(**context)

    def check_if_to_render(self, info):
        if "conditions" in info:
            conditions = info["conditions"]

            for key in conditions.keys():
                if key not in ["logged-in", "methods", "permissions"]:
                    raise Exception(
                        "Wrongly configured menu file."
                        "For menu-item %s the conditions parameter can not have key %s.",
                        (info["name"], key))

            auth_render = False
            if "logged-in" in conditions:
                if conditions["logged-in"] == "True":
                    auth_render = self.request.user.is_authenticated
                elif conditions["logged-in"] == "False":
                    auth_render = not self.request.user.is_authenticated
                elif conditions["logged-in"] == "any":
                    auth_render = True
                else:
                    raise Exception(
                        "Wrongly configured menu file. "
                        "For menu-item %s the conditions.logged-in parameter can not have key %s.",
                        (info["name"], conditions["logged-in"]))
            else:
                auth_render = True

            methods_render = False
            if "methods" in conditions:
                if self.request.user.is_authenticated:
                    for key in conditions["methods"].keys():
                        if key not in ["all", "any"]:
                            raise Exception(
                                "Wrongly configured menu file."
                                "For menu-item %s the conditions.methods parameter can not have key %s.",
                                (info["name"], key))
                    if "any" in conditions["methods"]:
                        for method_string in conditions["methods"]["any"]:
                            split = method_string.split(".")
                            model = apps.get_model(app_label=split[0], model_name=split[1])
                            methods_render |= getattr(model, (split[2]))(self.request.user.profile)
                    else:
                        methods_render = True
                    if "all" in conditions["methods"]:
                        for method_string in conditions["methods"]["all"]:
                            split = method_string.split(".")
                            model = apps.get_model(app_label=split[0], model_name=split[1])
                            methods_render &= getattr(model, (split[2]))(self.request.user.profile)
            else:
                methods_render = True

            perms_render = False
            if "permissions" in conditions:
                if self.request.user.is_authenticated:
                    for key in conditions["permissions"].keys():
                        if key not in ["all", "any"]:
                            raise Exception(
                                "Wrongly configured menu file."
                                "For menu-item %s the conditions.permissions parameter can not have key %s.",
                                (info["name"], key))
                    if "any" in conditions["permissions"]:
                        for codename in conditions["permissions"]["any"]:
                            perms_render |= self.request.user.has_perm(codename)
                    else:
                        perms_render = True
                    if "all" in conditions["permissions"]:
                        for codename in conditions["permissions"]["all"]:
                            perms_render &= self.request.user.has_perm(codename)
            else:
                perms_render = True

            return auth_render and methods_render and perms_render

        else:
            return True

    def render_to_response(self, context, **response_kwargs):
        if 'menu' in context:
            for side in ['left', 'right']:
                if side in context['menu']:
                    for i, menu_item in enumerate(context['menu'][side]):
                        if 'template_content' in menu_item:
                            context['menu'][side][i]['label'] = Template(menu_item['template_content']).render(
                                Context({**context, 'user': self.request.user, 'request': self.request}))
                        else:
                            context['menu'][side][i]['label'] = menu_item['name']

        return super().render_to_response(context, **response_kwargs)


class RedirectToGETArgMixin:
    def get_success_url(self):
        if REDIRECT_FIELD_NAME in self.request.GET:
            self.success_url = self.request.GET[REDIRECT_FIELD_NAME]
        return super().get_success_url()


class BackUrlMixin:
    back_url = None
    force_get_redirect = False

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.force_get_redirect:
            if REDIRECT_FIELD_NAME in request.GET:
                self.back_url = request.GET[REDIRECT_FIELD_NAME]
            else:
                raise Exception("View must be called with a next url GET-parameter.")
        elif self.back_url is None:
            self.back_url = self.get_back_url(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.back_url:
            context.update({
                'back_url': self.back_url
            })

        return context

    def get_back_url(self, request, *args, **kwargs):
        back_url = None
        if REDIRECT_FIELD_NAME in request.GET:
            back_url = request.GET[REDIRECT_FIELD_NAME]

        return back_url


class SiteMixin:
    site_name = None
    site_texts = []
    site_images = []
    site_paragraph_lists = []

    def get_site_context(self):
        if self.site_name:
            site_context = {}
            site = models.Site.get_populated_site(self.site_name, self.site_texts, self.site_images, self.site_paragraph_lists, True)

            texts_list = site.texts.values_list('key', 'text')
            images_list = site.images.values_list('key', 'image')
            paragraphs_lists = [(para_list, para_list.paragraphs.all()) for para_list in site.paragraph_lists.all()]
            site_context.update({
                'texts': {key_text_pair[0]: key_text_pair[1] for key_text_pair in texts_list},
                'images': {key_image_pair[0]: key_image_pair[1] for key_image_pair in images_list},
                'lists': {
                    key_list_pair[0].key: [
                        {
                            'order_num': para.order_num,
                            'title': para.title,
                            'text': para.text,
                            'image': para.image
                        } for para in key_list_pair[1].order_by(
                            ('' if key_list_pair[0].ascending_order else '-') + 'order_num'
                        )
                    ] for key_list_pair in paragraphs_lists
                }
            })

            return site_context
        else:
            return {}

    def get_context_data(self, **kwargs):
        super_context = super().get_context_data(**kwargs)
        super_context.update({
            'site': self.get_site_context()
        })
        return super_context


class NollesystemetMixin(SiteMixin, BackUrlMixin, MenuMixin, RedirectToGETArgMixin,
                         PermissionRequiredMixin, UserPassesTestMixin):
    """
    Mixin that all views of the project should inherit from. It overrides the error-throwing and default behaviour of
    mixins that might not be used, but forces those that all views in the project should have.

    menu_items_static_file: Set to the filepath of file used for defining the menu of the given view.

    default_back_url: The default value of self.back_url and context value back_url if no previous page was given.
    accepted_back_urls: A list of urls which is accepted to use as self.back_url. Otherwise self.back_url = default_back_url

    login_required: If true user must be logged in. Defaults to False. Uses AccessMixin for error logic.
    """

    login_required = False
    permission_denied_url = None

    def dispatch(self, request, *args, **kwargs):
        if self.login_required and not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        if self.permission_required is not None:
            return super().has_permission()
        else:
            return True

    def test_func(self):
        return True

    def handle_no_permission(self):
        if self.permission_denied_url:
            if self.raise_exception or self.request.user.is_authenticated:
                return HttpResponseRedirect(
                    self.permission_denied_url + '?' +
                    urllib.parse.urlencode({'denier': self.request.path})
                )
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        else:
            return super().handle_no_permission()


class FadderietMixin(NollesystemetMixin):
    menu_items_static_file = 'fadderiet/resources/menu_info.json'
    login_url = reverse_lazy('fadderiet:logga-in:index')
    permission_denied_url = reverse_lazy('fadderiet:saknar-rattigheter')


class FohserietMixin(NollesystemetMixin):
    menu_items_static_file = 'fohseriet/resources/menu_info.json'
    login_url = reverse_lazy('fohseriet:logga-in:index')
    permission_denied_url = reverse_lazy('fohseriet:saknar-rattigheter')
