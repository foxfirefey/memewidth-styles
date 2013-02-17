# Create your views here.

import re

from django.db.models import Count

from django.http import HttpResponse
from django.template import RequestContext
from django.http import HttpResponseRedirect

from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView

from DWStyles.models import *
from DWStyles.forms import *

def add_message(context, message):
    """Adds a message to the messages in the context.  Creates them if they don't exist."""
    
    if not "messages" in context:
        context["messages"] = []
    
    context["messages"].append(message)

def home(request):
    return render_to_response('home.html', {'title': "Home"},
        context_instance=RequestContext(request))

def stats(request):

    c = {'title': 'Stats'}
    c['theme_counts'] = DWTheme.objects.values("layout", "layout__name").annotate(themes=Count('layout')).order_by('-themes')
    c['total_themes'] = sum([count['themes'] for count in c['theme_counts']])
    c['total_layouts'] = len(c['theme_counts'])

    tally_properties = ["dw-free", "dw-nonfree", "dark-on-light", "light-on-dark", 
        "high-contrast", "low-contrast", 
        "one-column", "three-column-center", "three-column-left", "three-column-right", "two-column-left", "two-column-right"]

    property_counts = []

    for property in tally_properties:
        pc = dict() 
        p = StyleProperty.objects.get(codename=property)
        pc["property"] = p

        if p.theme_use:
            pc["theme_count"] = DWTheme.objects.filter(properties__pk = p.pk ).count()
        else:
            pc["theme_count"] = DWTheme.objects.filter(layout__properties__pk = p.pk ).count()

        if p.layout_use:
            pc["layout_count"] = DWLayout.objects.filter(properties__pk = p.pk ).count()
        else:
            pc["layout_count"] = 0
        property_counts.append(pc)

    c['property_counts'] = property_counts

    return render_to_response('stats.html', c,
        context_instance=RequestContext(request))

def layout_list(request, page=1):

    if not page:
        page = 1

    filters = []
    
    if "filter" in request.GET:
        filternames = request.GET.getlist("filter")
        for filtername in filternames:
            try:
                filters.append(StyleProperty.objects.get(codename = filtername))
            except:
                pass
            
    
    layout_list = DWLayout.objects.all()
    
    filterform = LayoutPropertyFilterForm(initial = {
        "filter": [filter.codename for filter in filters] })
    
    for filter in filters:
        layout_list = layout_list.filter(properties__pk = filter.pk)
    
    paginator = Paginator(layout_list, 25) # Show 25 layouts per page

    # If page request (9999) is out of range, deliver last page of results.
    try:
        layouts = paginator.page(page)
    except (EmptyPage, InvalidPage):
        layouts = paginator.page(paginator.num_pages)

    c = { "layouts": layouts, 
        "title": "Layouts",
        "filterform": filterform,
        "editlinks": request.user.is_staff,
        }
    
    return render_to_response('layout_list.html', c, 
        context_instance=RequestContext(request))

def layout_view(request, object_id):
    
    layout = DWLayout.objects.get(id = object_id)
    
    c = {
        "layout": layout,
        "editlinks": request.user.is_staff,
    }
    
    return render_to_response('view_layout.html', c, 
        context_instance=RequestContext(request))

class LayoutDetailView(DetailView):

    context_object_name = "layout"
    queryset = DWLayout.objects.all()

