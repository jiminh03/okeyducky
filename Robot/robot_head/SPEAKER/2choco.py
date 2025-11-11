import pygame
from time import sleep

pygame.mixer.init()
pygame.mixer.music.load("choco.wav")  # test.wav 파일 경로
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    sleep(0.1)

