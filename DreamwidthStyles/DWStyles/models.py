from django.db import models
import datetime, re
from colormath.color_objects import HSVColor, RGBColor
from DWStyles.colorutil import *

class DWLayout(models.Model):

    name = models.CharField(max_length = 100, db_index = True)
    official = models.BooleanField(default = False, db_index = True)
    description = models.TextField(blank = True, null = True)
    properties = models.ManyToManyField('StyleProperty', blank = True, null = True,
            limit_choices_to = {"layout_use": True})
    date_added = models.DateField(db_index = True, blank = True, null = True)
    
    example_theme = models.ForeignKey('DWTheme', null = True, blank = True,
        help_text="A theme to use as an example of this layout.")
    
    sysid = models.PositiveIntegerField(db_index = True, null = True, blank = True)
    labelid = models.CharField(max_length=255, db_index = True, null = True, blank = True)

    codelink = models.URLField(blank = True, null = True)
    browserlink = models.URLField(blank = True, null = True)
    codename = models.CharField(max_length = 100, 
        help_text="A-Za-z0-9_- only.")
    
    def __unicode__(self):
        return u"%s" % self.name
    
    def save(self):
        """This save function exists make add in the date if it's not made."""
       
        # save!
        super(DWLayout, self).save()
    
    def number_themes(self):
        
        return DWTheme.objects.filter(layout = self).count()
    
    def get_themes(self):
        
        return DWTheme.objects.filter(layout = self)
    
    @models.permalink
    def get_absolute_url(self):
        return ('layout_view', [], {'object_id': self.pk})
    
    @staticmethod
    def get_layout_choices():
        
        layouts = DWLayout.objects.filter(official = True)
        
        return [(layout.sysid, layout.name) for layout in layouts]
    
    class Meta:
        verbose_name = "DW layout"
        verbose_name_plural = "DW layouts"
        ordering = ["name"]

def theme_thumbnail_folder(instance, filename):
    """Returns what folder a theme thumbnail should go into, using the layout's codename."""
    
    return "images/layout_previews/%s/%s" % (instance.layout.codename, filename)

