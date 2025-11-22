import random
import time
from collections import deque
import LEDMatrix
import board
import config

NEOPIXEL = board.D13
WIDTH = 32
HEIGHT = 32

# colors
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

class Snake:
    def __init__(self, start_pos, direction, color, max_len=100):
        self.start_pos = start_pos
        self.start_dir = direction
        self.color = color
        self.max_len = max_len
        self.reset()

    def reset(self):
        self.body = deque([self.start_pos])   # head is leftmost
        self.dir = self.start_dir
        self.alive = True

    def head(self):
        return self.body[0]

    def step_propose(self):
        if not self.alive:
            return self.head()
        x, y = self.head()
        dx, dy = self.dir
        return (x + dx, y + dy)

    def move(self, new_head, grow=False):
        self.body.appendleft(new_head)
        if not grow and len(self.body) > self.max_len:
            self.body.pop()

    def turn(self, new_dir):
        # prevent 180 turn
        if (new_dir[0] == -self.dir[0] and new_dir[1] == -self.dir[1]):
            return
        self.dir = new_dir

    def positions(self):
        return list(self.body)

class Duel:
    DIRS = [(1,0), (0,1), (-1,0), (0,-1)]  # right, down, left, up

    def __init__(self, pixels, brightness=0.04, density=None):
        self.pixels = pixels  # flat buffer
        self.brightness = brightness
        self.led = LEDMatrix.LEDMatrix(NEOPIXEL, auto_write=False, brightness=self.brightness)
        # players start on opposite sides, slightly different rows to avoid instant head-on
        self.p1 = Snake((4, 15), (1, 0), RED, max_len=100)
        self.p2 = Snake((27, 16), (-1, 0), BLUE, max_len=100)
        self.occupancy = [[None for _ in range(WIDTH)] for __ in range(HEIGHT)]
        self.reset_board()
        self.scores = [0, 0]
        self.config = None
        try:
            self.config = config.Config()
        except Exception:
            self.config = None

    def reset_board(self):
        # clear occupancy
        for y in range(HEIGHT):
            for x in range(WIDTH):
                self.occupancy[y][x] = None

        # pick random start positions on opposite halves and random valid directions
        def pick_start(side):
            # side = "left" or "right"
            if side == "left":
                x = random.randint(2, 8)
            else:
                x = random.randint(WIDTH - 9, WIDTH - 3)
            y = random.randint(2, HEIGHT - 3)
            return (x, y)

        # ensure starts aren't too close
        for _ in range(100):
            s1 = pick_start("left")
            s2 = pick_start("right")
            # require some minimum Manhattan distance
            if abs(s1[0] - s2[0]) + abs(s1[1] - s2[1]) >= 12:
                break

        # pick initial directions that roughly point inward (but random)
        def pick_dir_for(start, prefer):
            dirs = list(self.DIRS)
            random.shuffle(dirs)
            for d in dirs:
                nx, ny = start[0] + d[0], start[1] + d[1]
                # prefer directions that move toward center (but allow randomness)
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    return d
            return (1, 0)

        self.p1.start_pos = s1
        self.p2.start_pos = s2
        self.p1.start_dir = pick_dir_for(s1, "in")
        self.p2.start_dir = pick_dir_for(s2, "in")

        # reset snake instances (they use start_pos/start_dir)
        self.p1.reset()
        self.p2.reset()

        # mark initial occupancy
        for p in (self.p1, self.p2):
            x, y = p.head()
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                self.occupancy[y][x] = p

    def in_bounds(self, pos):
        x,y = pos
        return 0 <= x < WIDTH and 0 <= y < HEIGHT

    def is_occupied(self, pos):
        x,y = pos
        if not self.in_bounds(pos):
            return True
        return self.occupancy[y][x] is not None

    def set_occ(self, pos, snake):
        x,y = pos
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.occupancy[y][x] = snake

    def clear_tail(self, pos):
        x,y = pos
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.occupancy[y][x] = None

    def simple_ai_choose_dir(self, snake):
        """
        Smarter, competitive AI:
        - avoids tails as before
        - prefers moves that increase its own free area
        - prefers moves that reduce opponent's reachable area (lure opponent into tight spaces / trails)
        - favors crossing the center rather than hugging walls
        - small randomness to avoid determinism
        """
        x, y = snake.head()
        opp = self.p1 if snake is self.p2 else self.p2

        def tail_will_be_freed(pos):
            px, py = pos
            if not (0 <= px < WIDTH and 0 <= py < HEIGHT):
                return False
            occ = self.occupancy[py][px]
            if occ is None:
                return False
            try:
                tail = occ.body[-1]
            except Exception:
                return False
            return tail == pos and len(occ.body) >= occ.max_len

        def cell_is_free_for_move(pos):
            px, py = pos
            if not (0 <= px < WIDTH and 0 <= py < HEIGHT):
                return False
            occ = self.occupancy[py][px]
            if occ is None:
                return True
            return tail_will_be_freed(pos)

        # candidate directions (no 180 turn)
        candidates = [d for d in self.DIRS if not (d[0] == -snake.dir[0] and d[1] == -snake.dir[1])]
        if not candidates:
            return snake.dir

        safe_dirs = []
        for d in candidates:
            nx, ny = x + d[0], y + d[1]
            if cell_is_free_for_move((nx, ny)):
                safe_dirs.append(d)
        if not safe_dirs:
            return random.choice(candidates)

        # reachable-area BFS used for both players
        def reachable_area_from(pos, treat_as_occupied=None, limit=80):
            # treat_as_occupied: set of positions to temporarily consider occupied
            visited = set()
            q = [pos]
            visited.add(pos)
            idx = 0
            while idx < len(q) and len(visited) < limit:
                cxp, cyp = q[idx]; idx += 1
                for dd in self.DIRS:
                    nxp, nyp = cxp + dd[0], cyp + dd[1]
                    if not (0 <= nxp < WIDTH and 0 <= nyp < HEIGHT):
                        continue
                    if (nxp, nyp) in visited:
                        continue
                    if treat_as_occupied and (nxp, nyp) in treat_as_occupied:
                        continue
                    # allow if currently free or tail that will be freed
                    if cell_is_free_for_move((nxp, nyp)):
                        visited.add((nxp, nyp))
                        q.append((nxp, nyp))
            return len(visited)

        # baseline opponent reachable area (before our move)
        opp_area_before = reachable_area_from(opp.head(), limit=60)

        cx = (WIDTH - 1) / 2.0
        cy = (HEIGHT - 1) / 2.0

        best = None
        best_score = -1e9

        for d in safe_dirs:
            after = (x + d[0], y + d[1])
            ax, ay = after

            # own reachable area from after-position
            my_area = reachable_area_from(after, limit=80)

            # simulate making 'after' occupied by our head for opponent computation
            # temporarily mark occupancy and restore
            orig = None
            simulated = False
            if 0 <= ax < WIDTH and 0 <= ay < HEIGHT:
                orig = self.occupancy[ay][ax]
                self.occupancy[ay][ax] = snake
                simulated = True

            try:
                opp_area_after = reachable_area_from(opp.head(), limit=60)
            finally:
                if simulated:
                    self.occupancy[ay][ax] = orig

            lure_score = (opp_area_before - opp_area_after)  # positive if we shrink opponent space

            # distance change relative to opponent: slightly prefer getting closer to tempt / cross
            cur_dist = abs(x - opp.head()[0]) + abs(y - opp.head()[1])
            new_dist = abs(after[0] - opp.head()[0]) + abs(after[1] - opp.head()[1])
            dist_delta = cur_dist - new_dist  # positive => closer

            # prefer center crossings
            center_dist = abs(after[0] - cx) + abs(after[1] - cy)
            wall_dist = min(after[0], after[1], WIDTH-1-after[0], HEIGHT-1-after[1])

            # small penalty if stepping into a currently-occupied cell that won't be freed
            occ_penalty = 0
            if self.occupancy[ay][ax] is not None and not tail_will_be_freed(after):
                occ_penalty += 1000

            noise = random.uniform(-0.6, 0.6)

            # score composition:
            # - encourage larger personal free area
            # - encourage reducing opponent's area (luring)
            # - encourage moving closer to opponent a bit to engage
            # - favor central crossing (penalize center_dist) and staying off walls (bonus wall_dist)
            score = (my_area * 2.2) + (lure_score * 4.0) + (dist_delta * 1.6) + (wall_dist * 0.9) - (center_dist * 0.25) - occ_penalty + noise

            # small bonus for keeping forward to avoid jitter
            if d == snake.dir:
                score += 0.7

            if score > best_score:
                best_score = score
                best = d

        return best if best is not None else random.choice(safe_dirs)


    def step(self):
        # AI choose new directions
        if self.p1.alive:
            self.p1.turn(self.simple_ai_choose_dir(self.p1))
        if self.p2.alive:
            self.p2.turn(self.simple_ai_choose_dir(self.p2))

        # propose moves
        h1_new = self.p1.step_propose() if self.p1.alive else None
        h2_new = self.p2.step_propose() if self.p2.alive else None

        # detect collisions (both moves evaluated simultaneously)
        p1_collision = (h1_new is None) or self.is_occupied(h1_new)
        p2_collision = (h2_new is None) or self.is_occupied(h2_new)

        # special case: both move into same empty cell -> both collide (tie)
        if h1_new is not None and h2_new is not None and h1_new == h2_new:
            p1_collision = True
            p2_collision = True

        # apply moves for survivors
        # before moving, record tails that will be cleared (non-growing)
        tail1 = None
        tail2 = None
        if self.p1.alive and not p1_collision:
            tail1 = self.p1.body[-1] if len(self.p1.body) >= self.p1.max_len else None
            self.p1.move(h1_new)
            self.set_occ(h1_new, self.p1)
        if self.p2.alive and not p2_collision:
            tail2 = self.p2.body[-1] if len(self.p2.body) >= self.p2.max_len else None
            self.p2.move(h2_new)
            self.set_occ(h2_new, self.p2)

        # clear tails if existing and they are not part of body anymore
        if tail1 is not None:
            # if tail was not captured by opponent head this tick, clear
            if tail1 not in self.p1.positions():
                self.clear_tail(tail1)
        if tail2 is not None:
            if tail2 not in self.p2.positions():
                self.clear_tail(tail2)

        # handle collisions: mark dead
        if p1_collision and self.p1.alive:
            self.p1.alive = False
        if p2_collision and self.p2.alive:
            self.p2.alive = False

        # determine round end
        round_over = False
        winner = None
        if not self.p1.alive and not self.p2.alive:
            round_over = True
            winner = None  # tie
        elif not self.p1.alive:
            round_over = True
            winner = 2
            self.scores[1] += 1
        elif not self.p2.alive:
            round_over = True
            winner = 1
            self.scores[0] += 1

        return round_over, winner

    def render(self):
        # write occupancy to flat pixels buffer; background black
        for i in range(WIDTH * HEIGHT):
            self.pixels[i] = BLACK
        # draw trails
        for y in range(HEIGHT):
            for x in range(WIDTH):
                occ = self.occupancy[y][x]
                if occ is None:
                    continue
                idx = y * WIDTH + x
                self.pixels[idx] = occ.color
        # ensure head brightness maybe brighter
        if self.p1.alive:
            x,y = self.p1.head()
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                self.pixels[y*WIDTH + x] = tuple(min(255, c+80) for c in self.p1.color)
        if self.p2.alive:
            x,y = self.p2.head()
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                self.pixels[y*WIDTH + x] = tuple(min(255, c+80) for c in self.p2.color)

    def flash_winner(self, winner):
        # flash board a few times
        for _ in range(6):
            for i in range(WIDTH * HEIGHT):
                self.pixels[i] = BLACK
            if winner == 1:
                for pos in self.p2.positions():
                    x,y = pos
                    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                        self.pixels[y*WIDTH + x] = BLUE
            elif winner == 2:
                for pos in self.p1.positions():
                    x,y = pos
                    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                        self.pixels[y*WIDTH + x] = RED
            else:
                # tie: white flash
                for i in range(WIDTH * HEIGHT):
                    self.pixels[i] = (160,160,160)
            LEDMatrix.LEDMatrix(NEOPIXEL, auto_write=False, brightness=self.brightness).show_buffer(self.pixels) if hasattr(LEDMatrix.LEDMatrix, "show_buffer") else None
            time.sleep(0.08)
            for i in range(WIDTH * HEIGHT):
                self.pixels[i] = BLACK
            LEDMatrix.LEDMatrix(NEOPIXEL, auto_write=False, brightness=self.brightness).show_buffer(self.pixels) if hasattr(LEDMatrix.LEDMatrix, "show_buffer") else None
            time.sleep(0.08)

