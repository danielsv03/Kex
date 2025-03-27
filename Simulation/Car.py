import numpy as np
import pygame
import time
from pygame.locals import *

class Car:
    speed: int
    initial_speed: int
    direction: np.ndarray
    size: int
    position: np.ndarray
    waypoints: list
    current_waypoint = 0
    rotated_corners: list
    origin_lane: int
    lane: int
    merging_start_point: float
    car_color: tuple
    allowed_to_go: bool
    stopped_timestamp: int
    last_stop_duration: int
    elapsed_time: int
    heuristic: str


    def __init__(self ,speed=0, size=25, position=(0,0), waypoints=[[0,0]], lane=1, merging_start_point=0.0, heuristic="none"):
        self.speed = speed
        self.size = size
        self.position = np.array(position, dtype=float)
        self.waypoints = waypoints
        self.direction = self._normalize(waypoints[self.current_waypoint]-self.position)
        self.rotated_corners = []
        self.lane = lane
        self.origin_lane = lane
        self.initial_speed = speed
        self.merging_start_point = merging_start_point
        self.car_color = (255, 0, 0)
        self.allowed_to_go = True
        self.elapsed_time = 0
        self.stopped_timestamp = 0
        self.last_stop_duration = 0
        self.heuristic = heuristic

    def _normalize (self, vector: tuple) -> np.ndarray:
        vector = np.array(vector, dtype=float)
        norm = np.linalg.norm(vector)
        return vector/norm if norm != 0 else np.array([1, 0])
    
    def bid(self) -> int:
        return np.random.lognormal(1.7, 0.5)

    def _move(self, dt) -> None:
        displacement = self.direction * self.speed * dt
        self.position += displacement

    def _follow_waypoints(self) -> None:
        waypoint = self.waypoints[self.current_waypoint] # Current waypoint
        distance_to_waypoint = np.linalg.norm(waypoint - self.position)
        if (distance_to_waypoint < 10): # Change to new waypoint
            if (len(self.waypoints) > self.current_waypoint+1):
                self.current_waypoint += 1
                if (self.current_waypoint == 3):
                    self.lane = 3
                self.change_direction(self.waypoints[self.current_waypoint] - self.position)

    def traffic_light_simple(self, dt: float, carList: list["Car"], light_status: int) -> None:
        distance_to_light = np.linalg.norm(self.position - self.waypoints[1])

        if (distance_to_light < 40 and light_status != self.lane):
            self.prevent_collision_simple(dt, carList, [self.waypoints[1]])
        else:
            self.prevent_collision_simple(dt, carList)

    def bidding_system(self, dt: float, carList: list["Car"]) -> None:
        distance_to_merge = np.linalg.norm(self.position - self.waypoints[1])

        if (distance_to_merge < 40):
            if (self.allowed_to_go):
                self.prevent_collision_simple(dt, carList)
                return
            self.prevent_collision_simple(dt, carList, [self.waypoints[1]])
        else:
            self.prevent_collision_simple(dt, carList)


    def prevent_collision_simple(self, dt: float, carList: list["Car"], extraStop: list = []) -> None:
        """
        A lane-aware, distance-based collision avoidance that smoothly accelerates
        or decelerates to maintain a safe following distance. Only stops if truly necessary.
        """
        # --- Tunable parameters ---
        safety_distance   = self.size * 2.0   # Minimum gap we want to maintain
        acceleration      = 0.0002  # How quickly we speed up (units per dt)
        deceleration      = 0.0005  # How quickly we slow down (units per dt)

        # Vector representing our travel direction
        dir_self = self.direction  # Already normalized

        future_self = self.position + dir_self * max(10 , self.speed * 300)

        collision = False

        for other in carList:
            if other is self:
                continue
            
            future_other = other.position + other.direction * other.speed

            distance_prediction = np.linalg.norm(future_self - future_other)

            if (distance_prediction < safety_distance):
                collision = True

        if (len(extraStop) > 0):
            for stop in extraStop:
                distance_prediction = np.linalg.norm(future_self - np.array((stop[0], stop[1]), dtype=float))
            if (distance_prediction < safety_distance):
                collision = True

        if (collision):
            self.speed = max(0.0, self.speed - deceleration*dt)
            if self.speed == 0.0:
               self.car_color = (255, 0, 0)
            else:
               self.car_color = (0, 0, 255)
        else:
            self.car_color = (0, 255, 0)
            self.speed = min(self.initial_speed, self.speed + acceleration*dt)
    
    def detect_future_collision(self, dt: float, carList: list["Car"]) -> bool:
        # --- Tunable parameters ---
        safety_distance = self.size * 2    # Distance threshold to begin slowing down
        
        for car in carList:
            if car is self:
                continue
            
            # Predict future positions. If different lane, only track x-axis.
            if car.lane != self.lane:
                future_position_self  = np.array([self.position[0], 0.0], dtype=float) \
                                    + (self.direction * self.speed * 600)
                future_position_other = np.array([car.position[0], 0], dtype=float)
            else:
                continue
            
            distance = np.linalg.norm(future_position_self - future_position_other)
            
            if distance < safety_distance:
                self.allowed_to_go = False
                #car.allowed_to_go = False
                return True
            
        return False
            

    def zipper_merge_complex(self, dt: float, carList: list["Car"]) -> None:
        """
        Adjusts speed dynamically based on distance to other cars in the same or adjacent lanes.
        Cars accelerate if space is free, slow down proportionally if another car is close,
        and only stop completely if absolutely necessary.
        """
        # If we haven't reached the correct waypoint, just run the basic collision avoidance.
        
        # --- Tunable parameters ---
        safety_distance = self.size * 2    # Distance threshold to begin slowing down
        max_speed       = self.initial_speed            # Desired maximum speed when unimpeded
        acceleration    = 0.0003             # How quickly the car accelerates/decelerates
        stop_threshold  = 0.009            # If computed safe speed is < this, we treat it as 0
        
        # We'll figure out the desired speed based on the nearest car conflict.
        # Start by assuming we can go max speed, then reduce if needed.
        desired_speed = max_speed
        
        for car in carList:
            if car is self:
                continue
            
            # Predict future positions. If different lane, only track x-axis.
            if car.lane != self.lane:
                future_position_self  = np.array([self.position[0], 0.0], dtype=float) \
                                    + (self.direction * self.speed * 400)
                future_position_other = np.array([car.position[0], 0], dtype=float)
            else:
                future_position_self  = self.position + (self.direction * self.speed * 400)
                future_position_other = car.position
            
            distance = np.linalg.norm(future_position_self - future_position_other)
            
            # If the distance is below the "safety_distance," reduce speed proportionally
            # so that distance / safety_distance gives a fraction in [0..1].
            if distance < safety_distance:
                # Speed limit based on how close we are:
                #   closer -> fraction goes toward 0,
                #   at safe distance -> fraction ~ 1 (no slowdown).
                fraction_of_safe = distance / float(safety_distance)
                
                # Compute the maximum allowed speed we can safely travel.
                safe_speed = fraction_of_safe * max_speed
                
                # If it's extremely low, treat as a stop condition.
                if safe_speed < stop_threshold:
                    safe_speed = 0
                    self.car_color = (255, 0, 0)
                
                # Among all cars, pick the *minimum* safe speed — the strongest constraint.
                desired_speed = min(desired_speed, safe_speed)
        
        # Smoothly move current speed to desired speed:
        if self.speed < desired_speed:
            # Accelerate up to desired_speed
            self.speed = min(self.speed + acceleration * dt, desired_speed)
        else:
            # Decelerate down to desired_speed
            self.speed = max(self.speed - acceleration * dt, desired_speed)


    def change_direction(self, new_direction: tuple) -> None:
        self.direction = self._normalize(new_direction)

    def get_rotation_angle(self):
        """Calculates the rotation angle in degrees from direction vector."""
        angle = np.degrees(np.arctan2(self.direction[1], self.direction[0]))
        return angle  # Pygame expects rotation in degrees

    def rotate_point(self, point, angle, center):
        """Rotates a point around a center by a given angle in degrees."""
        angle = np.radians(angle)
        sin_a, cos_a = np.sin(angle), np.cos(angle)

        # Translate point to origin
        px, py = point - center

        # Apply rotation
        x_new = px * cos_a - py * sin_a
        y_new = px * sin_a + py * cos_a

        # Translate back
        return np.array([x_new, y_new]) + center
    
    def update(self, dt, carList: list["Car"], light_status: int):
        self.elapsed_time += dt / 1000
        self._follow_waypoints()
        self._move(dt)
        
        if (self.position[0] > self.merging_start_point and self.current_waypoint < 2):
            match self.heuristic:
                case "Zipper":
                    self.zipper_merge_complex(dt, carList)
                case "TimeBased":
                    self.traffic_light_simple(dt, carList, light_status)
                case "PriorityBased":
                    self.traffic_light_simple(dt, carList, light_status)
                case "AuctionBased":
                    self.bidding_system(dt, carList)
        else:
            self.prevent_collision_simple(dt, carList)
    
        if (self.last_stop_duration > 0):
            self.last_stop_duration = 0     # Reset last stop time after 1 tick

        if (self.speed == 0 and self.stopped_timestamp == 0):   # Car was stopped
            self.stopped_timestamp = self.elapsed_time    # Save time when vehicle was stopped
        
        if (self.speed > 0 and self.stopped_timestamp > 0):   # Vehicle is moving and was previously stopped
            self.last_stop_duration = self.elapsed_time - self.stopped_timestamp  # Calculate the duration of the stop
            self.stopped_timestamp = 0
        


    def draw(self, screen: pygame.Surface):
        """Draws the car as a rotated rectangle using pygame.draw.polygon."""
        car_width = self.size
        car_length = self.size * 2  # Assume the car is twice as long as its width
        cx, cy = self.position  # Car's center position

        # Define unrotated rectangle corners (relative to the center)
        half_width = car_width / 2
        half_length = car_length / 2

        corners = np.array([
            [cx - half_length, cy - half_width],  # Top-left
            [cx + half_length, cy - half_width],  # Top-right
            [cx + half_length, cy + half_width],  # Bottom-right
            [cx - half_length, cy + half_width]   # Bottom-left
        ])

        # Rotate each corner around the center
        angle = self.get_rotation_angle()
        self.rotated_corners = np.array([self.rotate_point(p, angle, self.position) for p in corners])

        # Convert to integer tuples for Pygame
        polygon_points = [tuple(p) for p in self.rotated_corners]

        # Draw the rotated rectangle (car)
        pygame.draw.polygon(screen, self.car_color, polygon_points)  # Red car
        

    
