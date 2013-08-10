from PIL import Image

import ckit

#--------------------------------------------------------------------

class Wallpaper:

    def __init__( self, window ):
        self.window = window
        self.plane = ckit.Plane( window, (0,0), (1,1), 4 )
        self.filename = ""
        self.pil_image = None
        self.crop_rect = (0,0,1,1)

    def destroy(self):
        self.plane.destroy()

    def load( self, filename, strength ):
    
        self.filename = filename

        self.pil_image = Image.open(self.filename)
        self.pil_image = self.pil_image.convert( "RGBA" )
        
        bg = ckit.getColor("bg")
        bgcolor_pil_image = Image.new( "RGBA", self.pil_image.size, (bg[0],bg[1],bg[2],255) ) 

        self.pil_image = Image.blend( self.pil_image, bgcolor_pil_image, (100-strength)/100.0 )

    def copy( self, other_window ):
    
        self.filename = other_window.wallpaper.filename
        
        other_client_rect = other_window.getClientRect()
        other_left, other_top = other_window.clientToScreen( other_client_rect[0], other_client_rect[1] )
        other_right, other_bottom = other_window.clientToScreen( other_client_rect[2], other_client_rect[3] )

        client_rect = self.window.getClientRect()
        left, top = self.window.clientToScreen( client_rect[0], client_rect[1] )
        right, bottom = self.window.clientToScreen( client_rect[2], client_rect[3] )
        
        crop_ratio = [ 
            float( left - other_left ) / ( other_right - other_left ),
            float( top - other_top ) / ( other_bottom - other_top ),
            float( right - other_left ) / ( other_right - other_left ),
            float( bottom - other_top ) / ( other_bottom - other_top )
        ]
        
        crop_rect = [
            int( other_window.wallpaper.crop_rect[0] + (other_window.wallpaper.crop_rect[2]-other_window.wallpaper.crop_rect[0]) * crop_ratio[0] ),
            int( other_window.wallpaper.crop_rect[1] + (other_window.wallpaper.crop_rect[3]-other_window.wallpaper.crop_rect[1]) * crop_ratio[1] ),
            int( other_window.wallpaper.crop_rect[0] + (other_window.wallpaper.crop_rect[2]-other_window.wallpaper.crop_rect[0]) * crop_ratio[2] ),
            int( other_window.wallpaper.crop_rect[1] + (other_window.wallpaper.crop_rect[3]-other_window.wallpaper.crop_rect[1]) * crop_ratio[3] )
        ]
        
        crop_rect[0] = max( crop_rect[0], 0 )
        crop_rect[1] = max( crop_rect[1], 0 )
        crop_rect[2] = min( crop_rect[2], other_window.wallpaper.pil_image.size[0] )
        crop_rect[3] = min( crop_rect[3], other_window.wallpaper.pil_image.size[1] )
        
        self.pil_image = other_window.wallpaper.pil_image.crop(crop_rect)

    def adjust(self):

        client_rect = self.window.getClientRect()
        client_size = ( max(client_rect[2],1), max(client_rect[3],1) )
        
        try:
            wallpaper_ratio = float(self.pil_image.size[0]) / self.pil_image.size[1]
            client_rect_ratio = float(client_size[0]) / client_size[1]

            if wallpaper_ratio > client_rect_ratio:
                crop_width = int(self.pil_image.size[1] * client_rect_ratio)
                self.crop_rect = ( (self.pil_image.size[0]-crop_width)//2, 0, (self.pil_image.size[0]-crop_width)//2+crop_width, self.pil_image.size[1] )
            else:
                crop_height = int(self.pil_image.size[0] / client_rect_ratio)
                self.crop_rect = ( 0, (self.pil_image.size[1]-crop_height)//2, self.pil_image.size[0], (self.pil_image.size[1]-crop_height)//2+crop_height )
        except ZeroDivisionError:
            self.crop_rect = (0,0,self.pil_image.size[0],self.pil_image.size[1])

        cropped_pil_image = self.pil_image.crop(self.crop_rect)
        cropped_scaled_pil_image = cropped_pil_image.resize( client_size )

        img = ckit.Image.fromString( cropped_scaled_pil_image.size, cropped_scaled_pil_image.tostring() )
        self.plane.setSize(client_size)
        self.plane.setImage(img)
