import inspect

from django import forms
from django.conf import settings
from django.contrib.admin.sites import site
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.forms.formsets import formset_factory
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from DWStyles.models import *

class LayoutPropertyFilterForm(forms.Form):
    
    filter = forms.ChoiceField(widget=forms.CheckboxSelectMultiple,
        choices = StyleProperty.get_layout_property_choices(), required = False, 
        label="Layout Properties")

class ThemePropertyFilterForm(forms.Form):

    layoutfilter = forms.ChoiceField(widget=forms.CheckboxSelectMultiple,
        choices = StyleProperty.get_layout_property_choices(), required = False, 
        label="Layout Properties")
    layoutselect = forms.ChoiceField(widget=forms.CheckboxSelectMultiple,
        choices = DWLayout.get_layout_choices(), required = False,
        label="Layouts")
    themefilter = forms.ChoiceField(widget=forms.CheckboxSelectMultiple,
        choices = StyleProperty.get_theme_property_choices(), required = False,
        label="Theme Properties")
    colorfilter = forms.ChoiceField(widget=forms.CheckboxSelectMultiple,
        choices = ColorPropertyGroup.get_colorgroup_choices(), required = False,
        label="Color Groups")
    
class ColorForeignKeyRawIdWidget(ForeignKeyRawIdWidget):

    # https://github.com/jonasundderwolf/django-image-cropping/pull/3
    def __init__(self, *args, **kwargs):
        if 'admin_site' in inspect.getargspec(ForeignKeyRawIdWidget.__init__)[0]:  # Django 1.4
            kwargs['admin_site'] = site
        super(ColorForeignKeyRawIdWidget, self).__init__(*args, **kwargs)
    
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        related_url = '../../../%s/%s/' % (self.rel.to._meta.app_label, self.rel.to._meta.object_name.lower())
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
        else:
            url = ''
        if not attrs.has_key('class'):
            attrs['class'] = 'vForeignKeyRawIdAdminField' # The JavaScript looks for this hook.
        
        output = [self.color_for_value(value)]
        
        output.append(super(ForeignKeyRawIdWidget, self).render(name, value, attrs))
        # TODO: "id_" is hard-coded here. This should instead use the correct
        # API to determine the ID dynamically.
        output.append('<a href="%s%s" class="related-lookup" id="lookup_id_%s" onclick="return showRelatedObjectLookupPopup(this);"> ' % \
            (related_url, url, name))
        output.append('<img src="%sadmin/img/selector-search.gif" width="16" height="16" alt="%s" /></a>' % (settings.STATIC_URL, _('Lookup')))
        if value:
            output.append(self.label_for_value(value))
        return mark_safe(u''.join(output))

    def color_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(**{key: value})
            return '&nbsp;<span style="display: block; width: 2em; height: 2em; border: 1px solid black; background-color: #%s;"></span>' % obj.color_hex
        except ValueError:
            return ""
        except self.rel.to.DoesNotExist:
            return ''

class CopyLayerForm(forms.Form):
    """Shows the paste made, initial entry form."""
    paste = forms.CharField(widget=forms.Textarea, 
        help_text = "Paste in one theme layer.")

class HiddenCopyLayerForm(forms.Form):
    """Hides the paste made, to persist it from mode to mode."""
    paste = forms.CharField(widget=forms.HiddenInput)

class HiddenFormPrefixList(forms.Form):
    """Used to make a list of prefixes that a set of forms are using, to prevent from having to use
    formsets which make things harder if you also want extra information on the instance there."""
    prefixes = forms.CharField(widget=forms.HiddenInput)

class CopyColorForm(forms.ModelForm):

    class Meta:
        model = ColorProperty
        fields = ('color_hex', 'groups')
        widgets = {
            'groups': forms.CheckboxSelectMultiple(),
            'color_hex': forms.HiddenInput(),
        }

class CopyThemeColorForm(forms.ModelForm):

    class Meta:
        model = DWThemeColor
        fields = ('category', 'color', 'theme')
        widgets = {
            'category': forms.RadioSelect(),
            'color': forms.HiddenInput(),
            'theme': forms.HiddenInput(),
        }