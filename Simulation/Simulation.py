# Import standard modules.
import sys
 
# Import non-standard modules.
import pygame
from pygame.locals import *
import random
import time
import matplotlib.pyplot as plt
import csv

from Car import Car

width, height = 1500, 1000
carSize = 20
roadCenter = [width/1.5, height/2] # The center point of the road
roadWidth = 50 # The width of the road
traffic_light_status = 1
traffic_light_speed = 10
traffic_light_acc = 0.0

# Evaluation metrics
Throughput = [0]
Avg_waitingtime = [0]
Avg_stoptime = [0]
Fairness = [0]
Stability = [0]
Collision_count = [0]

# Helping metrics
Passed_cars = 0
Last_time = time.time()

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

def update_metrics():
   global Throughput, Avg_waitingtime, Avg_stoptime, Fairness, Stability, Collision_count, Last_time, Passed_cars

   # Throughput
   delta = time.time() - Last_time
   Throughput.append(round(Passed_cars / delta, 2))

def save_metrics_to_csv(filename="Datasets/TimeBased.csv"):
   """Saves all evaluation metrics to a CSV file."""
   
   global Throughput, Avg_waitingtime, Avg_stoptime, Fairness, Stability, Collision_count

   # Open file in write mode (overwrite if exists)
   with open(filename, "w", newline="") as file:
      writer = csv.writer(file)

      # Write header row
      writer.writerow(["Throughput", "Avg Waiting Time", "Avg Stop Time", "Fairness", "Stability", "Collision Count"])

      # Write data (Each row contains values from the same time step)
      for i, (t, wait, stop, fair, stab, coll) in enumerate(zip(Throughput, Avg_waitingtime, Avg_stoptime, Fairness, Stability, Collision_count)):
         writer.writerow([i, t, wait, stop, fair, stab, coll])

   print(f"Metrics saved to {filename}")

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

    start = random.randint(0, round(roadCenter[0]))

    if (random.randint(1,2) == 1):
       if is_clear(bottom_lane_spawn, 1):
          cars.append(Car(speed, carSize, bottom_lane_spawn, bottomLaneWaypoints, 1, start))
    else:
        if is_clear(upper_lane_spawn, 2):
          cars.append(Car(speed, carSize, upper_lane_spawn, upperLaneWaypoints, 2, start))

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
   """
   Update game. Called once per frame.
   dt is the amount of time passed since last frame.
   If you want to have constant apparent movement no matter your framerate,
   what you can do is something like
   
   x += v * dt
   
   and this will scale your velocity based on time. Extend as necessary."""

   global Passed_cars

   spawnCars(0.02)
   traffic_light(dt)
   # traffic_light_priority()

   for car in cars:
      car.update(dt, cars, traffic_light_status)
      if (car.position[0] > width):
         cars.remove(car)
         Passed_cars = Passed_cars + 1
         update_metrics()
  
   # Go through events that are passed to the script by the window.
   for event in pygame.event.get():
      # We need to handle these events. Initially the only one you'll want to care
      # about is the QUIT event, because if you don't handle it, your game will crash
      # whenever someone tries to exit.
      if event.type == QUIT:
         save_metrics_to_csv()
         pygame.quit() # Opposite of pygame.init
         sys.exit() # Not including this line crashes the script on Windows. Possibly
         # on other operating systems too, but I don't know for sure.
         # Handle other events as you wish.

def draw_text(screen, text, position, font_size=24, color=(0, 0, 0)):
    """Helper function to draw text on the screen."""
    font = pygame.font.Font(None, font_size)  # Use default font
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)

def draw(screen):
   """
   Draw things to the window. Called once per frame.
   """
   screen.fill((255, 255, 255)) # Fill the screen with black.

   rect_color = (255, 0, 0)  # Red

   drawRoad(screen)

   for car in cars:
      car.draw(screen)

   # Display variable values in the top-left corner
   draw_text(screen, f"Throughput: {Throughput[len(Throughput) - 1]}", (10, 10))
   draw_text(screen, f"Average Waiting Time: {Avg_waitingtime[len(Avg_waitingtime) - 1]}", (10, 40))
   draw_text(screen, f"Average Stop Time: {Avg_stoptime[len(Avg_stoptime) - 1]}", (10, 70))
   draw_text(screen, f"Fairness: {Fairness[len(Fairness) - 1]}", (10, 100))
   draw_text(screen, f"Traffic Stability: {Stability[len(Stability) - 1]}", (10, 130))
   draw_text(screen, f"Collision Count: {Collision_count[len(Collision_count) - 1]}", (10, 160))
   
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
    
    dt = fpsClock.tick(fps) * 5

runPyGame()