class DWTheme(models.Model):
    
    layout = models.ForeignKey('DWLayout', db_index = True)
    name = models.CharField(max_length = 100, db_index = True)
    official = models.BooleanField(default = False, db_index = True)
    description = models.TextField(blank = True, null = True)
    date_added = models.DateField(db_index = True, blank = True, null = True)
    
    thumbnail = models.ImageField( upload_to = theme_thumbnail_folder, max_length=255, 
        blank = True, null = True, height_field = "thumbnail_height", 
        width_field = "thumbnail_width")
    thumbnail_width = models.PositiveSmallIntegerField(blank = True)
    thumbnail_height = models.PositiveSmallIntegerField(blank = True)
    
    sysid = models.PositiveIntegerField(db_index = True, null = True, blank = True)
    labelid = models.CharField(max_length=255, db_index = True, null = True, blank = True)

    codelink = models.URLField(blank = True, null = True)
    browserlink = models.URLField(blank = True, null = True)
    properties = models.ManyToManyField('StyleProperty', blank = True, null = True,
        limit_choices_to = {"theme_use": True})
    colors = models.ManyToManyField('ColorProperty', through="DWThemeColor", blank = True, null = True)

    def __unicode__(self):
        return u"Theme: %s (Layout: %s)" % ( self.name, self.layout.name )
        
    def save(self):
        """This save function exists make add in the date if it's not made."""
        
        #if not self.date_added:
        #    self.date_added = datetime.date.today()
        
        # save!
        super(DWTheme, self).save()
    
    def color_boxes(self):
        """Returns HTML for color boxes for this theme."""
        
        main_colors = self.get_feature_colors()
        accent_colors = self.get_accent_colors()
        main_width = 2
        accent_width = 1
        
        if len(main_colors) == 0 and len(accent_colors) == 0:
            return ""
        
        c = {"feature_colors": main_colors, "accent_colors": accent_colors, "feature_width": 2, 
            "accent_width": 1, "border_color": "black"}
        c["colorbar_width"] = len(main_colors) * 2 + len(accent_colors)
        
        from django.template import Context, Template, loader
        t = loader.get_template("colorbar.html")
        return t.render(Context(c))
    color_boxes.allow_tags = True
    color_boxes.short_description = "Colors"
    
    def get_accent_colors(self):
        return self.dwthemecolor_set.select_related().filter(category="accent").order_by('color__H', 'color__S', 'color__V')
        
    def get_feature_colors(self):
        return self.dwthemecolor_set.select_related().filter(category="feature").order_by('color__H', 'color__S', 'color__V')
    
    def get_colors(self):
        return self.dwthemecolor_set.select_related()
    
    def get_entry_colors(self):
        
        page_entry = dict()
        
        for color in self.get_colors():
            if not color.variables:
                continue
        
            if re.search("color_entry_background([^_a-z]|$)", color.variables):
                page_entry["color_entry_background"] = color
            if re.search("color_page_text([^_a-z]|$)", color.variables):
                page_entry["color_page_text"] = color
            if re.search("color_entry_text([^_a-z]|$)", color.variables):
                page_entry["color_entry_text"] = color
            if re.search("color_page_background([^_a-z]|$)", color.variables):
                page_entry["color_page_background"] = color
        
        fg_bg = {"foreground": None, "background": None }
        
        if "color_entry_text" in page_entry:
            fg_bg["foreground"] = page_entry["color_entry_text"]
        elif "color_page_text" in page_entry:
            fg_bg["foreground"] = page_entry["color_page_text"]
        
        if "color_entry_background" in page_entry:
            fg_bg["background"] = page_entry["color_entry_background"]
        elif "color_page_background" in page_entry:
            fg_bg["background"] = page_entry["color_page_background"]
        
        return fg_bg
    
    def set_light_dark_contrast(self):
        
        fb = self.get_entry_colors()
        
        if not fb["foreground"] or not fb["background"]:
            return
        
        dol = StyleProperty.objects.get(codename="dark-on-light")
        lod = StyleProperty.objects.get(codename="light-on-dark")
        
        if fb["foreground"].color.V < fb["background"].color.V:
            self.properties.add(dol)
            self.properties.remove(lod)
        else:            
            self.properties.add(lod)
            self.properties.remove(dol)
        
        # define high and low contrast
        cr = contrast_ratio(fb["foreground"].color, fb["background"].color)
        
        hc = StyleProperty.objects.get(codename="high-contrast")
        lc = StyleProperty.objects.get(codename="low-contrast")
        
        if cr >= 7:
            self.properties.add(hc)
            self.properties.remove(lc)
        elif cr <= 5:
            self.properties.add(lc)
            self.properties.remove(hc)
        else:
            self.properties.remove(lc)
            self.properties.remove(hc)
        
        
    @models.permalink
    def get_absolute_url(self):
        return ('theme_view', [], {'pk': self.pk})
    
    class Meta:
        verbose_name = "DW theme"
        verbose_name_plural = "DW themes"
        ordering = ["layout", "name"]

def theme_light_on_dark_contrast():
    """Automatically sets light on dark or dark on light properties."""
    
    for theme in DWTheme.objects.all():
        theme.set_light_dark_contrast()

class StyleProperty(models.Model):
    
    label = models.CharField(max_length=255, db_index = True)
    description = models.TextField(null = True, blank = True)
    
    order = models.PositiveSmallIntegerField( default = 1, db_index = True)
    group = models.ForeignKey('StylePropertyGroup', db_index = True, null = True, blank = True)
    codename = models.CharField(max_length = 100, db_index = True)
    
    layout_use = models.BooleanField(default = False, db_index = True)
    theme_use = models.BooleanField(default = False, db_index = True)
    
    def __unicode__(self):
        return u"%s" % self.label
    
    @staticmethod
    def get_layout_property_choices():
        
        properties = StyleProperty.objects.filter(layout_use = True)
        
        return [(property.codename, property.label) for property in properties]
    
    @staticmethod
    def get_theme_property_choices():
        
        properties = StyleProperty.objects.filter(theme_use = True)
        
        return [(property.codename, property.label) for property in properties]
    
    class Meta:
        verbose_name_plural = "style properties"
        ordering = ["label"]
        
class StylePropertyGroup(models.Model):
    
    label = models.CharField(max_length=255, db_index = True)
    description = models.TextField(null = True, blank = True)
    exclusive = models.BooleanField(default = False)

    # in case we end up wanting to tree or order
    order = models.PositiveSmallIntegerField( default = 1, db_index = True)
    parent = models.ForeignKey('StylePropertyGroup', db_index = True, null = True, blank = True)
    codename = models.CharField(max_length = 100, db_index = True)
    
    def __unicode__(self):
        return u"%s" % self.label            
    
    class Meta:
        ordering = ["label"]
    
