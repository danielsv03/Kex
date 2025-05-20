# Import standard modules.
import math
import sys
 
# Import non-standard modules.
import numpy as np
import pygame
from pygame.locals import *
import random
import csv

from Car import Car
# One of: "Zipper", "TimeBased", "PriorityBased", "AuctionBased"
CURRENT_HEURISTIC = "Zipper"
run_count = 0
if (len(sys.argv) < 2):
   run_count = 1
else:
   run_count = int(sys.argv[1])

print("Run count: " + str(run_count))

width, height = 1500, 1000
carSize = 20
roadCenter = [width/1.5, height/2] # The center point of the road
roadWidth = 50 # The width of the road
traffic_light_status = 1
traffic_light_speed = 10
traffic_light_acc = 0.0
traffic_light_delay = 0.0
traffic_light_prev = 3
prev_cound = 0
traffic_light_green_time = 0.0

# Evaluation metrics
Throughput_tot = []
Avg_waitingtime = []
Avg_stoptime = []
Stop_count = []
Fairness = []
Stability = []

# Helping metrics
Passed_cars_l1 = 0
Passed_cars_l2 = 0
Throughput_l1 = 0
Throughput_l2 = 0
Passing_durations_sum = 0
Passing_durations_count = 0
Stop_times_sum = 0
Stop_times_count = 0
Stops = 0
Car_speeds_count = 0
Car_speeds_sum = 0
Car_speeds_last = 0
Car_speeds_mean = 0
Car_speeds_sq = 0
Elapsed_time = 0
ticks = 0

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

def update_metrics():
   global Throughput_l1, Throughput_l2, Car_speeds_mean, Car_speeds_sq

   # Throughputs
   passed_cars_tot = Passed_cars_l1 + Passed_cars_l2
   Throughput_tot.append(round(passed_cars_tot / Elapsed_time, 2))
   Throughput_l1 = round(Passed_cars_l1 / Elapsed_time, 2)
   Throughput_l2 = round(Passed_cars_l2 / Elapsed_time, 2)

   # Avg waiting time
   if (Passing_durations_count != 0):
      Avg_waitingtime.append(round(Passing_durations_sum / Passing_durations_count, 2))

   # Avg stop time
   if (Stop_times_count != 0):
      Avg_stoptime.append(round(Stop_times_sum / Stop_times_count, 2))
   else:
      Avg_stoptime.append(0)

   # Stop count
   Stop_count.append(Stops)

   # Fairness
   if (Throughput_l1 != 0 and Throughput_l2 != 0):
      Fairness.append(round(JainsFariness(Throughput_l1, Throughput_l2), 2))

   # Stability (Welfords algorithm)
   Car_speeds_mean = round(Car_speeds_sum / Car_speeds_count, 2)
   Car_speeds_sq += (Car_speeds_mean - Car_speeds_last)**2
   Stability.append(round(finalize_stddev(Car_speeds_count, Car_speeds_sq) * 100, 3))

def JainsFariness(val1, val2):
   return (val1 + val2)**2 / (2 * (val1**2 + val2**2))

def finalize_stddev(n, M2):
    if n < 2:
        return float('nan')  # Not enough data for standard deviation
    variance = M2 / (n - 1)
    return math.sqrt(variance)

def save_metrics_to_csv(filename="Datasets/"+CURRENT_HEURISTIC+"_"+str(run_count)+".csv"):
   """Saves all evaluation metrics to a CSV file."""

   # Open file in write mode (overwrite if exists)
   with open(filename, "w", newline="") as file:
      writer = csv.writer(file)

      # Write header row
      writer.writerow(["Time Step", "Throughput", "Avg Passing Time", "Avg Stationary Duration", "Stop Count", "Fairness", "Stability (Speed Deviation)"])

      # Write data (Each row contains values from the same time step)
      for i, (t, wait, stoptm, stop, fair, stab) in enumerate(zip(Throughput_tot, Avg_waitingtime, Avg_stoptime, Stop_count, Fairness, Stability)):
         writer.writerow([i, t, wait, stoptm, stop, fair, stab])

   print(f"Metrics saved to {filename}")

