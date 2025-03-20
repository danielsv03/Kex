# Import standard modules.
import sys
 
# Import non-standard modules.
import pygame
from pygame.locals import *
import random

from Car import Car

highest_id = 0
width, height = 1500, 1000
carSize = 20;
roadCenter = [width/1.5, height/2]; # The center point of the road
roadWidth = 50; # The width of the road
traffic_light_status = 1;
traffic_light_speed = 10;
traffic_light_acc = 0.0;

merging_start_point = roadCenter[0]/2

roadBoundaries = [[roadCenter[0], roadCenter[1]-roadWidth, 0, roadCenter[1]-roadWidth], # Upper lane boundarie
                  [roadCenter[0], roadCenter[1], 0, roadCenter[1]],                     # Midle lane boundarie
                  [roadCenter[0], roadCenter[1]+roadWidth, 0, roadCenter[1]+roadWidth], # Lower lane boundarie
                  [roadCenter[0], roadCenter[1]-roadWidth, roadCenter[0]+roadWidth*2, roadCenter[1]-roadWidth/2], # Upper merge point
                  [roadCenter[0], roadCenter[1]+roadWidth, roadCenter[0]+roadWidth*2, roadCenter[1]+roadWidth/2], # Lower merge point
                  [roadCenter[0]+roadWidth*2, roadCenter[1]-roadWidth/2, width, roadCenter[1]-roadWidth/2], # New lane upper
                  [roadCenter[0]+roadWidth*2, roadCenter[1]+roadWidth/2, width, roadCenter[1]+roadWidth/2]] # New lane lower


upperLaneWaypoints = [[roadCenter[0]/2, roadCenter[1]-roadWidth/2], [roadCenter[0], roadCenter[1]-roadWidth/2], [roadCenter[0]+roadWidth*2, roadCenter[1]], [width, roadCenter[1]]]
bottomLaneWaypoints = [[roadCenter[0]/2, roadCenter[1]+roadWidth/2], [roadCenter[0], roadCenter[1]+roadWidth/2], [roadCenter[0]+roadWidth*2, roadCenter[1]], [width, roadCenter[1]]]

cars: list[Car]
cars = []

allowed_cars: list[Car]
allowed_cars = []

def is_clear(spawn_pos, lane: int):
        """Returns True if the spawn position is clear of other cars."""
        for car in cars:
            if car.lane != lane:
               continue
            if abs(car.position[0] - spawn_pos[0]) < carSize:  # Check if too close
                return False
        return True

def spawnCars(rate: float):
    """Spawns cars at the beginning of each lane based on rate with randomness."""
    global highest_id
    
    # Random chance to spawn a new car (controlled by rate)
    if random.random() > rate:
        return
    
    # Define spawn positions for each lane
    upper_lane_spawn = (0, roadCenter[1] - roadWidth / 2)
    bottom_lane_spawn = (0, roadCenter[1] + roadWidth / 2)

    # Check if there is space in each lane before spawning a car

    # Randomize speed for new cars
    speed = 0.1
    #speed = random.uniform(0.05, 0.2)

    #start = random.randint(0, round(roadCenter[0]))
    start = roadCenter[0]/2

    if (random.randint(1,2) == 1):
       highest_id += 1
       if is_clear(bottom_lane_spawn, 1):
          cars.append(Car(highest_id,speed, carSize, bottom_lane_spawn, bottomLaneWaypoints, 1, start))
    else:
        if is_clear(upper_lane_spawn, 2):
          highest_id += 1
          cars.append(Car(highest_id ,speed, carSize, upper_lane_spawn, upperLaneWaypoints, 2, start))
   

def find_first_colliding_car(carList: list[Car]) -> int:
   max_x = 0
   #current_car: int = None
   for car in carList:
      if (car.detect_future_collision and car.position[0] > max_x):
         max_x = car.position[0]
   return max_x


def bidding_algorithm(carList: list[Car]) -> None:
   global traffic_light_status, allowed_cars
   if (len(allowed_cars) != 0):
      for car in allowed_cars:
         if (car.position[0] > roadCenter[0] + roadWidth*2):
            allowed_cars.remove(car)
      return
   for car in carList:
      car.allowed_to_go = True
   max_x = find_first_colliding_car(carList)
   if (max_x != None):
      biddingUpper = 0
      biddingBottom = 0
      for car in carList:
         if (car.position[0] < max_x and car.position[0] > car.merging_start_point):
            if (car.lane == 1):
               biddingUpper += car.bid()
            else:
               biddingBottom += car.bid()
      allowed_lane = 0
      if (biddingUpper > biddingBottom):
         allowed_lane = 1
      else:
         allowed_lane = 2
      
      for car in carList:
         if (car.position[0] < max_x and car.position[0] > car.merging_start_point):
            if (car.lane != allowed_lane):
               car.allowed_to_go = False
            else:
               car.car_color = (0, 255, 0)
               allowed_cars.append(car)

def traffic_light_priority():
   global traffic_light_status
   up_count = 0
   down_count = 0
   for car in cars:
      if (car.position[0] < car.merging_start_point):
         continue
      if (car.lane == 1):
         up_count += 1
      elif (car.lane ==2):
         down_count += 1
      else:
         continue
   if (up_count > down_count):
      traffic_light_status = 1
   else:
      traffic_light_status = 2


      

def traffic_light(dt):
   global traffic_light_acc, traffic_light_speed, traffic_light_status
   traffic_light_acc = traffic_light_acc + dt
   if (traffic_light_acc > traffic_light_speed*1000):
      traffic_light_acc = 0
      
      if traffic_light_status == 1:
         traffic_light_status = 2
         print("2")
      else:
         print("1")
         traffic_light_status = 1


def drawRoad(screen):
  for roadLine in roadBoundaries:
    pygame.draw.line(screen, (0,0,0), (roadLine[0], roadLine[1]), (roadLine[2], roadLine[3]), 2)

  #for stopLine in StopLines:
  #  pygame.draw.line(screen, (255,0,0), (stopLine[0], stopLine[1]), (stopLine[2], stopLine[3]), 2)

def update(dt):
  global cars
  """
  Update game. Called once per frame.
  dt is the amount of time passed since last frame.
  If you want to have constant apparent movement no matter your framerate,
  what you can do is something like
  
  x += v * dt
  
  and this will scale your velocity based on time. Extend as necessary."""

  spawnCars(0.02)
  #traffic_light(dt)
  #traffic_light_priority()
  bidding_algorithm(cars)

  for car in cars:
    car.update(dt, cars, traffic_light_status)
    if (car.position[0] > width):
       cars.remove(car)
    
  #print(len(cars))

  
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