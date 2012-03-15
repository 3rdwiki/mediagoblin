# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import uuid

from webob import exc
from string import split
from cgi import FieldStorage
from datetime import datetime

from werkzeug.utils import secure_filename

from mediagoblin import messages
from mediagoblin import mg_globals

from mediagoblin.auth import lib as auth_lib
from mediagoblin.edit import forms
from mediagoblin.edit.lib import may_edit_media
from mediagoblin.decorators import require_active_login, get_user_media_entry
from mediagoblin.tools.response import render_to_response, redirect
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.text import (
    clean_html, convert_to_tag_list_of_dicts,
    media_tags_as_string)
from mediagoblin.tools.licenses import SUPPORTED_LICENSES
from mediagoblin.db.util import check_media_slug_used


@get_user_media_entry
@require_active_login
def edit_media(request, media):
    if not may_edit_media(request, media):
        return exc.HTTPForbidden()

    defaults = dict(
        title=media.title,
        slug=media.slug,
        description=media.description,
        tags=media_tags_as_string(media.tags),
        license=media.license)

    form = forms.EditForm(
        request.POST,
        **defaults)

    if request.method == 'POST' and form.validate():
        # Make sure there isn't already a MediaEntry with such a slug
        # and userid.
        slug_used = check_media_slug_used(request.db, media.uploader,
                request.POST['slug'], media.id)

        if slug_used:
            form.slug.errors.append(
                _(u'An entry with that slug already exists for this user.'))
        else:
            media.title = unicode(request.POST['title'])
            media.description = unicode(request.POST.get('description'))
            media.tags = convert_to_tag_list_of_dicts(
                                   request.POST.get('tags'))

            media.license = unicode(request.POST.get('license', '')) or None

            media.slug = unicode(request.POST['slug'])

            media.save()

            return exc.HTTPFound(
                location=media.url_for_self(request.urlgen))

    if request.user.is_admin \
            and media.uploader != request.user._id \
            and request.method != 'POST':
        messages.add_message(
            request, messages.WARNING,
            _("You are editing another user's media. Proceed with caution."))

    return render_to_response(
        request,
        'mediagoblin/edit/edit.html',
        {'media': media,
         'form': form})


@get_user_media_entry
@require_active_login
def edit_attachments(request, media):
    if mg_globals.app_config['allow_attachments']:
        form = forms.EditAttachmentsForm()

        # Add any attachements
        if ('attachment_file' in request.POST
            and isinstance(request.POST['attachment_file'], FieldStorage)
            and request.POST['attachment_file'].file):

            attachment_public_filepath \
                = mg_globals.public_store.get_unique_filepath(
                ['media_entries', unicode(media._id), 'attachment',
                 secure_filename(request.POST['attachment_file'].filename)])

            attachment_public_file = mg_globals.public_store.get_file(
                attachment_public_filepath, 'wb')

            try:
                attachment_public_file.write(
                    request.POST['attachment_file'].file.read())
            finally:
                request.POST['attachment_file'].file.close()

            media.attachment_files.append(dict(
                    name=request.POST['attachment_name'] \
                        or request.POST['attachment_file'].filename,
                    filepath=attachment_public_filepath,
                    created=datetime.utcnow(),
                    ))

            media.save()

            messages.add_message(
                request, messages.SUCCESS,
                "You added the attachment %s!" \
                    % (request.POST['attachment_name']
                       or request.POST['attachment_file'].filename))

            return exc.HTTPFound(
                location=media.url_for_self(request.urlgen))
        return render_to_response(
            request,
            'mediagoblin/edit/attachments.html',
            {'media': media,
             'form': form})
    else:
        return exc.HTTPForbidden()


@require_active_login
def edit_profile(request):
    # admins may edit any user profile given a username in the querystring
    edit_username = request.GET.get('username')
    if request.user.is_admin and request.user.username != edit_username:
        user = request.db.User.find_one({'username': edit_username})
        # No need to warn again if admin just submitted an edited profile
        if request.method != 'POST':
            messages.add_message(
                request, messages.WARNING,
                _("You are editing a user's profile. Proceed with caution."))
    else:
        user = request.user

    form = forms.EditProfileForm(request.POST,
        url=user.get('url'),
        bio=user.get('bio'))

    if request.method == 'POST' and form.validate():
        user.url = unicode(request.POST['url'])
        user.bio = unicode(request.POST['bio'])

        user.save()

        messages.add_message(request,
                             messages.SUCCESS,
                             _("Profile changes saved"))
        return redirect(request,
                       'mediagoblin.user_pages.user_home',
                        user=user.username)

    return render_to_response(
        request,
        'mediagoblin/edit/edit_profile.html',
        {'user': user,
         'form': form})


@require_active_login
def edit_account(request):
    edit_username = request.GET.get('username')
    user = request.user

    form = forms.EditAccountForm(request.POST,
        wants_comment_notification=user.wants_comment_notification)

    if request.method == 'POST':
        #save status of comment checkbox first, so user does not need to 
        #change their password as well.
        user.wants_comment_notification = request.POST.get(
            'wants_comment_notification', False) == u'y'

        user.save()

        #check remaining fields for validation
        if form.validate():
            password_matches = auth_lib.bcrypt_check_password(
                request.POST['old_password'],
                user.pw_hash)

            if (request.POST['old_password'] or \
                request.POST['new_password']) and not \
                    password_matches:
                form.old_password.errors.append(_('Wrong password'))

                return render_to_response(
                    request,
                    'mediagoblin/edit/edit_account.html',
                    {'user': user,
                     'form': form})

            if password_matches:
                user.pw_hash = auth_lib.bcrypt_gen_password_hash(
                    request.POST['new_password'])
            user.save()

        messages.add_message(request,
                             messages.SUCCESS,
                             _("Account settings saved"))
        return redirect(request,
                       'mediagoblin.user_pages.user_home',
                        user=user.username)

    return render_to_response(
        request,
        'mediagoblin/edit/edit_account.html',
        {'user': user,
         'form': form})