def is_clear(spawn_pos, lane: int):
        """Returns True if the spawn position is clear of other cars."""
        for car in cars:
            if car.lane != lane:
               continue
            if abs(car.position[0] - spawn_pos[0]) < carSize*3:  # Check if too close
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

    #start = random.randint(0, round(roadCenter[0]))
    start = roadCenter[0]/2

    if (random.randint(1,2) == 1):
       if is_clear(bottom_lane_spawn, 1):
          cars.append(Car(speed, carSize, bottom_lane_spawn, bottomLaneWaypoints, 1, start, CURRENT_HEURISTIC))
    else:
        if is_clear(upper_lane_spawn, 2):
          cars.append(Car(speed, carSize, upper_lane_spawn, upperLaneWaypoints, 2, start, CURRENT_HEURISTIC))

def bidding_algorithm(dt, carList: list[Car]) -> None:
   global allowed_cars
   if (len(allowed_cars) != 0):
      for car in allowed_cars:
         if (car.position[0] > roadCenter[0] + roadWidth*2):
            allowed_cars.remove(car)
      return
   else:
      for car in carList:
         car.allowed_to_go = True
   collision_detected = False
   for car in carList:
      distance_to_merge = np.linalg.norm(car.position - car.waypoints[1])
      if (distance_to_merge < 30):
         if (car.detect_future_collision(dt, carList)):
            #print("GUUH")
            collision_detected = True
         else:
            collision_detected = False
   
   if (collision_detected):
      biddingUpper = 0
      biddingBottom = 0
      for car in carList:
         if (car.position[0] > car.merging_start_point and car.position[0] < car.waypoints[1][0]):
            if (car.lane == 1):
               biddingUpper += car.bid()
            else:
               biddingBottom += car.bid()
      allowed_lane = 1
      if (biddingUpper > biddingBottom):
         allowed_lane = 1
      else:
         allowed_lane = 2
      
      for car in carList:
         if (car.position[0] > car.merging_start_point and car.position[0] < car.waypoints[1][0]):
            if (car.lane == allowed_lane):
               car.allowed_to_go = True
               car.car_color = (0, 255, 0)
               allowed_cars.append(car)
            else:
               car.car_color = (0, 0, 255)
               car.allowed_to_go = False

def traffic_light_priority(dt):
    global traffic_light_status, traffic_light_prev
    global traffic_light_acc, traffic_light_delay, traffic_light_green_time

    traffic_light_green_time += dt

    up_count = 0
    down_count = 0

    for car in cars:
        if car.position[0] < car.merging_start_point:
            continue
        if car.lane == 1:
            up_count += 1
        elif car.lane == 2:
            down_count += 1

    # Decide desired next status based on car counts
    desired_status = 1 if up_count > down_count else 2

    if traffic_light_status == 3:
        # Currently in red-for-all transition
        traffic_light_delay += dt
        if traffic_light_delay > 2000:  # 2 seconds of red
            traffic_light_status = traffic_light_prev
            traffic_light_delay = 0
            traffic_light_green_time = 0
            print(f"Light switched to lane {traffic_light_status}")
    elif desired_status != traffic_light_status and traffic_light_green_time > 10000:
        # If 10 seconds have passed on current green, and we want to switch
        traffic_light_prev = desired_status
        traffic_light_status = 3  # Red for all
        traffic_light_delay = 0  # Start red timer
        print("Switching to red before changing direction.")

def traffic_light(dt):
   global traffic_light_acc, traffic_light_speed, traffic_light_status, traffic_light_delay, traffic_light_prev
   traffic_light_acc = traffic_light_acc + dt
   if (traffic_light_acc > traffic_light_speed*1000):
      traffic_light_delay = traffic_light_delay + dt
      if (traffic_light_prev == 3):
         traffic_light_prev = traffic_light_status
      traffic_light_status = 3
      if (traffic_light_delay > 2*1000):
         traffic_light_acc = 0
         traffic_light_status = traffic_light_prev
         if traffic_light_status == 1:
            traffic_light_status = 2
            print("2")
         else:
            print("1")
            traffic_light_status = 1
         traffic_light_delay = 0
         traffic_light_prev = 3
         

