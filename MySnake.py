import random
import sys

import pygame


# 게임 설정
GRID_SIZE = 20
TILE_SIZE = 25
WINDOW_WIDTH = GRID_SIZE * TILE_SIZE
WINDOW_HEIGHT = GRID_SIZE * TILE_SIZE
FPS = 8

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (76, 175, 80)
DARK_GREEN = (46, 125, 50)
RED = (244, 67, 54)
BLUE = (33, 150, 243)
BACKGROUND = (18, 18, 18)
GRID_COLOR = (40, 40, 40)


class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("malgun gothic", 28, bold=True)
        self.small_font = pygame.font.SysFont("malgun gothic", 18)

        self.reset_game()

    def reset_game(self):
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.snake = [
            (GRID_SIZE // 2, GRID_SIZE // 2),
            (GRID_SIZE // 2 - 1, GRID_SIZE // 2),
            (GRID_SIZE // 2 - 2, GRID_SIZE // 2),
        ]
        self.score = 0
        self.game_over = False
        self.spawn_apple()

    def spawn_apple(self):
        while True:
            apple = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1),
            )
            if apple not in self.snake:
                self.apple = apple
                return

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if self.game_over and event.key in (pygame.K_RETURN, pygame.K_r):
                    self.reset_game()
                    return

                if event.key == pygame.K_UP and self.direction != (0, 1):
                    self.next_direction = (-1, 0)
                elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                    self.next_direction = (1, 0)
                elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                    self.next_direction = (0, -1)
                elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                    self.next_direction = (0, 1)

    def update(self):
        if self.game_over:
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # 벽 충돌 검사
        if (
            new_head[0] < 0
            or new_head[0] >= GRID_SIZE
            or new_head[1] < 0
            or new_head[1] >= GRID_SIZE
        ):
            self.game_over = True
            return

        # 자기 몸 충돌 검사
        # 꼬리가 움직일 예정이라면, 꼬리 위치로 이동하는 것은 허용한다.
        body_without_tail = self.snake[:-1]
        if new_head in body_without_tail:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.apple:
            self.score += 1
            self.spawn_apple()
        else:
            self.snake.pop()

    def draw_grid(self):
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

    def draw_snake(self):
        for index, segment in enumerate(self.snake):
            x, y = segment
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            color = GREEN if index == 0 else DARK_GREEN
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)

    def draw_apple(self):
        x, y = self.apple
        center_x = x * TILE_SIZE + TILE_SIZE // 2
        center_y = y * TILE_SIZE + TILE_SIZE // 2
        radius = TILE_SIZE // 2 - 4
        pygame.draw.circle(self.screen, RED, (center_x, center_y), radius)

    def draw_score(self):
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        text = self.font.render("GAME OVER", True, WHITE)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        self.screen.blit(text, text_rect)

        hint = self.small_font.render("Press Enter or R to restart", True, WHITE)
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        self.screen.blit(hint, hint_rect)

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()

            self.screen.fill(BACKGROUND)
            self.draw_grid()
            self.draw_apple()
            self.draw_snake()
            self.draw_score()

            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = SnakeGame()
    game.run()