def theme_list(request, page=1):
    
    if not page:
        page = 1
    
    theme_list = DWTheme.objects.order_by('-date_added')
    
    layoutfilters = []
    layoutselects = []
    colorfilters = []
    themefilters = []
    filters = []

    if "layoutfilter" in request.GET:
        filternames = request.GET.getlist("layoutfilter")
        for filtername in filternames:
            try:
                layoutfilters.append(StyleProperty.objects.get(codename = filtername, 
                    layout_use = True))
            except:
                pass
        filters.append("Layout property filters: " + ", ".join(
            [p.label for p in layoutfilters]))
        
        
    if "layoutselect" in request.GET:
        layouts = request.GET.getlist("layoutselect")
        for layout in layouts:
            try:
                layoutselects.append(DWLayout.objects.get(sysid = layout))
            except:
                pass
        filters.append("Layouts included in search: " + ", ".join(
            [l.name for l in layoutselects]))
            
    if "colorfilter" in request.GET:
        filternames = request.GET.getlist("colorfilter")
        for filtername in filternames:
            try:
                colorfilters.append(ColorPropertyGroup.objects.get(codename = filtername))
            except:
                pass
        filters.append("Color group filters: " + ", ".join(
            [c.label for c in colorfilters]))
        
    if "themefilter" in request.GET:
        filternames = request.GET.getlist("themefilter")
        for filtername in filternames:
            try:
                themefilters.append(StyleProperty.objects.get(codename = filtername, 
                    theme_use = True))
            except:
                pass
        filters.append("Theme property filters: " + ", ".join(
            [p.label for p in themefilters]))
        

    filterform = ThemePropertyFilterForm(initial = {
        "layoutfilter": [filter.codename for filter in layoutfilters],
        "layoutselects": [layout.sysid for layout in layoutselects],
        "colorfilter": [filter.codename for filter in colorfilters],
        "themefilter": [filter.codename for filter in themefilters],
    })
    
    for filter in themefilters:
        theme_list = theme_list.filter(properties__pk = filter.pk)
    
    for filter in layoutfilters:
        theme_list = theme_list.filter(layout__properties__pk = filter.pk)
    
    for filter in colorfilters:
        theme_list = theme_list.filter(colors__groups__pk = filter.pk, dwthemecolor__category = "feature")
    
    if len(layoutselects):
        theme_list = theme_list.filter( layout__in = layoutselects )
    
    # want to make sure only distinct themes are chosen
    theme_list = theme_list.distinct()
    
    paginator = Paginator(theme_list, 25)
    
    # If page request (9999) is out of range, deliver last page of results.
    try:
        themes = paginator.page(page)
    except (EmptyPage, InvalidPage):
        themes = paginator.page(paginator.num_pages)
    
    c = { "themes": themes, 
        "title": "Themes",
        "filterform": filterform,
        "query": request.GET.copy(),
        "editlinks": request.user.is_staff,
        "filters": filters,
    }
    
    return render_to_response('theme_list.html', c, 
        context_instance=RequestContext(request))

def color_list(request, page=1):
    
    if not page:
        page = 1
    
    color_list = ColorProperty.get_colors_in_themes()
    paginator = Paginator(color_list, 200) # Show 50 colors per page

    # If page request (9999) is out of range, deliver last page of results.
    try:
        colors = paginator.page(page)
    except (EmptyPage, InvalidPage):
        colors = paginator.page(paginator.num_pages)

    c = { "colors": colors, "title": "Colors" }
    
    return render_to_response('color_list.html', c, 
        context_instance=RequestContext(request))
   
def color_view(request, hex_value):
     
    hex_value = hex_value.lower()

    try:
        color = ColorProperty.objects.get(color_hex = hex_value)
    except:
        color = ColorProperty(color_hex = hex_value)
        color.refresh_values()
         
    c = {
        "color": color,
        "title": "Color: #%s" % color.color_hex,
    }
     
    return render_to_response('view_color.html', c, 
        context_instance=RequestContext(request))

def colorgroup_list(request):
    
    c = { 
        "characteristics": ColorPropertyGroup.get_characteristics(),
        "colors": ColorPropertyGroup.get_colors(),
        "title": "Color Groups",
    }
    
    return render_to_response('colorgroup_list.html', c, 
        context_instance=RequestContext(request))

def colorgroup_colorlist(request, codename, page=1):
    
    colorgroup = ColorPropertyGroup.objects.get(codename = codename)
    
    if not page:
        page = 1
    
    color_list = ColorProperty.objects.filter(groups__id=colorgroup.pk)
    paginator = Paginator(color_list, 200) # Show 50 colors per page

    # If page request (9999) is out of range, deliver last page of results.
    try:
        colors = paginator.page(page)
    except (EmptyPage, InvalidPage):
        colors = paginator.page(paginator.num_pages)
    
    c = {
        "colorgroup": colorgroup,
        "colors": colors,
        "title": "Colors: %s" % colorgroup.label
    }
    
    return render_to_response('colorgroup_colorlist.html', c,
        context_instance=RequestContext(request))

