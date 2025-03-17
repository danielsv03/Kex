import numpy as np
import pygame
from pygame.locals import *

class Car:
    speed: int
    direction: np.ndarray
    size: int
    position: np.ndarray
    waypoints: list
    current_waypoint = 0


    def __init__(self, speed=0, size=25, position=(0,0), waypoints=[[0,0]]):
        self.speed = speed
        self.size = size
        self.position = np.array(position, dtype=float)
        self.waypoints = waypoints
        self.direction = self._normalize(waypoints[self.current_waypoint]-self.position)

    def _normalize (self, vector: tuple) -> np.ndarray:
        vector = np.array(vector, dtype=float)
        norm = np.linalg.norm(vector)
        return vector/norm if norm != 0 else np.array([1, 0])

    def _move(self, dt) -> None:
        displacement = self.direction * self.speed * dt
        self.position += displacement

    def _follow_waypoints(self) -> None:
        waypoint = self.waypoints[self.current_waypoint] # Current waypoint
        distance_to_waypoint = np.linalg.norm(waypoint - self.position)
        if (distance_to_waypoint < 10): # Change to new waypoint
            if (len(self.waypoints) > self.current_waypoint+1):
                self.current_waypoint += 1
                self.change_direction(self.waypoints[self.current_waypoint] - self.position)

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
    
    def update(self, dt):
        self._follow_waypoints()
        self._move(dt)

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
        rotated_corners = np.array([self.rotate_point(p, angle, self.position) for p in corners])

        # Convert to integer tuples for Pygame
        polygon_points = [tuple(p) for p in rotated_corners]

        # Draw the rotated rectangle (car)
        pygame.draw.polygon(screen, (255, 0, 0), polygon_points)  # Red car
        

    