class DWThemeColor(models.Model):
    
    THEME_COLOR_CATEGORIES = (
        ('feature', 'Feature'),
        ('accent', 'Accent'),
    )
    
    theme = models.ForeignKey('DWTheme', db_index = True)
    color = models.ForeignKey('ColorProperty', db_index = True)
    category = models.CharField(max_length = 30, choices = THEME_COLOR_CATEGORIES,
        db_index = True)
    variables = models.TextField(blank = True, null = True)
    
    def __unicode__(self):
        if self.color.label:
            return u"%s: %s" % (self.theme.name, self.color.label)            
        else:
            return u"%s: #%s" % (self.theme.name, self.color.color_hex)
            
    def small_color_box(self):
        return """<div style="background-color: #%s; border: 1px solid black; width: 20px; height: 20px;"></div>""" % (self.color.color_hex,);
    small_color_box.allow_tags = True
    small_color_box.short_description = "Color"

    class Meta:
        verbose_name = "DW theme color"
        verbose_name_plural = "DW theme colors"
        ordering = ["theme", "-category", "color"]
        # each theme can only have a color once for each category
        unique_together = (("theme", "color", "category"),)

class ColorPropertyGroup(models.Model):
    
    COLOR_GROUP_CATEGORIES = (
        ('color', 'Color'),
        ('characteristic', 'Characteristic'),
    )
    
    label = models.CharField(max_length = 255, db_index = True)
    description = models.TextField(blank = True, null = True)
    display_color = models.CharField(max_length=6, 
        help_text="Hex code for color to display for this group.")
    category = models.CharField(max_length = 30, choices = COLOR_GROUP_CATEGORIES,
        db_index = True)
    codename = models.CharField(max_length = 100, db_index = True)
    
    def __unicode__(self):
        return u"%s" % self.label

    @staticmethod
    def get_characteristics():
        
        return ColorPropertyGroup.objects.filter(category = "characteristic")
    
    @staticmethod
    def get_colors():
        
        return ColorPropertyGroup.objects.filter(category = "color")
    
    @staticmethod
    def get_colorgroup_choices():
        
        groups = ColorPropertyGroup.objects.order_by('category', 'label')
        
        return [(group.codename, group.label) for group in groups]

 #   def get_themes():
  
 
    @models.permalink
    def get_absolute_url(self):
        return ('colorgroup_colorlist', [], {'codename': self.codename})
    
    
    class Meta:
        ordering = ["label"]
        