def drawRoad(screen):
  for roadLine in roadBoundaries:
    pygame.draw.line(screen, (0,0,0), (roadLine[0], roadLine[1]), (roadLine[2], roadLine[3]), 2)

  #for stopLine in StopLines:
  #  pygame.draw.line(screen, (255,0,0), (stopLine[0], stopLine[1]), (stopLine[2], stopLine[3]), 2)

def update(dt):
   global cars, Passed_cars_l1, Passed_cars_l2, Stops, Passing_durations_count, Passing_durations_sum, Stop_times_count, Stop_times_sum, Car_speeds_sum, Car_speeds_count, Car_speeds_last, Elapsed_time, ticks
   """
   Update game. Called once per frame.
   dt is the amount of time passed since last frame.
   If you want to have constant apparent movement no matter your framerate,
   what you can do is something like
   
   x += v * dt
   
   and this will scale your velocity based on time. Extend as necessary."""

   Elapsed_time += dt / 1000
   spawnCars(0.07)


   match CURRENT_HEURISTIC:
      case "TimeBased":
         traffic_light(dt)
      case "PriorityBased":
         traffic_light_priority(dt)
      case "AuctionBased":
         bidding_algorithm(dt, cars)


   for car in cars:
      car.update(dt, cars, traffic_light_status)

      # Save speed for all cars
      Car_speeds_last = car.speed
      Car_speeds_sum += car.speed
      Car_speeds_count += 1

      # Save stop durations of cars and increment total stop count
      if (car.last_stop_duration > 0):
         Stop_times_sum += car.last_stop_duration
         Stop_times_count += 1
         Stops += 1

      if (car.position[0] > width):
         # Increase passed-cars-count
         if (car.origin_lane == 1):
            Passed_cars_l1 += 1
         else:
            Passed_cars_l2 += 1

         # Calculate duration for the car to pass
         Passing_durations_sum += car.elapsed_time
         Passing_durations_count += 1

         cars.remove(car)
      
      update_metrics()
  
   ticks = ticks + 1
   if (ticks > 6000):
      save_metrics_to_csv()
      pygame.quit()
      sys.exit()

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

def draw_text(screen, text, position, font_size=32, color=(0, 0, 0)):
    """Helper function to draw text on the screen."""
    font = pygame.font.Font(None, font_size)  # Use default font
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)

def draw(screen):
   """
   Draw things to the window. Called once per frame.
   """
   screen.fill((255, 255, 255)) # Fill the screen with black.

   drawRoad(screen)

   for car in cars:
      car.draw(screen)

   # Display variable values in the top-left corner
   draw_text(screen, f"Throughput: {Throughput_tot[-1] if len(Throughput_tot) > 0 else 0} vehicles/sec", (10, 10))
   draw_text(screen, f"Average Waiting Time: {Avg_waitingtime[-1] if len(Avg_waitingtime) > 0 else 0} sec/vehicle", (10, 40))
   draw_text(screen, f"Average Stop Time: {Avg_stoptime[-1] if len(Avg_stoptime) > 0 else 0} sec/vehicle", (10, 70))
   draw_text(screen, f"Stop Count: {Stop_count[-1] if len(Stop_count) > 0 else 0} stops", (10, 100))
   draw_text(screen, f"Fairness: {Fairness[-1] if len(Fairness) > 0 else 0} (Lane 1: {Throughput_l1}, Lane 2: {Throughput_l2})", (10, 130))
   draw_text(screen, f"Traffic Stability: {Stability[-1] if len(Stability) > 0 else 0}", (10, 160))
   draw_text(screen, f"Simulation complete: {round(ticks * 100 / 60000, 1)}%", (10, 190))
   
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
  SIMULATION_SPEED = 10
  while True: # Loop forever!
    for _ in range(SIMULATION_SPEED):
      update(dt) # You can update/draw here, I've just moved the code for neatness.
    draw(screen)
    dt = fpsClock.tick(fps)

runPyGame()