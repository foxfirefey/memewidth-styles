# Create your views here.

import re

from django.db.models import Count

from django.http import HttpResponse
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, ListView, TemplateView

from DWStyles.models import *
from DWStyles.forms import *

class HomeView(TemplateView):

    template_name = "home.html"

class StatsView(TemplateView):

    template_name = "DWStyles/stats.html"

    tally_properties = ["dw-free", "dw-nonfree", "dark-on-light", "light-on-dark",
        "high-contrast", "low-contrast",
        "one-column", "three-column-center", "three-column-left", "three-column-right", "two-column-left", "two-column-right"]

    def get_context_data(self, **kwargs):

        context = super(StatsView, self).get_context_data(**kwargs)

        context['theme_counts'] = DWTheme.objects.values("layout", "layout__name").annotate(themes=Count('layout')).order_by('-themes')
        context['total_themes'] = sum([count['themes'] for count in context['theme_counts']])
        context['total_layouts'] = len(context['theme_counts'])

        property_counts = []

        for property in self.tally_properties:
            pc = dict()
            p = StyleProperty.objects.get(codename=property)
            pc["property"] = p

            if p.theme_use:
                pc["theme_count"] = DWTheme.objects.filter(properties__pk = p.pk).count()
            else:
                pc["theme_count"] = DWTheme.objects.filter(layout__properties__pk = p.pk).count()

            if p.layout_use:
                pc["layout_count"] = DWLayout.objects.filter(properties__pk = p.pk).count()
            else:
                pc["layout_count"] = 0

            property_counts.append(pc)

        context['property_counts'] = property_counts
        return context

class DWLayoutListView(ListView):

    model = DWLayout
    context_object_name = "layout_list"
    paginate_by = 25

    def get_queryset(self):
        layout_list = DWLayout.objects.all()

        self.filters = []

        if "filter" in self.request.GET:
            filternames = self.request.GET.getlist("filter")
            for filtername in filternames:
                try:
                    property_filter = StyleProperty.objects.get(codename = filtername)
                    self.filters.append(property_filter)
                    layout_list = layout_list.filter(properties__pk = property_filter.pk)
                except:
                    pass
        
        return layout_list

    def get_context_data(self, **kwargs):
        c = super(DWLayoutListView, self).get_context_data(**kwargs)

        filterform = LayoutPropertyFilterForm(initial = {
            "filter": [filter.codename for filter in self.filters] })

        c.update({
            "filterform": filterform,
            "applied_filters": self.filters,
        })

        return c

class DWLayoutDetailView(DetailView):

    context_object_name = "layout"
    queryset = DWLayout.objects.all()

    def get_context_data(self, **kwargs):
        context = super(DWLayoutDetailView, self).get_context_data(**kwargs)

        context["editlinks"] = self.request.user.is_staff

        return context

class DWThemeDetailView(DetailView):

    context_object_name = "theme"
    queryset = DWTheme.objects.all()

    def get_context_data(self, **kwargs):
        context = super(DWThemeDetailView, self).get_context_data(**kwargs)

        context["editlinks"] = self.request.user.is_staff

        return context

class DWThemeListView(ListView):

    model = DWTheme
    context_object_name = "theme_list"
    paginate_by = 25

    def get_queryset(self):
        theme_list = DWTheme.objects.order_by('-date_added')

        self.layoutfilters = []
        self.layoutselects = []
        self.colorfilters = []
        self.themefilters = []
        self.filters = []

        if "layoutfilter" in self.request.GET:
            filternames = self.request.GET.getlist("layoutfilter")
            for filtername in filternames:
                try:
                    self.layoutfilters.append(StyleProperty.objects.get(codename = filtername, 
                        layout_use = True))
                except:
                    pass
            self.filters.append("Layout property filters: " + ", ".join(
                [p.label for p in self.layoutfilters]))
            
        if "layoutselect" in self.request.GET:
            layouts = self.request.GET.getlist("layoutselect")
            for layout in layouts:
                try:
                    self.layoutselects.append(DWLayout.objects.get(sysid = layout))
                except:
                    pass
            self.filters.append("Layouts included in search: " + ", ".join(
                [l.name for l in self.layoutselects]))
                
        if "colorfilter" in self.request.GET:
            filternames = self.request.GET.getlist("colorfilter")
            for filtername in filternames:
                try:
                    self.colorfilters.append(ColorPropertyGroup.objects.get(codename = filtername))
                except:
                    pass
            self.filters.append("Color group filters: " + ", ".join(
                [c.label for c in self.colorfilters]))
            
        if "themefilter" in self.request.GET:
            filternames = self.request.GET.getlist("themefilter")
            for filtername in filternames:
                try:
                    self.themefilters.append(StyleProperty.objects.get(codename = filtername, 
                        theme_use = True))
                except:
                    pass
            self.filters.append("Theme property filters: " + ", ".join(
                [p.label for p in self.themefilters]))

        for filter in self.themefilters:
            theme_list = theme_list.filter(properties__pk = filter.pk)
        
        for filter in self.layoutfilters:
            theme_list = theme_list.filter(layout__properties__pk = filter.pk)
        
        for filter in self.colorfilters:
            theme_list = theme_list.filter(colors__groups__pk = filter.pk, dwthemecolor__category = "feature")
        
        if len(self.layoutselects):
            theme_list = theme_list.filter( layout__in = self.layoutselects )
        
        # want to make sure only distinct themes are chosen
        theme_list = theme_list.distinct()
        
        return theme_list

    def get_context_data(self, **kwargs):
        context = super(DWThemeListView, self).get_context_data(**kwargs)

        filterform = ThemePropertyFilterForm(initial = {
            "layoutfilter": [filter.codename for filter in self.layoutfilters],
            "layoutselects": [layout.sysid for layout in self.layoutselects],
            "colorfilter": [filter.codename for filter in self.colorfilters],
            "themefilter": [filter.codename for filter in self.themefilters],
        })

        context.update({
            "filterform": filterform,
            "applied_filters": self.filters,
            "editlinks": self.request.user.is_staff,
            "query": self.request.GET.copy(),
        })

        return context
        
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

class ColorPropertyDetailView(DetailView):

    slug_field = "color_hex"
    context_object_name = "color"
    queryset = ColorProperty.objects.all()

    def get_object(self, queryset = None):
        """Overriding the default function; if a color property does not exist, it means that
           it should be created and the values refreshed.  All hex colors exist, they just
           might not be in the database yet."""

        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        # Next, try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)

        if pk is not None:
            queryset = queryset.filter(pk=pk)

        # Next, try looking up by slug.
        elif slug is not None:
            #CHANGED -- we are expecting a hex color; normalize to all lowercase
            slug = slug.lower()
            slug_field = self.get_slug_field()
            queryset = queryset.filter(**{slug_field: slug})

        # If none of those are defined, it's an error.
        else:
            raise AttributeError("Generic detail view %s must be called with "
                                 "either an object pk or a slug."
                                 % self.__class__.__name__)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except ObjectDoesNotExist:
            # CHANGED -- if it doesn't exist, create it
            obj = ColorProperty(**{slug_field: slug})
            obj.save() # saving runs the refresh_values bit

        return obj

class ColorGroupListView(TemplateView):

    template_name = "DWStyles/colorgroup_list.html"

    def get_context_data(self, **kwargs):
        context = super(ColorGroupListView, self).get_context_data(**kwargs)

        context.update({ 
            "characteristics": ColorPropertyGroup.get_characteristics(),
            "colors": ColorPropertyGroup.get_colors(),
        })
        
        return context

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