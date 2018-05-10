"""
Define Movie class
"""

class Movie():
    """
    Base class for Movie
    Members: 
        title
        storyline
        poster URL
        trailer URL
    Methods:
        None
    """
    
    def __init__(self, title, storyline, poster, trailer):
        self.title = title
        self.storyline = storyline
        self.poster_image_url = poster
        self.trailer_youtube_url = trailer

