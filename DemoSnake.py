import random
import sys

import pygame


# ----------------------------
# Config
# ----------------------------
COLS = 10
ROWS = 20
BLOCK = 30
BOARD_WIDTH = COLS * BLOCK
BOARD_HEIGHT = ROWS * BLOCK
SIDE_PANEL_WIDTH = 180
WINDOW_WIDTH = BOARD_WIDTH + SIDE_PANEL_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT
FPS = 30

# ----------------------------
# Shapes
# ----------------------------
SHAPES = {
    "I": [
        [1, 1, 1, 1]
    ],
    "J": [
        [1, 0, 0],
        [1, 1, 1],
    ],
    "L": [
        [0, 0, 1],
        [1, 1, 1],
    ],
    "O": [
        [1, 1],
        [1, 1],
    ],
    "S": [
        [0, 1, 1],
        [1, 1, 0],
    ],
    "T": [
        [0, 1, 0],
        [1, 1, 1],
    ],
    "Z": [
        [1, 1, 0],
        [0, 1, 1],
    ],
}

COLORS = {
    "I": (56, 189, 248),
    "J": (96, 165, 250),
    "L": (251, 191, 36),
    "O": (250, 204, 21),
    "S": (74, 222, 128),
    "T": (192, 132, 252),
    "Z": (248, 113, 113),
    "ghost": (255, 255, 255),
}


