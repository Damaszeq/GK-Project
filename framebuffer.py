from OpenGL.GL import *



class Framebuffer:

    def __init__(self, width: int, height: int):
        """
        Tworzy uniwersalny Framebuffer Object (FBO) z podpiętą teksturą koloru
        oraz buforem głębokości (Renderbuffer).
        """
        self.width = width
        self.height = height

        # --- KROK 2.1.1: Utworzenie pojemnika FBO ---
        self.fbo_id = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_id)

        # --- KROK 2.1.2: Tworzenie i podpinanie Tekstury Koloru ---
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

        # Wygenerowanie i aktywacja Renderbuffera
        self.depth_rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.depth_rbo)

        # Alokacja pamięci pod test głębokości
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height
        )

        # Podpięcie Renderbuffera do FBO jako bufor głębokości
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depth_rbo
        )

        #Walidacja kompletości FBO ---
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(f"Błąd tworzenia FBO! Status statusu: {status}")

        # Po skonfigurowaniu odpinamy FBO, wracając do domyślnego bufora
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind(self):
        """
        Przekierowuje cały proces renderowania do tego wirtualnego bufora.
        """
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_id)
        glViewport(0, 0, self.width, self.height)

    def unbind(self, screen_width: int, screen_height: int):
        """
        Przywraca renderowanie na fizyczny ekran monitora.
        """
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, screen_width, screen_height)

    def clean_up(self):
        """
        Zwalnia zasoby w pamięci karty graficznej przy zamykaniu programu.
        """
        glDeleteFramebuffers(1, [self.fbo_id])
        glDeleteTextures(1, [self.color_texture])
        glDeleteRenderbuffers(1, [self.depth_rbo])