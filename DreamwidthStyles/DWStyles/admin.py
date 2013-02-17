from django.contrib import admin
from DWStyles.models import *
from django.forms import ModelForm
from DWStyles.forms import ColorForeignKeyRawIdWidget

# Inline admin classes

class DWThemeColorForm(ModelForm):
    """This filters the example theme to only include themes belonging to this layout."""
    
    def __init__(self, *args, **kwargs):
        super(DWThemeColorForm, self).__init__(*args, **kwargs)

        rel = DWThemeColor._meta.get_field('color').rel
        self.fields["color"].widget = ColorForeignKeyRawIdWidget(rel)
        
class DWThemeColorInlineAdmin(admin.TabularInline):
    model = DWThemeColor
    extra = 1
    #raw_id_fields = ('color', )
    form = DWThemeColorForm
    
class DWThemeInlineAdmin(admin.TabularInline):
    model = DWTheme
    extra = 1
    fields = ('name', 'official', 'thumbnail', 'date_added', 'sysid', 'labelid')

# Admin forms

class DWLayoutForm(ModelForm):
    """This filters the example theme to only include themes belonging to this layout."""
    
    def __init__(self, *args, **kwargs):
        super(DWLayoutForm, self).__init__(*args, **kwargs)
        self.fields['example_theme'].queryset = DWTheme.objects.filter(
            layout=self.instance.pk)

# actions

def set_light_dark_contrast(modeladmin, request, queryset):

    for obj in queryset:
        obj.set_light_dark_contrast()
set_light_dark_contrast.short_description = "Set light/dark contrast"

# Main admin classes

class DWLayoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'official', 'date_added')
    list_filter = ('official',)
    search_fields = ('name',)
    date_hierarchy = 'date_added'
    inlines = ( DWThemeInlineAdmin, )
    form = DWLayoutForm
    filter_horizontal = ('properties',)
    
    # couldn't get this method for filtering example themes to work
    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    if db_field.name == "example_theme":
    #        kwargs["queryset"] = self.model.get_themes()
    #    return super(MyModelAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
admin.site.register(DWLayout, DWLayoutAdmin)
    
class DWThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'layout', 'official', 'date_added', 'color_boxes')
    list_filter = ('layout', 'official')
    search_fields = ('name',)
    date_hierarchy = 'date_added'
    exclude = ('colors', 'thumbnail_width', 'thumbnail_height')
    filter_horizontal = ('properties',)
    inlines = ( DWThemeColorInlineAdmin, )
    actions = [set_light_dark_contrast]
admin.site.register(DWTheme, DWThemeAdmin)

class StylePropertyAdmin(admin.ModelAdmin):
    list_display = ('label', 'group', 'codename', 'layout_use', 'theme_use')
    list_editable = ('layout_use', 'theme_use')
    list_filter = ('group',)
admin.site.register(StyleProperty, StylePropertyAdmin)
    
class StylePropertyGroupAdmin(admin.ModelAdmin):
    list_display = ('label', 'parent')
admin.site.register(StylePropertyGroup, StylePropertyGroupAdmin)

class DWThemeColorAdmin(admin.ModelAdmin):
    list_display = ('color', 'small_color_box', 'theme', 'category')
    list_filter = ('category',)
    raw_id_fields = ('theme', 'color')
    search_fields = ('theme__name', 'color__label')
admin.site.register(DWThemeColor, DWThemeColorAdmin)
    
class ColorPropertyGroupAdmin(admin.ModelAdmin):
    list_display = ('label', 'display_color', 'category')
    list_filter = ('category',)
    #fields = ('label', 'description', 'display_color', 'category', 'codename')
admin.site.register(ColorPropertyGroup, ColorPropertyGroupAdmin)

class ColorPropertyAdmin(admin.ModelAdmin):
    list_display = ('color_hex', 'label', 'small_color_box')
    list_filter = ('groups', 'is_round', 'in_themes')
    search_fields = ('color_hex', 'label')
    filter_horizontal = ('groups',)

    fieldsets = (
        (None, {
            'fields': ('label', 'color_hex', 'groups')
        }),
        #("Automatic information", {
        #    'fields': ('in_themes', 'R', 'G', 'B', 'H', 'S', 'V', 'rounded_hex', 'is_round', 'rR', 'rG', 'rB', 
        #        'rH', 'rS', 'rV', ),
        #    'classes': ('collapse'),
        #}),
    )
admin.site.register(ColorProperty, ColorPropertyAdmin)

class ColorDistanceAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'small_color_box','distance')
    fields = ('color_a', 'color_b')
    search_fields = ('color_a__color_hex', 'color_b__color_hex')
admin.site.register(ColorDistance, ColorDistanceAdmin)