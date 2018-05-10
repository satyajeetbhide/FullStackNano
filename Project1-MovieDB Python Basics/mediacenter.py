"""
Host a Movie Database
"""

import fresh_tomatoes
import media

def seedDB():
    """
    Initialize a database of Movies
    """
    toyStory = media.Movie("Toy Story", "Story of a boy's toys acting out in all sorts of ways",
                            "assets/posters/toystory.jpg",
                            "https://www.youtube.com/watch?v=Ny_hRfvsmU8")
    shawshank = media.Movie("Shawshank Redemption", "Story of a wrongfully convicted man's escape from prison",
                            "assets/posters/shawshank.jpg", 
                            "https://www.youtube.com/watch?v=6hB3S9bIaco")
    schindlerList = media.Movie("Schindler's List", "Story of Oscar Schindler and how he saved lives of thousands of jews  during WW2",
                            "assets/posters/schindlerList.jpg", 
                            "https://www.youtube.com/watch?v=JdRGC-w9syA")
    rango = media.Movie("Rango", "Story of a chamelion who starts a revolution",
                            "assets/posters/rango.jpg", 
                            "https://www.youtube.com/watch?v=k-OOfW6wWyQ")

    return [toyStory, shawshank, schindlerList, rango]

def hostServer():
    """
    Start a Movie Database server
    """
    movieDB = seedDB()
    fresh_tomatoes.open_movies_page(movieDB)

if __name__ == "__main__":
    hostServer()

    