class ColorProperty(models.Model):
    
    label = models.CharField(max_length=100, null = True, blank = True, 
        help_text="This can help accessibility.")
    color_hex = models.CharField(max_length=8, db_index = True, unique = True)
    groups = models.ManyToManyField('ColorPropertyGroup')
    
    in_themes = models.BooleanField(default = False, db_index = True,
        help_text="Whether or not this counts as a color in themes.")
    
    # The rest of these fields can all technically be computed by the color hex
    # but need to be here for efficiency in calculations
    
    # 0 - 255
    R = models.PositiveSmallIntegerField(db_index = True, default = 0)
    G = models.PositiveSmallIntegerField(db_index = True, default = 0)
    B = models.PositiveSmallIntegerField(db_index = True, default = 0)
    
    # 0 - 100
    H = models.PositiveSmallIntegerField(db_index = True, default = 0)
    S = models.PositiveSmallIntegerField(db_index = True, default = 0)
    V = models.PositiveSmallIntegerField(db_index = True, default = 0)
    
    # rounding is necessary to help define colorspace in a way that won't take
    # up too many comparisons!
    rounded_hex = models.CharField(max_length=6, db_index = True,)
    # is true if this color IS a rounded color
    is_round = models.BooleanField(default = False, db_index = True,
        help_text="Lets us do searches for all rounded colors." )

    # rounded values from the rounded hex
    # 0 - 255
    rR = models.PositiveSmallIntegerField(db_index = True, default = 0)
    rG = models.PositiveSmallIntegerField(db_index = True, default = 0)
    rB = models.PositiveSmallIntegerField(db_index = True, default = 0)
    
    # 0 - 100
    rH = models.PositiveSmallIntegerField(db_index = True, default = 0)
    rS = models.PositiveSmallIntegerField(db_index = True, default = 0)
    rV = models.PositiveSmallIntegerField(db_index = True, default = 0)
    
    def __unicode__(self):
        if self.label:
            return u"#%s (%s)" % (self.color_hex, self.label)
        else:
            return u"#%s" % self.color_hex

    def small_color_box(self):
        return """<div class="smallcolorbox" style="background-color: #%s; border: 1px solid black; width: 20px; height: 20px;"></div>""" % self.color_hex;
    small_color_box.allow_tags = True
    small_color_box.short_description = "Color"
        
    def distance(self, color):
        """Calculates the distance to another color using the colormath library's default."""
        
        return color_distance(self, color)
    
    def rounded_distance(self, color):
        """Calculates the distance to another color, but using the rounded values."""
        
        return color_distance(self, color)
    
    @models.permalink
    def get_absolute_url(self):
        return ('color_view', (), {'hex_value': self.hex_color})
        
    def save(self):
        """This save function exists to update all of the many different automatically
        calculated values of a given color."""
        
        self.refresh_values()
        
        if self.themes_in().count() > 0:
            self.in_themes = True
        else:
            self.in_themes = False
        
        # save!
        super(ColorProperty, self).save()
    
    def refresh_values(self):
        
        if not self.color_hex.islower():
            self.color_hex = self.color_hex.lower()
        
        # get rgb and hsv values
        rgbcolor = RGBColor()
        rgbcolor.set_from_rgb_hex(self.color_hex)
        hsvcolor = rgbcolor.convert_to('hsv')
        
        self.R = rgbcolor.rgb_r
        self.G = rgbcolor.rgb_g
        self.B = rgbcolor.rgb_b
        
        self.H = round(hsvcolor.hsv_h)
        # need to multiply by 100 to get the percent
        self.S = round(hsvcolor.hsv_s * 100.0)
        self.V = round(hsvcolor.hsv_v * 100.0)
        
        # make rounded values
        self.rR = round_rgb_colorvalue(self.R)
        self.rG = round_rgb_colorvalue(self.G)
        self.rB = round_rgb_colorvalue(self.B)

        round_rgb = RGBColor(rgb_r = self.rR, rgb_g = self.rG, rgb_b = self.rB)
        round_hsv = round_rgb.convert_to('hsv')
        
        self.rounded_hex = round_rgb.get_rgb_hex()[1:7]
        
        self.rH = round_hsv.hsv_h
        self.rS = round_hsv.hsv_s
        self.rV = round_hsv.hsv_v
        
        # check to see if this is a round color
        if self.R == self.rR and self.G == self.rG and self.B == self.rB:
            self.is_round = True
        else:
            self.is_round = False
            
    def contrast_text(self):
        """Returns hex code of a color that contrasts with this one, for 
        overlaying text. Includes the #."""
                
        # get rgb and hsv values
        rgbcolor = RGBColor()
        rgbcolor.set_from_rgb_hex(self.color_hex)
        
        hsvcolor = rgbcolor.convert_to('hsv')
        
        new_v = hsvcolor.hsv_v;
        
        if new_v <= .55:
            new_v = 1.0;
        elif new_v > .55:
            new_v = 0.0;
        
        new_h = hsvcolor.hsv_h
        
        new_s = 0
        
        contrast = HSVColor(hsv_h = new_h, hsv_s = new_s, hsv_v = new_v)
        contrast_rgb = contrast.convert_to('rgb')
        
        return contrast_rgb.get_rgb_hex()

    @staticmethod
    def get_colors_in_themes():
        """Gets all the "rounded" colors with nearby colors in themes."""
        
        return ColorProperty.objects.filter(in_themes = True, is_round = True).order_by(
            'H', 'S', 'V')
    
    def get_rounded_color(self):
        """Returns a pointer to the rounded color."""
        
        try:
            return ColorProperty.objects.get(color_hex = self.rounded_hex)
        except:
            return None
            
    def similar_colors(self):
        """This gets all of the similar colors in themes."""
        return ColorProperty.objects.filter(rounded_hex = self.rounded_hex, 
            in_themes = True).exclude(id = self.id).distinct()
    
    def near_colors(self): 
        """This gets all of the colors that are *near* to this one."""
        
        # work off of the rounded color
        if self.is_round:
            rounded = self
        else:
            rounded = self.get_rounded_color()
        
        if not rounded:
            return []
        
        near = ColorDistance.objects.filter(
            # color_a or color_b should be equal to rounded
            models.Q(color_a = rounded) | models.Q(color_b = rounded)
            # order by the distance, only include things with a distance less than 10
            ).order_by('distance').filter(distance__lt = 10).filter(
            # filter by colors in themes only
            color_a__in_themes = True, color_b__in_themes = True)
        
        near_colors = []
        
        # get the colors that are near the rounded color
        for color in near:
            if color.color_a == rounded:
                near_colors.append(color.color_b)
            else:
                near_colors.append(color.color_a)
        
        return near_colors
        
    def themes_in(self, category = None):
        """This gets all of the themes in the rounded version of the color, 
        with optional category."""
        
        if category:
            return DWThemeColor.objects.filter(color__rounded_hex = self.rounded_hex, category = category)
        else:
            return DWThemeColor.objects.filter(color__rounded_hex = self.rounded_hex )
    
    def feature_in_themes(self):
        return self.themes_in(category="feature").select_related()
    
    def accent_in_themes(self):
        return self.themes_in(category="accent").select_related()
    
    def css_hex(self):
        """Returns a string with # to the front of the color hex value."""
        return "#%s" % self.color_hex
    
    @models.permalink
    def get_absolute_url(self):
        return ('view_color', (), {'hex_value': self.color_hex})
    
    class Meta:
        ordering = ["color_hex"]
        verbose_name_plural = "color properties"