class S2LayerParse(object):
    
    # picks out the variable name and color being set
    set_color_variable = re.compile(r'set\s+(?P<variable>[a-zA-Z_]+)\s*=\s*"#(?P<color>[A-Fa-f0-9]{3,6})"\s*;')
    # layerinfo redist_uniq = "bases/beechy";
    find_redist_unique = re.compile(r'layerinfo\s+"?redist_uniq"?\s*=\s*"(?P<layername>[a-z/A-Z0-9_]+)"\s*;')
    
    def __init__(self, text):
        
        self.load(text)
    
    def standardize_hex(self, hex):
        
        if len(hex) == 3:
            hex = "%s%s%s" % (hex[0]*2, hex[1]*2, hex[2]*2)
            
        return hex.lower()
    
    def load(self, text):
        self.layer = text
        
        self.color_variables = list()
        self.redist_unique = None
        
        # find all lines that set colors or have the redist_unique
        for line in text.split('\n'):
            
            if not self.redist_unique:
                m = self.find_redist_unique.search(line)
                if m:
                    self.redist_unique = m.groups()[0]
                    continue
            
            m = self.set_color_variable.search(line)
            if m:
                self.color_variables.append(m.groups())

        # gather all unique colors and their variables            
        self.colors = dict()
        for variable, color in self.color_variables:
            
            # work off of the full six form, lowercase version of the hex
            color = self.standardize_hex(color)
            
            if not color in self.colors:
                # create the list
                self.colors[color] = [variable]
        # top left = 0
            else:
                # add to the list
                self.colors[color].append(variable)
        
        self.existing_colors = {}
        
        for color in self.colors.keys():
            color = self.standardize_hex(color)
            
            try:
                self.existing_colors[color] = ColorProperty.objects.get(color_hex = color)
            except:
                color_model = ColorProperty(color_hex = color)
                color_model.save()
                self.existing_colors[color] = color_model
        
        # try to get the layer object; if it doesn't exist, will need to create it
        try:
            self.theme = DWTheme.objects.get(labelid=self.redist_unique)
        except:
            self.theme = None
            return
        
        self.existing_themecolors = {}
        
        for color in self.colors.keys():
        
            variables = ", ".join(self.colors[color])
            
            # don't change existing assignments
            try:
                themecolor_model = DWThemeColor.objects.get(color = self.existing_colors[color], theme = self.theme)
                themecolor_model.variables = variables
                themecolor_model.save()
            except:
                if "color_entry_background" in self.colors[color] or "color_page_background" in self.colors[color]:
                    category = "feature"
                else:
                    category = "accent"
                themecolor_model = DWThemeColor(color = self.existing_colors[color], theme = self.theme, variables = variables, category=category)
                themecolor_model.save()
        
@login_required
def color_layer_copy(request):
    """This view handles processing an S2 layer, most likely a theme, copied from the site.
    Gets all the colors, associated with their variables, and lets people create nonexistant ones
    and then attach them to the theme in question."""
    
    context = {"title": "Layer Copy Color Entry"}
    
    if request.method == "POST":
        
        success = process_themecolor_pasteform(request, context)
        
        # returns if success isn't True, because that means it's trying to serve a page
        if not (success and isinstance(success, bool)) and isinstance(success, HttpResponse):
            return success
        
        # if processing was successful we'll have a layer in the context
        layer = context["layer"]
        
        # if this layer doesn't exists redirect to theme creation page
        if not layer.theme:
            redirect("admin:DWStyles_dwtheme_add")
        else:
            url = reverse("admin:DWStyles_dwtheme_change", args=(layer.theme.pk,))
            # jump to the theme editing
            return HttpResponseRedirect(url + "#dwthemecolor_set-group")
    else:
        return serve_themecolor_pasteform(request, context)

def serve_themecolor_pasteform(request, context, layer = None):
    """Serves the layer copy paste form."""
    
    context["stage"] = "paste"
    
    if not "pasteform" in context:
        context["pasteform"] = CopyLayerForm()
    
    return render_to_response("colorlayercopy/color_layer_copy.html",
        context,
        RequestContext(request))

def process_themecolor_pasteform(request, context, layer = None):
    """Processes the layer copy paste form."""
    
    if "paste_stage" in request.POST:
        pasteform = CopyLayerForm(request.POST)
    else:
        pasteform = HiddenCopyLayerForm(request.POST)
    
    if not pasteform.is_valid():
        return render_to_response("colorlayercopy/color_layer_copy.html",
            {"title": "Copy Error", "pasteform": pasteform, "messages": ["Invalid copy paste."]},
            RequestContext(request))
            
    # we now have cleaned data to work with
    paste = pasteform.cleaned_data["paste"]
    
    if "paste_stage" in request.POST:
        # change over to hidden forms if we were in paste
        pasteform = HiddenCopyLayerForm(request.POST)
    
    # add paste form to the context
    context["pasteform"] = pasteform
    
    # add the layer to the context
    layer = S2LayerParse(paste)

    if not layer.theme:
        return render_to_response("colorlayercopy/color_layer_copy.html",
            {"title": "Copy Error", "pasteform": pasteform, "messages": ["Could not find theme or multiple themes with redist_unique of %s." % layer.redist_unique]},
            RequestContext(request))

    context["layer"] = layer
    
    return True

class ThemeDetailView(DetailView):

    context_object_name = "theme"
    queryset = DWTheme.objects.all()
