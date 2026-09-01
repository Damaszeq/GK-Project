from OpenGL.GL import *



class Framebuffer:

    def __init__(self, width: int, height: int):
        """
        Tworzy uniwersalny Framebuffer Object (FBO) z podpiętą teksturą koloru
        oraz buforem głębokości (Renderbuffer).
        """
        self.width = width
        self.height = height

        # Utworzenie pojemnika FBO
        self.fbo_id = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_id)

        # Tworzenie i podpinanie Tekstury Koloru 
        self.color_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.color_texture)
        
        # Alokacja pustej tekstury w pamięci VRAM (None jako ostatni parametr)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGB, self.width, self.height, 
            0, GL_RGB, GL_UNSIGNED_BYTE, None
        )
        
        # Ustawienie filtrów wygładzających
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        # Podpięcie tekstury jako główny punkt zapisu koloru
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.color_texture, 0
        )

        # Wygenerowanie i aktywacja Tekstury Głębokości
        self.depth_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        
        # Alokacja pamięci pod test głębokości
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        # Podpięcie Tekstury jako bufor głębokości
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_texture, 0)

        #Walidacja kompletości FBO 
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(f"Błąd tworzenia FBO! Status statusu: {status}")

        # Po skonfigurowaniu odpinamy FBO, wracając do domyślnego bufora
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    #Przekierowuje cały proces renderowania do tego wirtualnego bufora.
    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_id)
        glViewport(0, 0, self.width, self.height)

    #Przywraca renderowanie na fizyczny ekran monitora.
    def unbind(self, screen_width: int, screen_height: int):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, screen_width, screen_height)

    #Zwalnia zasoby w pamięci karty graficznej przy zamykaniu programu.
    def clean_up(self):
        glDeleteFramebuffers(1, [self.fbo_id])
        glDeleteTextures(1, [self.color_texture])
        glDeleteTextures(1, [self.depth_texture])