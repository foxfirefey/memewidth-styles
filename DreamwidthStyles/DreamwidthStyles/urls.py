from django.conf.urls.defaults import *
from django.template import RequestContext

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from DWStyles.models import *
from DWStyles.views import ThemeDetail

urlpatterns = patterns('',
    # Example:
    # (r'^dwstyles/', include('dwstyles.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    url(r'^admin/color_layer_copy$', "DWStyles.views.color_layer_copy", name="color_layer_copy"),

    url(r'^$', 'DWStyles.views.home', name="home"),
    url(r'^stats/?', 'DWStyles.views.stats', name="stats"),
    #(r'^$', 'django.views.generic.simple.direct_to_template', {'template': "base.html"}),

    # list all the layouts
    url(r'^layouts/(?P<page>[0-9]+)?$', "DWStyles.views.layout_list", name="layout_list"),
    url(r'^themes/(?P<page>[0-9]+)?$', "DWStyles.views.theme_list", name="theme_list"),
    url(r'^colors/(?P<page>[0-9]+)?$', "DWStyles.views.color_list", name="color_list"),
    url(r'^color/(?P<hex_value>[a-fA-F0-9]+)$', 'DWStyles.views.color_view', name='color_view'),
    
    url(r'^colorgroups/?$', "DWStyles.views.colorgroup_list", name="colorgroup_list"),
    url(r'^colorgroup/(?P<codename>[a-zA-Z0-9_s]+)/(?P<page>[0-9]+)?$', 
        "DWStyles.views.colorgroup_colorlist", name="colorgroup_colorlist"),
    
    #(r'^layout/(?P<object_id>[0-9]+)$', object_detail, 
    #    {'template_name': 'view_layout.html', 
    #    'template_object_name': 'layout',
    #    'queryset': DWLayout.objects.all(),
    #    }, "layout_view" ),
    url(r'^layout/(?P<object_id>[0-9]+)$', "DWStyles.views.layout_view", name="layout_view"),
    #(r'^theme/(?P<object_id>[0-9]+)$', object_detail, 
    #    {'template_name': 'view_theme.html', 
    #    'template_object_name': 'theme',
    #    'queryset': DWTheme.objects.all(),
    #    }, "theme_view" )
    # url(r'^theme/(?P<object_id>[0-9]+)$', 'DWStyles.views.theme_view', name="theme_view")
    url(r'^theme/(?P<pk>\d+)$', ThemeDetail.as_view(), name="theme_view"),
)
