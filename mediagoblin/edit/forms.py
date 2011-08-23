# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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


import wtforms

from mediagoblin.util import tag_length_validator, TOO_LONG_TAG_WARNING
from mediagoblin.util import fake_ugettext_passthrough as _


class EditForm(wtforms.Form):
    title = wtforms.TextField(
        _('Title'),
        [wtforms.validators.Length(min=0, max=500)])
    slug = wtforms.TextField(
        _('Slug'),
        [wtforms.validators.Required(message=_("The slug can't be empty"))])
    description = wtforms.TextAreaField('Description of this work')
    tags = wtforms.TextField(
        _('Tags'),
        [tag_length_validator])

class EditProfileForm(wtforms.Form):
    bio = wtforms.TextAreaField(
        _('Bio'),
        [wtforms.validators.Length(min=0, max=500)])
    url = wtforms.TextField(
        _('Website'),
        [wtforms.validators.Optional(),
         wtforms.validators.URL(message='Improperly formed URL')])

class EditAttachmentsForm(wtforms.Form):
    attachment_name = wtforms.TextField(
        'Title')
    attachment_file = wtforms.FileField(
        'File')
