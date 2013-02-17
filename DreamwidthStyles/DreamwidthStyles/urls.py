from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from DWStyles.views import DWLayoutListView

urlpatterns = patterns('',
    url(r'', include('DWStyles.urls', namespace="dwstyles", app_name="DWStyles")),
    url(r'^admin/', include(admin.site.urls)),
)
