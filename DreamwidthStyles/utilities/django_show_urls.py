"""
django_show_urls.py

A simple script that prints out all of a Django project's URLs, with namespaces and URL
names associated.  Uses the ROOT_URLCONF laid out in settings.  

DJANGO_SETTINGS_MODULE must be properly set and in PYTHONPATH.

Based on: http://code.activestate.com/recipes/576974/
"""

from django.core.urlresolvers import RegexURLPattern, RegexURLResolver

def show_urls(urllist, depth=0):
    for entry in urllist:
        if isinstance(entry, RegexURLPattern):
            print "    " * depth, entry.regex.pattern, "\tname: %s" % entry.name
        elif isinstance(entry, RegexURLResolver):
            print "    " * depth, entry.regex.pattern, "\tnamespace: %s" % entry.namespace
        else:
            print "Could not recognize entry: ", str(entry)
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)

if __name__ == "__main__":

    from django.conf import settings
    from django.utils.importlib import import_module

    # use the URLs defined in settings
    root_urls = getattr(settings, 'ROOT_URLCONF', '')
    urls = import_module(root_urls)
    
    show_urls(urls.urlpatterns)
