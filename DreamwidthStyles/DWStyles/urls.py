from django.conf.urls import patterns, url

from .views import ColorPropertyDetailView
from .views import DWLayoutDetailView
from .views import DWThemeDetailView

from .views import DWLayoutListView
from .views import DWThemeListView
from .views import ColorGroupListView

from .views import StatsView
from .views import HomeView


urlpatterns = patterns('DWStyles.views',
    url(r'^admin/color_layer_copy$', "color_layer_copy", name="color_layer_copy"),

    # list views
    url(r'^colors/(?P<page>[0-9]+)?$', "color_list", name="color_list"),

    # detail views
    url(r'^colorgroup/(?P<codename>[a-zA-Z0-9_s]+)/(?P<page>[0-9]+)?$', 
        "colorgroup_colorlist", name="colorgroup_colorlist"),
)

# Class based generic views
urlpatterns += patterns('',
    # template views
    url(r'^$', HomeView.as_view(), name="home"),
    url(r'^stats/?$', StatsView.as_view(), name="stats"),
    url(r'^colorgroups/?$', ColorGroupListView.as_view(), name="colorgroup_list"),

    # list views
    url(r'^layouts$', DWLayoutListView.as_view(), name="layout_list"),
    url(r'^themes$', DWThemeListView.as_view(), name="theme_list"),
    
    # detail views
    url(r'^color/(?P<slug>[a-fA-F0-9]+)$', ColorPropertyDetailView.as_view(), name='color_view'),
    url(r'^layout/(?P<pk>\d+)$', DWLayoutDetailView.as_view(), name="layout_view"),
    url(r'^theme/(?P<pk>\d+)$', DWThemeDetailView.as_view(), name="theme_view"),
)