def categorize_color_properties():
    """Automatically categorize color properties."""
    
    ccat = ColorCategorizer()
    colors = ColorProperty.objects.filter(in_themes = True)
    categories = ColorPropertyGroup.objects.all()
    categorizer = {}
    
    for category in categories:
        
        # try to get function from the color categorizer by codename
        try:
            categorizer[category.codename] = getattr(ccat, "is_%s" % category.codename)
        # no automatic categorizer for this function
        except AttributeError:
            continue
    
    for color in colors:
        color_groups = color.groups.all()
        change = False
        for category in categories:
            if category.codename in categorizer:
                in_category = categorizer[category.codename](color)
                if in_category and category not in color_groups:
                    # add if we get a true!
                    print "Adding %s to %s" % (category, color)
                    color.groups.add(category)
                    change = True
                elif not in_category and category in color_groups:
                    # remove if it doesn't match the criteria
                    print "REMOVING %s from %s" % (category, color)
                    color.groups.remove(category)
                    change = True
        
        if change:
            color.save()

class ColorDistance(models.Model):
    """Represents the distance between two colors. Start with (5*5)^2."""
    
    # color a will always be "alphabetically" before color_b
    color_a = models.ForeignKey('ColorProperty', db_index = True, related_name="color_a")
    color_b = models.ForeignKey('ColorProperty', db_index = True, related_name="color_b")
    distance = models.FloatField(db_index = True)
    
    def __unicode__(self):
        return u"%s vs %s" % (self.color_a.color_hex, self.color_b.color_hex)
    
    def small_color_box(self):
        return """<div style="background-color: #%s; border: 1px solid black; border-bottom: none; width: 20px; height: 10px;"></div><div style="background-color: #%s; border: 1px solid black; border-top: none; width: 20px; height: 10px;"></div>""" % (self.color_a.color_hex, self.color_b.color_hex);
    small_color_box.allow_tags = True
    small_color_box.short_description = "Color"
    
    def save(self):
        """This save function exists to update all of the many different automatically
        calculated values of a given color."""
        
        self.distance = color_distance(self.color_a, self.color_b)
        
        # save!
        super(ColorDistance, self).save()
    
    class Meta:
        ordering = ["distance"]
        unique_together = (("color_a", "color_b"),)

def generate_rounded_colors():
    """Hardcoded to generate rounded colors, with a distance of 32RGB in between."""
    
    values = ["00", "20", "40", "60", "80", "a0", "c0", "e0", "ff"]
    
    for r_val in values:
        for g_val in values:
            for b_val in values:
                yield "%s%s%s" % (r_val, g_val, b_val)

def create_rounded_colors():
    
    for color in generate_rounded_colors():
        cp, created = ColorProperty.objects.get_or_create(color_hex = color)
        cp.save()

def create_rounded_distances():
    """Generate the distances for all round colors we have."""
    round_colors = ColorProperty.objects.filter(is_round = True)
    
    for color_a in round_colors:
        for color_b in round_colors:
            # don't calculate the distance for equal colors
            if color_a.pk == color_b.pk:
                continue
            # first color is always lexographically before the second
            if color_a.color_hex > color_b.color_hex:
                continue
            new_distance, created = ColorDistance.objects.get_or_create(color_a = color_a, color_b = color_b )
            #ColorDistance(color_a = color_a, color_b = color_b, distance = distance)
            if created:
                distance = color_distance(color_a, color_b)
                new_distance.distance = distance
                new_distance.save()

def color_distance(color_a, color_b):
    
    from colormath.color_objects import RGBColor
    
    colora = RGBColor(rgb_r = color_a.rR, rgb_g = color_a.rG, rgb_b = color_a.rB)
    colorb = RGBColor(rgb_r = color_b.rR, rgb_g = color_b.rG, rgb_b = color_b.rB)
    
    return colora.delta_e(colorb, mode='cmc', pl=1, pc=1)
    
