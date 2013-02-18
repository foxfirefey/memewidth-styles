import re

from django.core.exceptions import ObjectDoesNotExist

from .models import ColorProperty, DWThemeColor, DWTheme

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
        except ObjectDoesNotExist:
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