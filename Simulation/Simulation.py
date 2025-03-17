# Import standard modules.
import sys
 
# Import non-standard modules.
import pygame
from pygame.locals import *

from Car import Car

width, height = 1500, 1000
carSize = 30;

roadCenter = [width/1.5, height/2]; # The center point of the road
roadWidth = 50; # The width of the road

roadBoundaries = [[roadCenter[0], roadCenter[1]-roadWidth, 0, roadCenter[1]-roadWidth], # Upper lane boundarie
                  [roadCenter[0], roadCenter[1], 0, roadCenter[1]],                     # Midle lane boundarie
                  [roadCenter[0], roadCenter[1]+roadWidth, 0, roadCenter[1]+roadWidth], # Lower lane boundarie
                  [roadCenter[0], roadCenter[1]-roadWidth, roadCenter[0]+roadWidth*2, roadCenter[1]-roadWidth/2], # Upper merge point
                  [roadCenter[0], roadCenter[1]+roadWidth, roadCenter[0]+roadWidth*2, roadCenter[1]+roadWidth/2], # Lower merge point
                  [roadCenter[0]+roadWidth*2, roadCenter[1]-roadWidth/2, width, roadCenter[1]-roadWidth/2], # New lane upper
                  [roadCenter[0]+roadWidth*2, roadCenter[1]+roadWidth/2, width, roadCenter[1]+roadWidth/2]] # New lane lower


upperLaneWaypoints = [[roadCenter[0], roadCenter[1]-roadWidth/2], [roadCenter[0]+roadWidth*2, roadCenter[1]], [width, roadCenter[1]]]
bottomLaneWaypoints = [[roadCenter[0], roadCenter[1]+roadWidth/2], [roadCenter[0]+roadWidth*2, roadCenter[1]], [width, roadCenter[1]]]


c1 = Car(0.1, 25, (20,roadCenter[1]-roadWidth/2), upperLaneWaypoints)
c5 = Car(0.1, 25, (-170,roadCenter[1]-roadWidth/2), upperLaneWaypoints)
c2 = Car(0.1, 25, (0,roadCenter[1]+roadWidth/2), bottomLaneWaypoints)
c3 = Car(0.1, 25, (-150,roadCenter[1]+roadWidth/2), bottomLaneWaypoints)
c4 = Car(0.1, 25, (-250,roadCenter[1]+roadWidth/2), bottomLaneWaypoints)
cars = [c1, c2, c3, c4, c5]


def drawRoad(screen):
  for roadLine in roadBoundaries:
    pygame.draw.line(screen, (0,0,0), (roadLine[0], roadLine[1]), (roadLine[2], roadLine[3]), 2)

  #for stopLine in StopLines:
  #  pygame.draw.line(screen, (255,0,0), (stopLine[0], stopLine[1]), (stopLine[2], stopLine[3]), 2)

def update(dt):
  """
  Update game. Called once per frame.
  dt is the amount of time passed since last frame.
  If you want to have constant apparent movement no matter your framerate,
  what you can do is something like
  
  x += v * dt
  
  and this will scale your velocity based on time. Extend as necessary."""

  for car in cars:
    car.update(dt, cars)

  
  # Go through events that are passed to the script by the window.
  for event in pygame.event.get():
    # We need to handle these events. Initially the only one you'll want to care
    # about is the QUIT event, because if you don't handle it, your game will crash
    # whenever someone tries to exit.
    if event.type == QUIT:
      pygame.quit() # Opposite of pygame.init
      sys.exit() # Not including this line crashes the script on Windows. Possibly
      # on other operating systems too, but I don't know for sure.
    # Handle other events as you wish.
 
def draw(screen):
  """
  Draw things to the window. Called once per frame.
  """
  screen.fill((255, 255, 255)) # Fill the screen with black.

  rect_color = (255, 0, 0)  # Red

  drawRoad(screen);

  for car in cars:
    car.draw(screen)
  
  # Redraw screen here.
  
  # Flip the display so that the things we drew actually show up.
  pygame.display.flip()
 
def runPyGame():
  # Initialise PyGame.
  pygame.init()
  
  # Set up the clock. This will tick every frame and thus maintain a relatively constant framerate. Hopefully.
  fps = 60.0
  fpsClock = pygame.time.Clock()
  
  # Set up the window.
  
  screen = pygame.display.set_mode((width, height))
  
  # screen is the surface representing the window.
  # PyGame surfaces can be thought of as screen sections that you can draw onto.
  # You can also draw surfaces onto other surfaces, rotate surfaces, and transform surfaces.
  
  # Main game loop.
  dt = 1/fps # dt is the time since last frame.
  while True: # Loop forever!
    update(dt) # You can update/draw here, I've just moved the code for neatness.
    draw(screen)
    
    dt = fpsClock.tick(fps)

runPyGame()