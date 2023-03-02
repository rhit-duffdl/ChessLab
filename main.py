import math

import chess
import chess.engine
import pygame
import numpy
import threading
import time
from stockfish import Stockfish


class ChessLab:
    board = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(
        r"C:\Users\dillo\OneDrive\Desktop\stockfish_15.1_win_x64_avx2\stockfish-windows-2022-x86-64-avx2.exe")

    width, height = 752 * 1.25, 1000 * 1.25
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Chess Labs")
    background_color = (129, 84, 56)
    pygame.mouse.set_visible(False)

    square_width = int(width / 8)
    board_bottom = square_width * 8

    running = True

    board_matrix = numpy.zeros((8, 8))

    cursor_size = square_width / 3

    default_cursor = pygame.transform.scale(pygame.image.load("Mouse-Cursor.svg"),
                                            (cursor_size, cursor_size))

    hover_cursor = pygame.transform.scale(pygame.image.load("open_hand.svg"),
                                          (cursor_size, cursor_size))

    grab_cursor = pygame.transform.scale(pygame.image.load("grabbed_hand.png"),
                                         (cursor_size, cursor_size))

    cursor_image = default_cursor

    bB = pygame.image.load("bB.svg")
    bK = pygame.image.load("bK.svg")
    bN = pygame.image.load("bN.svg")
    bP = pygame.image.load("bP.svg")
    bQ = pygame.image.load("bQ.svg")
    bR = pygame.image.load("bR.svg")

    wB = pygame.image.load("wB.svg")
    wK = pygame.image.load("wK.svg")
    wN = pygame.image.load("wN.svg")
    wP = pygame.image.load("wP.svg")
    wQ = pygame.image.load("wQ.svg")
    wR = pygame.image.load("wR.svg")

    piece_images = {"b": bB, "k": bK, "n": bN, "p": bP, "q": bQ, "r": bR, "B": wB, "K": wK, "N": wN, "P": wP, "Q": wQ,
                    "R": wR}

    # Ratio of piece size to square size
    piece_scale = 0.8
    # Offset = difference between old square side length and scaled square side length
    # square_width - (solve for scaled_square_width in: scaled_square_width^2 = square_width^2 * piece_scale)
    piece_img_offset = (square_width - square_width * math.sqrt(piece_scale))

    def __init__(self):
        # Scale the images of the pieces
        for key in self.piece_images.keys():
            self.piece_images[key] = pygame.transform.scale(self.piece_images.get(key),
                                                            (self.square_width * self.piece_scale,
                                                             self.square_width * self.piece_scale))

    columns = ["a", "b", "c", "d", "e", "f", "g", "h"]

    def coordinates_to_board_position(self, x, y):
        result = ""
        result += self.columns[x]
        result += str(8 - y)
        return result

    def board_position_to_coordinates(self, pos):
        return self.columns.index(pos[0]), int(pos[1])

    piece_grabbed = ""
    pos_grabbed = ""

    def handle_mouse(self):
        # Draw mouse and update grabbed pieces
        mouse_x, mouse_y = pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]
        center_cursor_x = (mouse_x + self.cursor_size / 2)
        center_cursor_y = (mouse_y + self.cursor_size / 2)

        closest_column_x = self.square_width * round(center_cursor_x / self.square_width)
        closest_row_y = self.square_width * round(center_cursor_y / self.square_width)

        col_num = int(center_cursor_x / self.square_width)
        row_num = int(center_cursor_y / self.square_width)

        self.cursor_image = self.default_cursor
        if (7 - row_num) * 8 + col_num < 64 and self.board.piece_at(
                (7 - row_num) * 8 + col_num) is not None and col_num < 8 and row_num < 8:

            if self.piece_grabbed == "" and pygame.mouse.get_pressed()[0]:
                self.cursor_image = self.grab_cursor
                self.piece_grabbed = self.board.piece_at((7 - row_num) * 8 + col_num)
                self.pos_grabbed = self.coordinates_to_board_position(col_num, row_num)

            elif self.piece_grabbed == "":
                self.cursor_image = self.hover_cursor

        # Handle releasing pieces onto squares
        if self.piece_grabbed != "" and not pygame.mouse.get_pressed()[0] and col_num < 8 and row_num < 8:

            square_released_on = self.coordinates_to_board_position(col_num, row_num)

            # Check which side of the column and row the mouse is on, and center the closest_column_x and
            # closest_row_y within their respective squares
            if center_cursor_x < closest_column_x:
                closest_column_x -= self.square_width / 2
            else:
                closest_column_x += self.square_width / 2

            if center_cursor_y < closest_row_y:
                closest_row_y -= self.square_width / 2
            else:
                closest_row_y += self.square_width / 2

            # Check if the mouse is too close to the column or row edge to determine the release position
            if not abs(center_cursor_x - closest_column_x) > self.square_width * 3 / 8 or abs(
                    center_cursor_y - closest_row_y) > self.square_width * 3 / 8:
                possible_moves = []

                # Generate possible moves
                for move in self.board.legal_moves:
                    if move.promotion is not None:
                        for promotion_piece in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                            possible_promotion_move = chess.Move(move.from_square, move.to_square,
                                                                 promotion=promotion_piece)
                            if possible_promotion_move in self.board.legal_moves:
                                possible_moves.append(possible_promotion_move)

                    if chess.square_name(move.from_square) == str(self.pos_grabbed) and chess.square_name(
                            move.to_square) == square_released_on:
                        possible_moves.append(move)

                # Handle possible moves
                if possible_moves:
                    # TODO: Handle promotion; currently auto-queens
                    self.board.push(possible_moves[0])
                    # self.stockfish.set_fen_position(self.board.fen())

            self.piece_grabbed = ""

    def run_game(self):
        # t1 = threading.Thread(target=self.handle_mouse)
        # t1.start()
        while self.running:
            if self.board.is_game_over():
                result = self.board.result()
                print(result)
                self.running = False

            # Generate engine move
            moves = len(self.board.move_stack)
            engine = True
            if moves % 2 != 0 and engine:
                # stockfish_moves = self.stockfish.get_top_moves(5)
                # print(stockfish_moves[0]["Move"])
                #
                # stockfish_move = chess.Move(chess.parse_square(stockfish_moves[0]["Move"][0:2]),
                #            chess.parse_square(stockfish_moves[0]["Move"][2::]))
                result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
                self.board.push(result.move)
                print(str(result.move) + "\n\n")

            self.screen.fill(self.background_color)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.handle_mouse()

            # Get FEN string representation of board
            row_contents = self.board.fen().split(" ")[0].split("/")

            # Draw board
            for j in range(8):
                for i in range(8):
                    offset = self.square_width
                    if j % 2 == 0:
                        offset = 0
                    if i % 2 == 0:
                        pygame.draw.rect(self.screen, (255, 255, 255),
                                         pygame.Rect(
                                             i * self.square_width + offset,
                                             j * self.square_width,
                                             self.square_width, self.square_width))

            # Draw pieces
            row_idx = 0
            col_idx = 0
            for contents in row_contents:
                row_idx = 0
                for item in contents:
                    if row_idx >= 8:
                        break

                    if item.isdigit():
                        row_idx += int(item) - 1
                    elif self.coordinates_to_board_position(row_idx, col_idx) == self.piece_grabbed:
                        continue
                    else:
                        self.screen.blit(self.piece_images[item], (
                            row_idx * self.square_width + self.piece_img_offset,
                            col_idx * self.square_width + self.piece_img_offset))
                    row_idx += 1
                col_idx += 1

            # Draw grabbed piece
            if self.piece_grabbed != "":

                grabbed_piece_cords = self.board_position_to_coordinates(self.pos_grabbed)
                grabbed_square_color = (255, 255, 255)
                if (grabbed_piece_cords[0] % 2 == 0 and grabbed_piece_cords[1] % 2 != 0) or (
                        grabbed_piece_cords[0] % 2 != 0 and grabbed_piece_cords[1] % 2 == 0):
                    grabbed_square_color = self.background_color

                pygame.draw.rect(self.screen, grabbed_square_color,
                                 pygame.Rect(
                                     grabbed_piece_cords[0] * self.square_width,
                                     (8 - grabbed_piece_cords[1]) * self.square_width,
                                     self.square_width, self.square_width))

                self.screen.blit(self.piece_images[str(self.piece_grabbed)],
                                 (pygame.mouse.get_pos()[0] - self.square_width * self.piece_scale / 4,
                                  pygame.mouse.get_pos()[1] - self.square_width * self.piece_scale / 4))

                self.cursor_image = self.grab_cursor

            # Draw GUI
            pygame.draw.rect(self.screen, (110, 109, 103),
                             pygame.Rect(0, self.board_bottom, self.width, self.height - self.board_bottom))

            # Draw mouse and update
            self.screen.blit(self.cursor_image, pygame.mouse.get_pos())
            pygame.display.flip()
        # t1.join()
        self.engine.quit()


if __name__ == "__main__":
    lab = ChessLab()
    lab.run_game()