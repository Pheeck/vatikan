"""
The Menu class

This file contains the class representing the main menu. Main menu let's you
choose if you'd like to play against yourself, against AI or if you'd like to
see two AI opponents play against each other.
"""

import pygame

from config import *

class Menu:
    def __init__(self, screen):
        self.screen = screen

        width = (SCREEN_SIZE[0] - 3 * STACK_PX_MARGINS) / 2
        height = (SCREEN_SIZE[1] - 3 * STACK_PX_MARGINS) / 2
        self.info_rect = pygame.Rect(
            (STACK_PX_MARGINS, STACK_PX_MARGINS),
            (width, height)
        )
        self.player_vs_player_rect = pygame.Rect(
            (2 * STACK_PX_MARGINS + width, STACK_PX_MARGINS),
            (width, height)
        )
        self.player_vs_ai_rect = pygame.Rect(
            (STACK_PX_MARGINS, 2 * STACK_PX_MARGINS + height),
            (width, height)
        )
        self.ai_vs_ai_rect = pygame.Rect(
            (2 * STACK_PX_MARGINS + width, 2 * STACK_PX_MARGINS + height),
            (width, height)
        )

        medium_font = pygame.font.SysFont(FONT_NAME, MEDIUM_FONT_SIZE)
        big_font = pygame.font.SysFont(FONT_NAME, BIG_FONT_SIZE)
        self.title_text = big_font.render(
            "Karetni hra VATIKAN",
            True,
            TEXT_COLOR
        )
        self.help_text = medium_font.render(
            "Vyberte si jeden z hernich modu." \
            + "Zbavte se vsech karet ze sve ruky.",
            True,
            TEXT_COLOR
        )
        self.player_vs_player_text = medium_font.render(
            "Hrac proti hraci",
            True,
            TEXT_COLOR
        )
        self.player_vs_ai_text = medium_font.render(
            "Hrac proti AI",
            True,
            TEXT_COLOR
        )
        self.ai_vs_ai_text = medium_font.render(
            "AI proti AI",
            True,
            TEXT_COLOR
        )

    def draw(self):
        self.screen.fill(BG_COLOR)

        pos = (
                self.info_rect.centerx \
                - self.title_text.get_width() / 2,
                self.info_rect.centery \
                - (self.title_text.get_height() \
                + self.help_text.get_height()) / 2
        )
        self.screen.blit(self.title_text, pos)
        pos = (
                self.info_rect.centerx \
                - self.help_text.get_width() / 2,
                pos[1] + self.title_text.get_height()
        )
        self.screen.blit(self.help_text, pos)

        pygame.draw.rect(self.screen, FG_COLOR, self.player_vs_player_rect)
        pos = (
                self.player_vs_player_rect.centerx \
                - self.player_vs_player_text.get_width() / 2,
                self.player_vs_player_rect.centery \
                - self.player_vs_player_text.get_height() / 2
        )
        self.screen.blit(self.player_vs_player_text, pos)

        pygame.draw.rect(self.screen, FG_COLOR, self.player_vs_ai_rect)
        pos = (
                self.player_vs_ai_rect.centerx \
                - self.player_vs_ai_text.get_width() / 2,
                self.player_vs_ai_rect.centery \
                - self.player_vs_ai_text.get_height() / 2
        )
        self.screen.blit(self.player_vs_ai_text, pos)

        pygame.draw.rect(self.screen, FG_COLOR, self.ai_vs_ai_rect)
        pos = (
                self.ai_vs_ai_rect.centerx \
                - self.ai_vs_ai_text.get_width() / 2,
                self.ai_vs_ai_rect.centery \
                - self.ai_vs_ai_text.get_height() / 2
        )
        self.screen.blit(self.ai_vs_ai_text, pos)

        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    if self.player_vs_player_rect.collidepoint(pos):
                        return PLAYER_VS_PLAYER
                    elif self.player_vs_ai_rect.collidepoint(pos):
                        return PLAYER_VS_AI
                    elif self.ai_vs_ai_rect.collidepoint(pos):
                        return AI_VS_AI

            self.draw()
            clock.tick(FPS)