# ----------------------------
# Game class
# ----------------------------
class TetrisGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tetris - Python Port")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("malgun gothic", 28, bold=True)
        self.small_font = pygame.font.SysFont("malgun gothic", 18)
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.last_drop = 0
        self.drop_interval = 700

        self.board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.current = self.create_piece()
        self.next_piece = self.create_piece()
        self.update_hud()

    def create_piece(self):
        piece_type = random.choice(list(SHAPES.keys()))
        matrix = [row[:] for row in SHAPES[piece_type]]
        return {
            "type": piece_type,
            "matrix": matrix,
            "x": (COLS - len(matrix[0])) // 2,
            "y": -1,
        }

    def update_hud(self):
        pass

    def spawn_piece(self):
        self.current = self.next_piece
        self.current["x"] = (COLS - len(self.current["matrix"][0])) // 2
        self.current["y"] = -1
        self.next_piece = self.create_piece()

        if self.check_collision(self.current):
            self.game_over = True

    def check_collision(self, piece, offset_x=0, offset_y=0, matrix=None):
        matrix = piece["matrix"] if matrix is None else matrix

        for row_index, row in enumerate(matrix):
            for col_index, value in enumerate(row):
                if not value:
                    continue

                new_x = piece["x"] + col_index + offset_x
                new_y = piece["y"] + row_index + offset_y

                if new_x < 0 or new_x >= COLS or new_y >= ROWS:
                    return True

                if new_y >= 0 and self.board[new_y][new_x]:
                    return True

        return False

    def merge_piece(self):
        for row_index, row in enumerate(self.current["matrix"]):
            for col_index, value in enumerate(row):
                if not value:
                    continue

                board_y = self.current["y"] + row_index
                board_x = self.current["x"] + col_index

                if board_y >= 0:
                    self.board[board_y][board_x] = self.current["type"]

    def clear_lines(self):
        remaining_rows = []
        cleared = 0

        for row in self.board:
            if all(cell != 0 for cell in row):
                cleared += 1
            else:
                remaining_rows.append(row)

        while len(remaining_rows) < ROWS:
            remaining_rows.insert(0, [0 for _ in range(COLS)])

        self.board = remaining_rows

        if cleared > 0:
            score_map = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += score_map.get(cleared, 0) * self.level
            self.lines += cleared
            self.level = self.lines // 10 + 1
            self.drop_interval = max(120, 700 - (self.level - 1) * 60)

    def move_piece(self, dx, dy):
        if self.game_over or self.paused:
            return False

        if not self.check_collision(self.current, offset_x=dx, offset_y=dy):
            self.current["x"] += dx
            self.current["y"] += dy
            return True

        if dy > 0:
            self.merge_piece()
            self.clear_lines()
            self.spawn_piece()
            return False

        return False

    def rotate_piece(self):
        if self.game_over or self.paused:
            return

        rotated = list(zip(*self.current["matrix"][::-1]))
        rotated = [list(row) for row in rotated]

        kicks = [0, -1, 1, -2, 2]
        for kick in kicks:
            if not self.check_collision(self.current, offset_x=kick, matrix=rotated):
                self.current["matrix"] = rotated
                self.current["x"] += kick
                return

    def hard_drop(self):
        if self.game_over or self.paused:
            return

        while not self.check_collision(self.current, offset_y=1):
            self.current["y"] += 1
            self.score += 2

        self.merge_piece()
        self.clear_lines()
        self.spawn_piece()

    def toggle_pause(self):
        if not self.game_over:
            self.paused = not self.paused

    def draw_block(self, x, y, color):
        pygame.draw.rect(
            self.screen,
            color,
            (x * BLOCK + 1, y * BLOCK + 1, BLOCK - 2, BLOCK - 2),
        )
        pygame.draw.rect(
            self.screen,
            (255, 255, 255, 80),
            (x * BLOCK + 1, y * BLOCK + 1, BLOCK - 2, BLOCK - 2),
            1,
        )

    def draw_board(self):
        self.screen.fill((12, 17, 30))

        board_rect = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT)
        pygame.draw.rect(self.screen, (18, 24, 40), board_rect)

        for y in range(ROWS):
            for x in range(COLS):
                if self.board[y][x]:
                    self.draw_block(x, y, COLORS[self.board[y][x]])
                else:
                    pygame.draw.rect(
                        self.screen,
                        (21, 31, 47),
                        (x * BLOCK, y * BLOCK, BLOCK, BLOCK),
                        1,
                    )

        if self.current:
            for y, row in enumerate(self.current["matrix"]):
                for x, value in enumerate(row):
                    if value:
                        draw_x = self.current["x"] + x
                        draw_y = self.current["y"] + y
                        if draw_y >= 0:
                            self.draw_block(draw_x, draw_y, COLORS[self.current["type"]])

        # side panel
        panel_x = BOARD_WIDTH + 20
        panel_y = 30
        pygame.draw.rect(self.screen, (22, 32, 50), (BOARD_WIDTH + 10, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))

        title = self.font.render("TETRIS", True, (230, 240, 255))
        self.screen.blit(title, (panel_x, panel_y))

        score_text = self.small_font.render(f"Score: {self.score}", True, (230, 240, 255))
        lines_text = self.small_font.render(f"Lines: {self.lines}", True, (230, 240, 255))
        level_text = self.small_font.render(f"Level: {self.level}", True, (230, 240, 255))
        self.screen.blit(score_text, (panel_x, panel_y + 70))
        self.screen.blit(lines_text, (panel_x, panel_y + 100))
        self.screen.blit(level_text, (panel_x, panel_y + 130))

        next_rect = pygame.Rect(panel_x, panel_y + 180, 120, 120)
        pygame.draw.rect(self.screen, (12, 17, 30), next_rect, 2)

        next_matrix = self.next_piece["matrix"]
        next_block_size = 20
        next_offset_x = (120 - len(next_matrix[0]) * next_block_size) // 2
        next_offset_y = (120 - len(next_matrix) * next_block_size) // 2

        for y, row in enumerate(next_matrix):
            for x, value in enumerate(row):
                if value:
                    pygame.draw.rect(
                        self.screen,
                        COLORS[self.next_piece["type"]],
                        (
                            panel_x + next_offset_x + x * next_block_size,
                            panel_y + 180 + next_offset_y + y * next_block_size,
                            next_block_size - 2,
                            next_block_size - 2,
                        ),
                    )

        if self.paused:
            pause_text = self.font.render("PAUSED", True, (255, 255, 255))
            self.screen.blit(pause_text, (BOARD_WIDTH // 2 - 55, BOARD_HEIGHT // 2 - 20))

        if self.game_over:
            over_text = self.font.render("GAME OVER", True, (255, 120, 120))
            self.screen.blit(over_text, (BOARD_WIDTH // 2 - 90, BOARD_HEIGHT // 2 - 20))

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.toggle_pause()
                    elif event.key == pygame.K_p:
                        self.toggle_pause()
                    elif event.key == pygame.K_LEFT:
                        self.move_piece(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move_piece(1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.move_piece(0, 1)
                        if not self.paused and not self.game_over:
                            self.score += 1
                    elif event.key == pygame.K_UP:
                        self.rotate_piece()
                    elif event.key == pygame.K_SPACE:
                        self.hard_drop()

            if not self.paused and not self.game_over:
                now = pygame.time.get_ticks()
                if now - self.last_drop >= self.drop_interval:
                    self.move_piece(0, 1)
                    self.last_drop = now

            self.draw_board()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    game = TetrisGame()
    game.run()