def set_pixel_buf(pixels, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        pixels[y * WIDTH + x] = color

def main():
    # create LED buffer
    led = LEDMatrix.LEDMatrix(NEOPIXEL, auto_write=False, brightness=0.04)
    pixels = led  # object implements buffer protocol; used like flat buffer in other scripts

    # wait for db (keeps same pattern as other scripts)
    while not config.is_db_available():
        time.sleep(0.3)

    duel = Duel(pixels, brightness=0.04)

    frame_delay = 0.06
    try:
        while True:
            # refresh brightness from config occasionally
            try:
                c = config.Config() if duel.config is None else duel.config
                b = c.get('brightness')
                if b is not None:
                    b = float(b)
                    if abs(b - duel.brightness) > 1e-6:
                        duel.brightness = b
                        led = LEDMatrix.LEDMatrix(NEOPIXEL, auto_write=False, brightness=duel.brightness)
                        pixels = led
                        duel.pixels = pixels
                duel.config = c
            except Exception:
                pass

            round_over = False
            # run a round
            while True:
                over, winner = duel.step()
                duel.render()
                # write pixels into actual LED buffer object if required:
                try:
                    # assume pixels implements sequence of tuples; copy values into it
                    for i in range(WIDTH*HEIGHT):
                        pixels[i] = duel.pixels[i]
                except Exception:
                    pass
                # show (LEDMatrix implementation)
                try:
                    pixels.show()
                except Exception:
                    # try alternative
                    try:
                        led.show()
                    except Exception:
                        pass

                if over:
                    round_over = True
                    break
                time.sleep(frame_delay)

            # round finished: update stats and flash
            duel.flash_winner(winner)
            # optional DB stats
            try:
                if duel.config:
                    duel.config.write_stats("snake_p1_wins", str(duel.scores[0]))
                    duel.config.write_stats("snake_p2_wins", str(duel.scores[1]))
            except Exception:
                pass

            # reset board for next round
            duel.reset_board()
            time.sleep(0.5)

    finally:
        # clear
        for i in range(WIDTH*HEIGHT):
            try:
                pixels[i] = BLACK
            except Exception:
                pass
        try:
            pixels.show()
        except Exception:
            pass

if __name__ == "__main__":
    main()