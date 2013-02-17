# Colors

round_color_segment = 32
max_color_value = 256

def contrast_ratio(color_a, color_b):
    
    rla = relative_luminance(color_a)
    rlb = relative_luminance(color_b)

    if rla < rlb:
        return (rlb + 0.05) / (rla + 0.05)
    else:
        return (rla + 0.05) / (rlb + 0.05)

def channel_value(v):
    
    if v <= 0.03928:
        return v / 12.92
    else:
        return ((v + 0.055) / 1.055) ** 2.4

def relative_luminance(c):
    
    (r, g, b) = [channel_value(v) for v in (c.R, c.G, c.B)]
    
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def round_rgb_colorvalue(cv):
    
    # returns the RGB color value rounded to the nearest segment
    value = int(cv / round_color_segment + round(float(cv % round_color_segment) 
        / float(round_color_segment))) * round_color_segment
    
    # don't return 256, return 255
    if value == max_color_value:
        return value - 1
    else:
        return value

class ColorCategorizer(object):
    
    def is_red(self, c):
        """Returns a boolean on whether or not to consider this color red."""
        
        if c.V <= 10:
            return False
        
        # red is in these regions
        if not (( c.H >= 0 and c.H <= 14) or (c.H >= 342 and c.H <= 359)):
            return False
        
        # if the saturation is low, probably pink
        if not c.S >= 50:
            return False
        
        return True
        
    def is_green(self, c):
        
        if c.V <= 10:
            return False
        
        if not (c.H >= 69 and c.H <= 170):
            return False
        
        return True
    
    def is_blue(self, c):
        
        if c.V <= 10:
            return False
        
        if not (c.H >=167 and c.H <= 250):
            return False
        
        return True
        
    def is_yellow(self, c):
        
        if c.V <= 10:
            return False
            
        if not (c.H <=72 and c.H >= 50):
            return False
        
        return True
        
    def is_orange(self, c):
        
        if not (c.H <= 50 and c.H >= 25):
            return False
        
        return True
    
    def is_purple(self, c):
        
        if c.V <= 10:
            return False
        
        if not (c.H >= 270 and c.H <= 290):
            return False
        
        return True
    
    def is_pink(self, c):
        
        if not (c.H > 290 and c.H <= 340):
            return False
        
        return True
        
    def is_brown(self, c):
        
        return False
    
    def is_gray(self, c):
        
        if c.V <= 10 or c.V >= 95:
            return False
        
        if c.S <= 5:
            return True
        
        return False
    
    def is_black(self, c):
        
        if c.V <= 10:
            return True
        
        return False
    
    def is_white(self, c):
        
        if c.S < 5 and c.V > 95:
            return True
        
        return False
    
    # Characteristics
    
    def is_dark(self, c):
        
        if c.V < 30:
            return True
        
        return False
    
    def is_light(self, c):
        
        if c.V > 95 and c.S < 30:
            return True
        
        return False
    
    def is_bright(self, c):
        
        if c.V > 95 and c.S > 90:
            return True
        
        return False
    
    def is_muted(self, c):
        
        if c.V > 50 and c.V < 85 and c.S > 5 and c.S < 85:
            return True
        
        return False